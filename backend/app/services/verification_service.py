"""Evidence-first factual verification.

The engine never treats "the model agrees" as proof. The order of operations is:

1. **Deterministic extraction** of factual claims (see ``claim_extraction``).
2. **Deterministic retrieval** of candidate evidence from the user's own research
   session (lexical overlap, numeric consistency).
3. **Optional AI assessment** of those passages - only when the provider supports
   it, and only accepted when the model's supporting quotes are found verbatim in
   the stored passages.
4. **Honest status**: when evidence is missing, irrelevant, or unverifiable the
   finding is ``Insufficient Evidence`` (or ``Not Checked`` when it was skipped),
   never ``Supported``.

Consequences worth knowing: with ``AI_PROVIDER=mock`` (the default) no assessor
exists, so findings are ``Insufficient Evidence`` with an explanation - which is
accurate. Turning on Groq enables the assessment step.
"""
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import Settings, get_settings
from app.core.database import Database
from app.models.document_ir import DocumentIR
from app.models.research import (
    ClaimVerification,
    EvidenceRecord,
    VerificationReport,
    VerificationStatus,
    VerificationSummary,
    VERIFICATION_STATUS_LABELS,
)
from app.providers.base import AIProvider
from app.providers.factory import get_provider
from app.repositories.document_repository import DocumentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.verification_repository import VerificationRepository
from app.services.claim_extraction import ExtractedClaim, extract_claims
from app.services.research_service import lexical_overlap, tokens

logger = logging.getLogger(__name__)

NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)?%?")
MAX_CANDIDATE_PASSAGES = 4
MAX_QUOTE_CHARS = 500

LIMITATIONS = [
    "Verification compares claims with the evidence you retrieved; it cannot check facts "
    "that no source covers.",
    "An LLM's agreement is not proof. Findings are labelled with the method that produced them.",
    "Search snippets are never treated as evidence - only extracted page passages are.",
    "Missing contradictory evidence does not mean a claim is supported.",
    "Opinions, recommendations and predictions are excluded from verification by design.",
    "Time-sensitive claims (years, 'currently', 'latest') are flagged for manual review.",
]


@dataclass
class Verdict:
    """Internal result of assessing one claim."""

    status: VerificationStatus
    explanation: str
    method: str
    supporting_ids: List[str] = field(default_factory=list)
    contradicting_ids: List[str] = field(default_factory=list)


def normalize_for_match(text: str) -> str:
    """Normalize text for verbatim-quote comparison."""
    return " ".join((text or "").split()).strip().lower()


def claim_numbers(claim: str) -> List[str]:
    """Numbers/percentages in a claim, normalized for comparison."""
    return [match.replace(",", "") for match in NUMBER_PATTERN.findall(claim or "")]


class VerificationService:
    """Runs verification passes and stores findings."""

    def __init__(
        self,
        db: Database,
        *,
        provider: Optional[AIProvider] = None,
        settings: Optional[Settings] = None,
    ):
        self.db = db
        self.settings = settings or get_settings()
        self.provider = provider or get_provider()
        self.documents = DocumentRepository(db)
        self.evidence = EvidenceRepository(db)
        self.sessions = ResearchRepository(db)
        self.verifications = VerificationRepository(db)

    async def verify_document(
        self,
        document_id: str,
        user_id: str,
        *,
        research_session_id: Optional[str] = None,
        max_claims: Optional[int] = None,
        section_titles: Optional[List[str]] = None,
    ) -> VerificationReport:
        """Verify the factual claims of a document against session evidence."""
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        session_id = research_session_id
        if session_id is None:
            latest = await self.sessions.get_latest_for_document(document_id, user_id)
            session_id = latest.id if latest else None

        evidence_pool: List[EvidenceRecord] = []
        if session_id:
            evidence_pool = await self.evidence.list_by_session(
                session_id, user_id, selected_only=True
            )

        extraction = extract_claims(document, section_titles)
        limit = max_claims or self.settings.VERIFICATION_MAX_CLAIMS
        findings: List[ClaimVerification] = []

        for position, claim in enumerate(extraction.claims):
            if position >= limit:
                findings.append(
                    await self._persist(
                        claim,
                        document,
                        user_id,
                        session_id,
                        Verdict(
                            status=VerificationStatus.NOT_CHECKED,
                            explanation=(
                                "Not evaluated: the verification limit for this pass was reached."
                            ),
                            method="not_run",
                        ),
                    )
                )
                continue

            verdict = await self._assess(claim, evidence_pool)
            findings.append(
                await self._persist(claim, document, user_id, session_id, verdict)
            )

        summary = await self.verifications.summary(document_id, user_id)
        return VerificationReport(
            document_id=document_id,
            research_session_id=session_id,
            summary=summary,
            findings=findings,
            limitations=list(LIMITATIONS),
        )

    async def recheck(
        self,
        verification_id: str,
        user_id: str,
        *,
        max_claims: Optional[int] = None,
    ) -> Optional[ClaimVerification]:
        """Re-run verification for one stored finding."""
        finding = await self.verifications.get_by_id(verification_id, user_id)
        if not finding:
            return None
        return await self.recheck_claim(
            finding.document_id,
            user_id,
            finding.claim_id,
            session_id=finding.research_session_id,
        )

    async def recheck_claim(
        self,
        document_id: str,
        user_id: str,
        claim_id: str,
        *,
        session_id: Optional[str] = None,
    ) -> Optional[ClaimVerification]:
        """Re-check a single claim in place (used by the UI's "Recheck" button)."""
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            return None

        extraction = extract_claims(document)
        claim = next((item for item in extraction.claims if item.claim_id == claim_id), None)
        if claim is None:
            return None

        evidence_pool: List[EvidenceRecord] = []
        if session_id:
            evidence_pool = await self.evidence.list_by_session(session_id, user_id, selected_only=True)

        verdict = await self._assess(claim, evidence_pool)
        return await self._persist(claim, document, user_id, session_id, verdict)

    async def report(
        self,
        document_id: str,
        user_id: str,
        status: Optional[VerificationStatus] = None,
    ) -> VerificationReport:
        """Read existing findings without re-running verification."""
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        findings = await self.verifications.list_for_document(document_id, user_id, status)
        summary = await self.verifications.summary(document_id, user_id)
        latest = await self.sessions.get_latest_for_document(document_id, user_id)
        return VerificationReport(
            document_id=document_id,
            research_session_id=latest.id if latest else None,
            summary=summary,
            findings=findings,
            limitations=list(LIMITATIONS),
        )

    # -- assessment -------------------------------------------------------
    async def _assess(self, claim: ExtractedClaim, evidence_pool: List[EvidenceRecord]) -> Verdict:
        if not evidence_pool:
            return Verdict(
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                explanation=(
                    "No evidence was retrieved for this document, so the claim could not be "
                    "checked. Run research or attach your own sources first."
                ),
                method="no_evidence",
            )

        candidates = self._rank_candidates(claim.text, evidence_pool)
        if not candidates:
            return Verdict(
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                explanation=(
                    "The retrieved evidence does not discuss this claim closely enough to "
                    "support or contradict it."
                ),
                method="lexical_match_failed",
            )

        # Deterministic numeric guard: a claim about "38%" cannot be supported by
        # a passage that says "83%", no matter what the model thinks.
        numbers = claim_numbers(claim.text)
        if numbers:
            haystack = " ".join(normalize_for_match(item.passage) for _, item in candidates)
            missing = [value for value in numbers if value.replace(",", "") not in haystack.replace(",", "")]
            if missing:
                return Verdict(
                    status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                    explanation=(
                        "No retrieved passage contains the figure(s) "
                        + ", ".join(missing)
                        + " quoted in this claim, so it cannot be confirmed."
                    ),
                    method="numeric_check",
                )

        passages_payload = [
            {"marker": f"P{index}", "text": item.passage}
            for index, (_, item) in enumerate(candidates, 1)
        ]
        by_marker = {
            f"P{index}": item for index, (_, item) in enumerate(candidates, 1)
        }

        try:
            assessment = await self.provider.assess_claim(claim.text, passages_payload)
        except Exception as exc:  # provider/network failure
            logger.warning("Claim assessment failed: %s", type(exc).__name__)
            return Verdict(
                status=VerificationStatus.NOT_CHECKED,
                explanation=(
                    "The assessment step failed, so this claim was not evaluated. "
                    "Recheck it when the AI provider is available."
                ),
                method="provider_error",
            )

        if not assessment:
            return Verdict(
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                explanation=(
                    "Relevant passages were found, but no automated assessor is configured for "
                    "this run. Review the passages manually before relying on the claim."
                ),
                method="evidence_retrieved_no_assessor",
            )

        return self._verdict_from_assessment(assessment, by_marker)

    def _verdict_from_assessment(
        self,
        assessment: Dict[str, Any],
        by_marker: Dict[str, EvidenceRecord],
    ) -> Verdict:
        raw_status = str(assessment.get("status") or "").strip().lower()
        explanation = str(assessment.get("explanation") or "").strip()[:2000]
        quotes = assessment.get("quotes") or []

        status_map = {
            "supported": VerificationStatus.SUPPORTED,
            "contradicted": VerificationStatus.CONTRADICTED,
            "insufficient_evidence": VerificationStatus.INSUFFICIENT_EVIDENCE,
            "insufficient": VerificationStatus.INSUFFICIENT_EVIDENCE,
        }
        status = status_map.get(raw_status, VerificationStatus.INSUFFICIENT_EVIDENCE)

        validated: List[Tuple[str, EvidenceRecord]] = []
        discarded = 0
        for quote in quotes if isinstance(quotes, list) else []:
            if not isinstance(quote, dict):
                continue
            marker = str(quote.get("marker") or "").strip().upper()
            text = str(quote.get("quote") or "").strip()[:MAX_QUOTE_CHARS]
            evidence_record = by_marker.get(marker)
            if not evidence_record or not text:
                discarded += 1
                continue
            if normalize_for_match(text) in normalize_for_match(evidence_record.passage):
                validated.append((marker, evidence_record))
            else:
                discarded += 1

        if discarded:
            explanation += (
                f" ({discarded} quoted passage(s) could not be found verbatim in the retrieved "
                "evidence and were discarded.)"
            )

        if status == VerificationStatus.SUPPORTED and not validated:
            return Verdict(
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                explanation=(
                    "The assessor reported support but could not quote the supporting text "
                    "verbatim, so the finding was downgraded. " + explanation
                ).strip(),
                method="ai_quotes_unverified",
            )

        if status == VerificationStatus.CONTRADICTED and not validated:
            return Verdict(
                status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                explanation=(
                    "The assessor reported a contradiction but could not quote the conflicting "
                    "text verbatim, so the finding was downgraded. " + explanation
                ).strip(),
                method="ai_quotes_unverified",
            )

        evidence_ids = {item.id for _, item in validated}
        supporting: List[str] = []
        contradicting: List[str] = []

        if status == VerificationStatus.SUPPORTED:
            supporting = list(evidence_ids)
        elif status == VerificationStatus.CONTRADICTED:
            contradicting = list(evidence_ids)

        if not explanation:
            explanation = (
                f"Assessed as {VERIFICATION_STATUS_LABELS[status]} using "
                f"{len(validated)} verbatim passage(s)."
            )

        return Verdict(
            status=status,
            explanation=explanation,
            method="ai_assisted_with_quote_verification",
            supporting_ids=supporting,
            contradicting_ids=contradicting,
        )

    def _rank_candidates(
        self, claim: str, evidence_pool: List[EvidenceRecord]
    ) -> List[Tuple[float, EvidenceRecord]]:
        threshold = float(self.settings.VERIFICATION_MIN_LEXICAL_OVERLAP)
        claim_tokens = tokens(claim)
        if not claim_tokens:
            return []

        scored: List[Tuple[float, EvidenceRecord]] = []
        for record in evidence_pool:
            if not record.user_selected:
                continue
            overlap = len(claim_tokens & tokens(record.passage)) / len(claim_tokens)
            if overlap >= threshold:
                scored.append((overlap, record))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[:MAX_CANDIDATE_PASSAGES]

    # -- persistence ------------------------------------------------------
    async def _persist(
        self,
        claim: ExtractedClaim,
        document: DocumentIR,
        user_id: str,
        session_id: Optional[str],
        verdict: Verdict,
    ) -> ClaimVerification:
        finding = ClaimVerification(
            user_id=user_id,
            document_id=document.id,
            research_session_id=session_id,
            claim_id=claim.claim_id,
            claim_text=claim.text,
            section_id=claim.section_id,
            section_title=claim.section_title,
            status=verdict.status,
            explanation=verdict.explanation,
            verification_method=verdict.method,
            time_sensitive=claim.time_sensitive,
            supporting_evidence_ids=verdict.supporting_ids,
            contradicting_evidence_ids=verdict.contradicting_ids,
            checked_at=datetime.utcnow()
            if verdict.status != VerificationStatus.NOT_CHECKED
            else None,
        )
        return await self.verifications.upsert(finding)

    @staticmethod
    def status_label(status: VerificationStatus) -> str:
        return VERIFICATION_STATUS_LABELS[status]
