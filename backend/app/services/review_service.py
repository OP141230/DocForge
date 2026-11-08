"""AI review engine (Phase 6).

Two independent layers produce findings:

1. **Deterministic checks** (this module, plain Python). They are reproducible,
   offline and never hallucinate: repeated sentences, very long sentences,
   heading-level jumps, empty sections, missing brief requirements, and
   citation/verification problems already recorded by Phase 5.
2. **Model review** (``provider.review_document``). Its output is *untrusted*:
   categories and severities are whitelisted, text is length-capped, and every
   ``original_text`` quote must be located in the real document before a finding
   is stored. Offsets always come from :class:`DocumentTextIndex`, never from the
   model.

The distinction is visible in the UI (``ReviewFinding.source``), because
"a regex found a 45-word sentence" and "a language model thinks this is vague"
are different kinds of claim and should not be presented as equal.
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

from app.core.config import Settings, get_settings
from app.core.database import Database
from app.models.document_brief import DocumentBrief
from app.models.document_ir import DocumentIR
from app.models.review import (
    CATEGORY_LABELS,
    MODE_CATEGORIES,
    SEVERITY_ORDER,
    DocumentVersionNote,
    EditProposal,
    EditOperation,
    FindingSource,
    FindingStatus,
    ProposalStatus,
    ReviewCategory,
    ReviewFinding,
    ReviewMode,
    ReviewReport,
    ReviewScope,
    ReviewSession,
    ReviewStatus,
    ReviewSummary,
    Severity,
    StartReviewRequest,
    VersionOrigin,
)
from app.models.research import VerificationStatus
from app.providers.base import AIProvider
from app.providers.factory import get_provider
from app.repositories.citation_repository import CitationRepository
from app.repositories.compliance_repository import ComplianceRepository
from app.repositories.document_brief_repository import DocumentBriefRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.review_repository import (
    EditProposalRepository,
    ReviewRepository,
    VersionNoteRepository,
)
from app.repositories.verification_repository import VerificationRepository
from app.services.citation_service import CitationService
from app.services.citations import normalize_style
from app.services.document_text import DocumentTextIndex, block_text, normalize

logger = logging.getLogger(__name__)

MAX_AI_FINDINGS = 25
MAX_TITLE = 200
MAX_EXPLANATION = 2000
MAX_SUGGESTION = 5000
MAX_QUOTE = 400
LONG_SENTENCE_WORDS = 40
MIN_REPEAT_SENTENCE_WORDS = 12

LIMITATIONS = [
    "Deterministic checks catch measurable problems (repetition, length, structure); "
    "they cannot judge meaning.",
    "AI findings are suggestions, not corrections. Nothing is changed until you accept it.",
    "Findings are tied to the exact document version they reviewed; after an edit they "
    "are marked stale instead of being applied to different text.",
    "Factual findings reuse the Phase 5 verification results. They do not prove a claim is "
    "true - they report what the evidence you retrieved said.",
]

AI_LIMITATION = (
    "The configured AI provider does not support document review, so only deterministic "
    "checks ran. Set AI_PROVIDER=groq with a valid key to enable language-model review."
)

_SEVERITY_BY_NAME = {severity.value: severity for severity in Severity}
_CATEGORY_BY_NAME = {category.value: category for category in ReviewCategory}


def split_sentences(text: str) -> List[str]:
    """Split text into sentences without external NLP dependencies."""
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text or "") if part.strip()]


class ReviewService:
    """Runs reviews and manages their findings."""

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
        self.briefs = DocumentBriefRepository(db)
        self.reviews = ReviewRepository(db)
        self.proposals = EditProposalRepository(db)
        self.version_notes = VersionNoteRepository(db)
        self.verifications = VerificationRepository(db)
        self.citations = CitationRepository(db)
        self.evidence = EvidenceRepository(db)
        self.sessions = ResearchRepository(db)
        self.compliance = ComplianceRepository(db)
        self.citation_service = CitationService(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def start_review(
        self, document_id: str, user_id: str, request: StartReviewRequest
    ) -> ReviewReport:
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        index = DocumentTextIndex(document)
        brief = await self._load_brief(document, user_id)
        categories = self._categories_for(request)

        session = ReviewSession(
            user_id=user_id,
            document_id=document_id,
            brief_id=brief.id if brief else None,
            mode=request.mode,
            categories=categories,
            scope=request.scope,
            section_id=request.section_id,
            status=ReviewStatus.RUNNING,
            document_fingerprint=index.fingerprint,
            progress_message="Running deterministic checks",
        )
        await self.reviews.create_session(session)

        limitations = list(LIMITATIONS)
        try:
            findings: List[ReviewFinding] = []

            # --- scope resolution -------------------------------------
            scope_units = index.units
            if request.scope == ReviewScope.SECTION:
                if not request.section_id:
                    raise ValueError("section_id is required for a section review")
                scope_units = index.units_for_section(request.section_id)
                if not scope_units:
                    raise ValueError("Section not found in this document")
            scoped_text = "\n\n".join(unit.text for unit in scope_units)

            # --- deterministic layer ---------------------------------
            findings.extend(
                self._deterministic_findings(
                    document=document,
                    index=index,
                    units=scope_units,
                    categories=categories,
                    brief=brief,
                    session=session,
                )
            )

            # --- citation + verification reuse (Phase 5) -------------
            findings.extend(
                await self._citation_and_factual_findings(
                    document=document,
                    categories=categories,
                    session=session,
                )
            )

            # --- AI layer --------------------------------------------
            if request.use_ai and categories:
                session.progress_message = "Running AI review"
                await self.reviews.update_session(session)

                payload = {
                    "text": scoped_text,
                    "categories": [category.value for category in categories],
                    "requirements": self._requirements_payload(brief),
                    "section_titles": [
                        f"{unit.section_level}. {unit.section_title}" for unit in scope_units
                    ],
                    "evidence": await self._evidence_payload(document_id, user_id),
                }
                try:
                    raw = await self.provider.review_document(payload)
                except Exception as exc:  # provider/network failure
                    logger.warning("AI review failed: %s", type(exc).__name__)
                    raw = None
                    session.provider = self._provider_name()
                    session.provider_message = "AI review raised an error; deterministic findings kept."
                    limitations.append(session.provider_message)

                if raw is None:
                    limitations.append(AI_LIMITATION)
                else:
                    validated, discarded = self._validate_ai_findings(
                        raw, index, categories, session
                    )
                    if discarded:
                        limitations.append(
                            f"{discarded} model suggestion(s) were discarded because they quoted "
                            "text that does not exist in the document or used an unsupported "
                            "category/severity."
                        )
                    findings.extend(validated)

            # --- persist ---------------------------------------------
            findings = self._deduplicate(findings)
            findings.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.category.value))
            await self.reviews.add_findings(findings)
            session.findings_total = len(findings)
            session.status = ReviewStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.progress_message = None
            await self.reviews.update_session(session)

            return ReviewReport(
                session=session,
                findings=findings,
                summary=self._summarise(findings, index.fingerprint),
                limitations=limitations,
            )
        except ValueError:
            session.status = ReviewStatus.FAILED
            session.error = "Invalid review request"
            await self.reviews.update_session(session)
            raise
        except Exception as exc:
            session.status = ReviewStatus.FAILED
            session.error = f"{type(exc).__name__}: {exc}"[:500]
            await self.reviews.update_session(session)
            logger.exception("Review failed")
            raise

    async def report(
        self,
        review_id: str,
        user_id: str,
        *,
        category: Optional[ReviewCategory] = None,
        severity: Optional[Severity] = None,
        status: Optional[FindingStatus] = None,
    ) -> ReviewReport:
        session = await self.reviews.get_session(review_id, user_id)
        if session is None:
            raise ValueError("Review not found")

        findings = await self.reviews.list_findings(
            review_id, user_id, category=category, severity=severity, status=status
        )
        current = await self.documents.get_by_id(session.document_id, user_id)
        fingerprint = DocumentTextIndex(current).fingerprint if current else None
        if fingerprint:
            for finding in findings:
                finding.is_stale = bool(
                    finding.document_fingerprint
                    and finding.document_fingerprint != fingerprint
                )

        return ReviewReport(
            session=session,
            findings=findings,
            summary=self._summarise(findings, fingerprint),
            limitations=list(LIMITATIONS),
        )

    async def latest_report(self, document_id: str, user_id: str) -> Optional[ReviewReport]:
        session = await self.reviews.latest_session(document_id, user_id)
        if session is None:
            return None
        return await self.report(session.id, user_id)

    async def update_finding_status(
        self, finding_id: str, user_id: str, status: FindingStatus
    ) -> Optional[ReviewFinding]:
        return await self.reviews.update_finding_status(finding_id, user_id, status)

    # ------------------------------------------------------------------
    # Category selection
    # ------------------------------------------------------------------
    def _categories_for(self, request: StartReviewRequest) -> List[ReviewCategory]:
        if request.mode == ReviewMode.CUSTOM:
            return list(request.categories or [])
        categories = list(MODE_CATEGORIES.get(request.mode, MODE_CATEGORIES[ReviewMode.FULL]))
        # A custom list narrows a preset mode but never widens it silently.
        if request.categories:
            allowed = set(categories)
            categories = [category for category in request.categories if category in allowed]
        return categories

    # ------------------------------------------------------------------
    # Deterministic checks
    # ------------------------------------------------------------------
    def _deterministic_findings(
        self,
        *,
        document: DocumentIR,
        index: DocumentTextIndex,
        units,
        categories: Sequence[ReviewCategory],
        brief: Optional[DocumentBrief],
        session: ReviewSession,
    ) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []

        def add(**kwargs) -> None:
            findings.append(self._finding(session=session, source=FindingSource.DETERMINISTIC, **kwargs))

        # --- clarity: very long sentences ---------------------------
        if ReviewCategory.CLARITY in categories:
            for unit in units:
                if not unit.is_prose:
                    continue
                for sentence in split_sentences(unit.text):
                    if len(sentence.split()) <= LONG_SENTENCE_WORDS:
                        continue
                    located = index.locate(sentence, hint_block_id=unit.block_id)
                    if located is None:
                        continue
                    add(
                        category=ReviewCategory.CLARITY,
                        severity=Severity.LOW,
                        title="Sentence is very long",
                        explanation=(
                            f"This sentence has {len(sentence.split())} words. Splitting it "
                            "into shorter sentences usually improves readability."
                        ),
                        section_id=unit.section_id,
                        section_title=unit.section_title,
                        block_id=unit.block_id,
                        original_text=located.text,
                        start_offset=located.start,
                        end_offset=located.end,
                    )

        # --- repetition ---------------------------------------------
        if ReviewCategory.REPETITION in categories:
            seen: Dict[str, List[Tuple[str, str, str, int, int]]] = defaultdict(list)
            for unit in units:
                for sentence in split_sentences(unit.text):
                    key = normalize(sentence)
                    if len(key.split()) < MIN_REPEAT_SENTENCE_WORDS:
                        continue
                    located = index.locate(sentence, hint_block_id=unit.block_id)
                    if located is None:
                        continue
                    seen[key].append(
                        (unit.section_id, unit.section_title, unit.block_id, located.start, located.end)
                    )
            for key, occurrences in seen.items():
                if len(occurrences) < 2:
                    continue
                section_id, section_title, block_id, start, end = occurrences[0]
                add(
                    category=ReviewCategory.REPETITION,
                    severity=Severity.MEDIUM,
                    title="Sentence is repeated",
                    explanation=(
                        f"This sentence appears {len(occurrences)} times in the reviewed content. "
                        "Keep one occurrence or vary the wording."
                    ),
                    section_id=section_id,
                    section_title=section_title,
                    block_id=block_id,
                    original_text=index.unit_for_block(block_id).text[start:end],
                    start_offset=start,
                    end_offset=end,
                )

            # Repeated whole paragraphs (different wording inside is fine; an
            # exact duplicate block is always unintended).
            paragraph_seen: Dict[str, Tuple[str, str, str]] = {}
            for unit in units:
                if not unit.is_prose or len(unit.text.split()) < 20:
                    continue
                key = normalize(unit.text)
                if key in paragraph_seen:
                    first_title = paragraph_seen[key][1]
                    add(
                        category=ReviewCategory.REPETITION,
                        severity=Severity.HIGH,
                        title="Paragraph is duplicated",
                        explanation=(
                            f"This paragraph also appears in the section \"{first_title}\". "
                            "Remove one copy or merge them."
                        ),
                        section_id=unit.section_id,
                        section_title=unit.section_title,
                        block_id=unit.block_id,
                        original_text=unit.text[:MAX_QUOTE],
                    )
                else:
                    paragraph_seen[key] = (unit.section_id, unit.section_title, unit.block_id)

        # --- structure: heading jumps -------------------------------
        if ReviewCategory.STRUCTURE in categories and document.content:
            previous_level = document.content[0].level
            for section in document.content[1:]:
                if section.level > previous_level + 1:
                    add(
                        category=ReviewCategory.STRUCTURE,
                        severity=Severity.MEDIUM,
                        title="Heading level skipped",
                        explanation=(
                            f"\"{section.title}\" is level {section.level} but the previous heading "
                            f"was level {previous_level}. Add the missing intermediate heading or "
                            "promote this one."
                        ),
                        section_id=section.id,
                        section_title=section.title,
                    )
                previous_level = section.level

        # --- structure/completeness against the brief ---------------
        if brief is not None:
            titles = {normalize(section.title) for section in document.content}
            if ReviewCategory.COMPLETENESS in categories:
                for required in brief.required_sections or []:
                    if normalize(required) in titles:
                        continue
                    add(
                        category=ReviewCategory.COMPLETENESS,
                        severity=Severity.HIGH,
                        title=f"Missing required section: {required}",
                        explanation=(
                            f"The brief requires a section called \"{required}\", but no section "
                            "with that title exists in the document."
                        ),
                        suggested_text=None,
                    )

            if ReviewCategory.STRUCTURE in categories and brief.outline:
                expected = [normalize(item.title) for item in brief.outline]
                actual = [normalize(section.title) for section in document.content]
                missing = [title for title in expected if title not in actual]
                if missing:
                    add(
                        category=ReviewCategory.STRUCTURE,
                        severity=Severity.HIGH,
                        title="Document does not follow the approved outline",
                        explanation=(
                            "These approved outline headings are absent: "
                            + ", ".join(missing[:6])
                            + "."
                        ),
                    )

        # --- completeness: starved sections -------------------------
        if ReviewCategory.COMPLETENESS in categories:
            for section in document.content:
                words = len(
                    " ".join(
                        block_text(block) for block in section.blocks
                    ).split()
                )
                if words and words < 25:
                    add(
                        category=ReviewCategory.COMPLETENESS,
                        severity=Severity.LOW,
                        title="Section is very short",
                        explanation=(
                            f"\"{section.title}\" contains only {words} words, which may be "
                            "underdeveloped for its role in the document."
                        ),
                        section_id=section.id,
                        section_title=section.title,
                    )
                elif words == 0:
                    add(
                        category=ReviewCategory.COMPLETENESS,
                        severity=Severity.MEDIUM,
                        title="Section has no content",
                        explanation=f"\"{section.title}\" has a heading but no body text.",
                        section_id=section.id,
                        section_title=section.title,
                    )

        return findings

    # ------------------------------------------------------------------
    # Phase 5 reuse: citations and verification
    # ------------------------------------------------------------------
    async def _citation_and_factual_findings(
        self,
        *,
        document: DocumentIR,
        categories: Sequence[ReviewCategory],
        session: ReviewSession,
    ) -> List[ReviewFinding]:
        findings: List[ReviewFinding] = []

        if ReviewCategory.CITATIONS in categories:
            try:
                report = await self.citation_service.reference_list(
                    document.id,
                    session.user_id,
                    style=normalize_style(document.metadata.custom_fields.get("citation_style") or "apa")
                    if document.metadata.custom_fields
                    else "apa",
                    document=document,
                )
            except Exception:  # citation rendering must never fail a review
                logger.warning("Citation review skipped", exc_info=True)
                report = None

            if report is not None:
                for issue in report.issues:
                    findings.append(
                        self._finding(
                            session=session,
                            source=FindingSource.DETERMINISTIC,
                            category=ReviewCategory.CITATIONS,
                            severity=Severity.HIGH if issue.severity == "error" else Severity.MEDIUM,
                            title=f"Citation problem: {issue.code}",
                            explanation=issue.message,
                            citation_ids=[issue.citation_id] if issue.citation_id else [],
                            evidence_ids=[issue.source_id] if issue.source_id else [],
                        )
                    )

        if ReviewCategory.FACTUAL in categories:
            verifications = await self.verifications.list_for_document(
                document.id, session.user_id
            )
            for verification in verifications:
                if verification.status == VerificationStatus.CONTRADICTED:
                    severity = Severity.CRITICAL
                    title = "Claim is contradicted by your evidence"
                elif verification.status == VerificationStatus.INSUFFICIENT_EVIDENCE:
                    severity = Severity.MEDIUM
                    title = "Claim is not supported by your evidence"
                else:
                    continue
                findings.append(
                    self._finding(
                        session=session,
                        source=FindingSource.DETERMINISTIC,
                        category=ReviewCategory.FACTUAL,
                        severity=severity,
                        title=title,
                        explanation=(verification.explanation or "")[:MAX_EXPLANATION],
                        section_id=verification.section_id,
                        section_title=verification.section_title,
                        original_text=(verification.claim_text or "")[:MAX_QUOTE] or None,
                        evidence_ids=list(verification.supporting_evidence_ids)
                        + list(verification.contradicting_evidence_ids),
                    )
                )

        return findings

    # ------------------------------------------------------------------
    # AI output validation
    # ------------------------------------------------------------------
    def _validate_ai_findings(
        self,
        raw: Dict,
        index: DocumentTextIndex,
        categories: Sequence[ReviewCategory],
        session: ReviewSession,
    ) -> Tuple[List[ReviewFinding], int]:
        """Convert untrusted model output into stored findings.

        Anything we cannot verify is dropped and counted, never silently kept.
        """
        allowed_categories = set(categories)
        validated: List[ReviewFinding] = []
        discarded = 0

        items = raw.get("findings") if isinstance(raw, dict) else None
        if not isinstance(items, list):
            return [], 1

        for item in items[: MAX_AI_FINDINGS * 2]:
            if not isinstance(item, dict):
                discarded += 1
                continue

            category = _CATEGORY_BY_NAME.get(str(item.get("category") or "").strip().lower())
            if category is None or category not in allowed_categories:
                discarded += 1
                continue

            severity = _SEVERITY_BY_NAME.get(
                str(item.get("severity") or "").strip().lower(), Severity.MEDIUM
            )

            quote = str(item.get("original_text") or "").strip()[:MAX_QUOTE]
            if not quote:
                discarded += 1
                continue

            located = index.locate(quote)
            if located is None:
                # The model paraphrased or invented the passage: unusable.
                discarded += 1
                continue

            suggestion = item.get("suggested_text")
            suggestion = (
                str(suggestion).strip()[:MAX_SUGGESTION] if isinstance(suggestion, str) else None
            )
            if suggestion and suggestion == located.text:
                suggestion = None

            title = str(item.get("title") or CATEGORY_LABELS[category]).strip()[:MAX_TITLE]
            explanation = str(item.get("explanation") or "").strip()[:MAX_EXPLANATION]

            validated.append(
                self._finding(
                    session=session,
                    source=FindingSource.AI,
                    category=category,
                    severity=severity,
                    title=title or CATEGORY_LABELS[category],
                    explanation=explanation
                    or "The reviewer flagged this passage without a detailed explanation.",
                    section_id=located.unit.section_id,
                    section_title=located.unit.section_title,
                    block_id=located.unit.block_id,
                    original_text=located.text,
                    start_offset=located.start,
                    end_offset=located.end,
                    suggested_text=suggestion,
                )
            )
            if len(validated) >= MAX_AI_FINDINGS:
                break

        return validated, discarded

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _finding(self, *, session: ReviewSession, **kwargs) -> ReviewFinding:
        return ReviewFinding(
            user_id=session.user_id,
            review_id=session.id,
            document_id=session.document_id,
            document_fingerprint=session.document_fingerprint,
            **kwargs,
        )

    def _deduplicate(self, findings: List[ReviewFinding]) -> List[ReviewFinding]:
        """Drop duplicates so one passage is not reported twice by two layers."""
        seen = set()
        unique: List[ReviewFinding] = []
        for finding in findings:
            key = (
                finding.category,
                finding.block_id,
                finding.start_offset,
                finding.end_offset,
                normalize(finding.original_text or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(finding)
        return unique

    def _summarise(self, findings: List[ReviewFinding], fingerprint: Optional[str]) -> ReviewSummary:
        by_severity: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        stale = 0
        open_count = 0
        for finding in findings:
            by_severity[finding.severity.value] = by_severity.get(finding.severity.value, 0) + 1
            by_category[finding.category.value] = by_category.get(finding.category.value, 0) + 1
            by_status[finding.status.value] = by_status.get(finding.status.value, 0) + 1
            if finding.status == FindingStatus.OPEN:
                open_count += 1
            if fingerprint and finding.document_fingerprint and finding.document_fingerprint != fingerprint:
                stale += 1
        return ReviewSummary(
            total=len(findings),
            by_severity=by_severity,
            by_category=by_category,
            by_status=by_status,
            stale=stale,
            open=open_count,
        )

    async def _load_brief(
        self, document: DocumentIR, user_id: str
    ) -> Optional[DocumentBrief]:
        custom = document.metadata.custom_fields or {}
        brief_id = custom.get("brief_id")
        if brief_id:
            brief = await self.briefs.get_by_id(brief_id, user_id)
            if brief:
                return brief
        # Fall back to any brief that points at this document.
        briefs, _ = await self.briefs.list_by_user(user_id, limit=200)
        return next((brief for brief in briefs if brief.document_id == document.id), None)

    def _requirements_payload(self, brief: Optional[DocumentBrief]) -> Dict:
        if brief is None:
            return {}
        return {
            "document_type": brief.document_type,
            "title": brief.title,
            "audience": brief.audience,
            "tone": brief.tone,
            "desired_length": brief.desired_length,
            "required_sections": brief.required_sections,
            "important_points": brief.important_points,
        }

    async def _evidence_payload(self, document_id: str, user_id: str) -> List[Dict]:
        session = await self.sessions.get_latest_for_document(document_id, user_id)
        if session is None:
            return []
        records = await self.evidence.list_by_session(session.id, user_id, selected_only=True)
        return [
            {"marker": f"E{index}", "title": record.claim_or_finding, "text": record.passage[:1200]}
            for index, record in enumerate(records[:8], 1)
        ]

    def _provider_name(self) -> str:
        return type(self.provider).__name__
