"""Factual-verification tests.

These cover the four required statuses, the quote-provenance guard (an AI claim
that cannot quote the evidence is downgraded), the numeric guard, deterministic
claim extraction and ownership isolation.
"""
import pytest

from app.core.config import Settings
from app.models.research import (
    ClaimVerification,
    EvidenceRecord,
    ResearchSession,
    ResearchSource,
    RetrievalStatus,
    VerificationStatus,
)
from app.repositories.document_repository import DocumentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.services.claim_extraction import classify_sentence, extract_claims, is_time_sensitive
from app.services.verification_service import VerificationService

SUPPORTING_PASSAGE = (
    "The report was published by the World Institute in March 2023 after an "
    "independent review of the findings."
)


class StubAssessor:
    """Minimal provider double exposing only ``assess_claim``."""

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    async def assess_claim(self, claim, passages):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def settings() -> Settings:
    return Settings(VERIFICATION_MAX_CLAIMS=20, VERIFICATION_MIN_LEXICAL_OVERLAP=0.18)


async def build_context(db, user_id, passage=SUPPORTING_PASSAGE, title="World Institute"):
    session = await ResearchRepository(db).create_session(
        ResearchSession(user_id=user_id, title="Verification session")
    )
    source = await ResearchSourceRepository(db).create(
        ResearchSource(
            session_id=session.id,
            user_id=user_id,
            retrieval_status=RetrievalStatus.FETCHED,
            title=title,
            url="https://93.184.216.34/report",
            author="Jane Doe",
            publisher="World Institute",
            published_date="2023-03-05",
            content_text=passage,
            selected=True,
        )
    )
    evidence = await EvidenceRepository(db).create(
        EvidenceRecord(
            session_id=session.id,
            source_id=source.id,
            user_id=user_id,
            claim_or_finding=passage[:120],
            passage=passage,
        )
    )
    return session, source, evidence


async def build_document(db, document_factory, user_id, paragraphs):
    document = document_factory(paragraphs=paragraphs)
    return await DocumentRepository(db).create(document, user_id=user_id)


# ---------------------------------------------------------------------------
# Deterministic extraction
# ---------------------------------------------------------------------------

def test_classify_sentence_distinguishes_claim_types():
    assert classify_sentence("The policy requires annual audits of all systems.") == "factual"
    assert classify_sentence("We should migrate to a new platform.") == "recommendation"
    assert classify_sentence("The market will double by 2030.") == "prediction"
    assert classify_sentence("I think the design is beautiful.") == "opinion"
    assert classify_sentence("What does the policy require?") == "question"


def test_time_sensitive_claims_are_flagged():
    assert is_time_sensitive("The system currently processes 42 percent of records.")
    assert is_time_sensitive("In 2023 the policy was updated.")
    assert not is_time_sensitive("Water boils at one hundred degrees.")


def test_extraction_skips_opinions_and_short_sentences(document_factory):
    document = document_factory(
        paragraphs=[
            "The report was published by the World Institute in March 2023.",
            "We should rewrite the entire document immediately.",
            "Nice.",
        ]
    )
    result = extract_claims(document)
    texts = [claim.text for claim in result.claims]
    assert any("World Institute" in text for text in texts)
    assert not any("should rewrite" in text for text in texts)
    assert result.skipped_count >= 2


def test_claim_ids_are_stable(document_factory):
    document = document_factory(paragraphs=["The report was published by the World Institute."])
    first = extract_claims(document).claims[0].claim_id
    second = extract_claims(document).claims[0].claim_id
    assert first == second


# ---------------------------------------------------------------------------
# Verification statuses
# ---------------------------------------------------------------------------

async def test_supported_claim_with_verbatim_quote(db, user, document_factory):
    session, source, evidence = await build_context(db, user.id)
    document = await build_document(
        db, document_factory, user.id,
        ["The report was published by the World Institute in March 2023."],
    )

    assessor = StubAssessor(
        result={
            "status": "supported",
            "explanation": "The passage states publication by the World Institute.",
            "quotes": [{"marker": "P1", "quote": "published by the World Institute"}],
        }
    )
    service = VerificationService(db, provider=assessor, settings=settings())
    report = await service.verify_document(document.id, user.id, research_session_id=session.id)

    assert report.findings[0].status == VerificationStatus.SUPPORTED
    assert report.findings[0].supporting_evidence_ids == [evidence.id]
    assert report.findings[0].verification_method == "ai_assisted_with_quote_verification"
    assert report.summary.supported == 1


async def test_contradicted_claim_keeps_conflicting_evidence(db, user, document_factory):
    passage = "The platform is hosted in Canada, according to the operations handbook."
    session, source, evidence = await build_context(db, user.id, passage=passage)
    document = await build_document(
        db, document_factory, user.id, ["The platform is hosted in Germany."]
    )

    assessor = StubAssessor(
        result={
            "status": "contradicted",
            "explanation": "The handbook says Canada.",
            "quotes": [{"marker": "P1", "quote": "hosted in Canada"}],
        }
    )
    service = VerificationService(db, provider=assessor, settings=settings())
    report = await service.verify_document(document.id, user.id, research_session_id=session.id)

    assert report.findings[0].status == VerificationStatus.CONTRADICTED
    assert report.findings[0].contradicting_evidence_ids == [evidence.id]


async def test_no_evidence_means_insufficient_not_supported(db, user, document_factory):
    session = await ResearchRepository(db).create_session(
        ResearchSession(user_id=user.id, title="Empty session")
    )
    document = await build_document(
        db, document_factory, user.id, ["The report was published by the World Institute."]
    )

    assessor = StubAssessor(result=None)
    service = VerificationService(db, provider=assessor, settings=settings())
    report = await service.verify_document(document.id, user.id, research_session_id=session.id)

    assert report.findings[0].status == VerificationStatus.INSUFFICIENT_EVIDENCE
    assert report.findings[0].verification_method == "no_evidence"
    assert assessor.calls == 0


async def test_unquoted_ai_support_is_downgraded(db, user, document_factory):
    """An LLM saying "supported" without a real quote proves nothing."""
    session, _source, _evidence = await build_context(db, user.id)
    document = await build_document(
        db, document_factory, user.id,
        ["The report was published by the World Institute in March 2023."],
    )

    assessor = StubAssessor(
        result={
            "status": "supported",
            "explanation": "Trust me.",
            "quotes": [{"marker": "P1", "quote": "this text is not in the passage at all"}],
        }
    )
    service = VerificationService(db, provider=assessor, settings=settings())
    report = await service.verify_document(document.id, user.id, research_session_id=session.id)

    finding = report.findings[0]
    assert finding.status == VerificationStatus.INSUFFICIENT_EVIDENCE
    assert finding.verification_method == "ai_quotes_unverified"


async def test_numeric_mismatch_is_not_supported(db, user, document_factory):
    passage = "The platform processed 42 percent of records in the first quarter of 2023."
    session, _source, _evidence = await build_context(db, user.id, passage=passage)
    document = await build_document(
        db, document_factory, user.id,
        ["The platform processed 57 percent of records in the first quarter of 2023."],
    )

    assessor = StubAssessor(
        result={
            "status": "supported",
            "explanation": "Looks close enough.",
            "quotes": [{"marker": "P1", "quote": "processed 42 percent of records"}],
        }
    )
    service = VerificationService(db, provider=assessor, settings=settings())
    report = await service.verify_document(document.id, user.id, research_session_id=session.id)

    finding = report.findings[0]
    assert finding.status == VerificationStatus.INSUFFICIENT_EVIDENCE
    assert finding.verification_method == "numeric_check"
    assert assessor.calls == 0


async def test_provider_error_marks_claim_not_checked(db, user, document_factory):
    session, _source, _evidence = await build_context(db, user.id)
    document = await build_document(
        db, document_factory, user.id,
        ["The report was published by the World Institute in March 2023."],
    )

    assessor = StubAssessor(error=RuntimeError("groq unavailable"))
    service = VerificationService(db, provider=assessor, settings=settings())
    report = await service.verify_document(document.id, user.id, research_session_id=session.id)

    assert report.findings[0].status == VerificationStatus.NOT_CHECKED
    assert report.findings[0].verification_method == "provider_error"


async def test_opinions_are_not_verified_as_claims(db, user, document_factory):
    session, _source, _evidence = await build_context(db, user.id)
    document = await build_document(
        db, document_factory, user.id,
        ["We should migrate the entire platform to a different vendor next year."],
    )

    service = VerificationService(db, provider=StubAssessor(result=None), settings=settings())
    report = await service.verify_document(document.id, user.id, research_session_id=session.id)
    assert report.findings == []


async def test_verification_limit_marks_remaining_claims_not_checked(db, user, document_factory):
    session, _source, _evidence = await build_context(db, user.id, passage=SUPPORTING_PASSAGE)
    document = await build_document(
        db,
        document_factory,
        user.id,
        [
            "The report was published by the World Institute in March 2023.",
            "The audit was completed by an independent reviewer in April 2023.",
        ],
    )

    service = VerificationService(db, provider=StubAssessor(result=None), settings=settings())
    report = await service.verify_document(
        document.id, user.id, research_session_id=session.id, max_claims=1
    )

    statuses = {finding.status for finding in report.findings}
    assert VerificationStatus.NOT_CHECKED in statuses
    assert len(report.findings) == 2


async def test_recheck_is_idempotent(db, user, document_factory):
    session, _source, _evidence = await build_context(db, user.id)
    document = await build_document(
        db, document_factory, user.id,
        ["The report was published by the World Institute in March 2023."],
    )

    service = VerificationService(db, provider=StubAssessor(result=None), settings=settings())
    first = await service.verify_document(document.id, user.id, research_session_id=session.id)
    second = await service.verify_document(document.id, user.id, research_session_id=session.id)

    assert len(first.findings) == len(second.findings) == 1
    findings = await service.verifications.list_for_document(document.id, user.id)
    assert len(findings) == 1, "re-verification must update, not duplicate"


async def test_verification_requires_ownership(db, user, other_user, document_factory):
    session, _source, _evidence = await build_context(db, user.id)
    document = await build_document(
        db, document_factory, user.id,
        ["The report was published by the World Institute in March 2023."],
    )

    service = VerificationService(db, provider=StubAssessor(result=None), settings=settings())
    with pytest.raises(ValueError):
        await service.verify_document(document.id, other_user.id, research_session_id=session.id)


async def test_report_reads_back_stored_findings(db, user, document_factory):
    session, _source, _evidence = await build_context(db, user.id)
    document = await build_document(
        db, document_factory, user.id,
        ["The report was published by the World Institute in March 2023."],
    )
    service = VerificationService(db, provider=StubAssessor(result=None), settings=settings())
    await service.verify_document(document.id, user.id, research_session_id=session.id)

    report = await service.report(document.id, user.id)
    assert report.summary.total == 1
    assert report.limitations
    filtered = await service.report(
        document.id, user.id, VerificationStatus.INSUFFICIENT_EVIDENCE
    )
    assert len(filtered.findings) == 1
    empty = await service.report(document.id, user.id, VerificationStatus.SUPPORTED)
    assert empty.findings == []
