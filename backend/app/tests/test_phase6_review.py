"""Phase 6 tests: review engine, findings, editing, compliance, versions.

Every test runs offline. Providers are either the real ``MockProvider`` (which
is deterministic) or a small ``FakeProvider`` defined here, so a failing test
means the code is wrong - not that the network was flaky.
"""
import pytest

from app.models.document_brief import OutlineItem
from app.models.document_ir import (
    DocumentIR,
    DocumentMetadata,
    InlineContent,
    Paragraph,
    Section,
    Table,
)
from app.models.research import (
    ClaimVerification,
    CitationRecord,
    EvidenceRecord,
    ResearchSession,
    ResearchSource,
    RetrievalStatus,
    VerificationStatus,
)
from app.models.review import (
    ComplianceStatus,
    EditOperation,
    FindingStatus,
    FindingSource,
    ProposeEditRequest,
    ProposalStatus,
    ReviewCategory,
    ReviewMode,
    ReviewScope,
    Severity,
    StartReviewRequest,
    VersionOrigin,
)
from app.providers.mock_provider import MockProvider
from app.repositories.citation_repository import CitationRepository
from app.repositories.document_brief_repository import DocumentBriefRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.repositories.review_repository import EditProposalRepository, ReviewRepository
from app.repositories.verification_repository import VerificationRepository
from app.services.compliance_service import ComplianceService
from app.services.document_text import DocumentTextIndex
from app.services.editing_service import EditConflict, EditingService
from app.services.review_service import ReviewService
from app.services.version_service import VersionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_document(*sections, title="Audit report", doc_type="general_report"):
    return DocumentIR(
        title=title,
        content=[
            Section(
                level=level,
                title=section_title,
                blocks=[Paragraph(content=[InlineContent(text=text)]) for text in paragraphs],
            )
            for level, section_title, paragraphs in sections
        ],
        metadata=DocumentMetadata(document_type=doc_type, tone="formal"),
    )


async def save_document(db, user_id, document):
    return await DocumentRepository(db).create(document, user_id=user_id)


class FakeProvider(MockProvider):
    """Provider whose review output the test controls exactly."""

    def __init__(self, findings=None, rewrite=None, raise_on=None):
        self._findings = findings or []
        self._rewrite = rewrite
        self._raise_on = raise_on

    async def review_document(self, payload):
        if self._raise_on == "review":
            raise RuntimeError("provider exploded")
        return {"findings": self._findings}

    async def transform_text(self, payload):
        if self._raise_on == "transform":
            raise RuntimeError("provider exploded")
        if self._rewrite is not None:
            return self._rewrite
        return await super().transform_text(payload)

    async def assess_compliance(self, payload):
        if self._raise_on == "compliance":
            raise RuntimeError("provider exploded")
        return await super().assess_compliance(payload)


async def seed_brief(db, user_id, document_id=None, **overrides):
    repo = DocumentBriefRepository(db)
    payload = {
        "document_type": "general_report",
        "title": "Audit brief",
        "topic": "Audit policy",
        "language": "en",
        "required_sections": [],
        "important_points": [],
        "topics_to_avoid": [],
        "desired_length": None,
    }
    payload.update(overrides)
    brief = await repo.create(payload, user_id=user_id)
    if document_id:
        await repo.update(brief.id, user_id, {"document_id": document_id})
        brief = await repo.get_by_id(brief.id, user_id)
    return brief


REPEATED = (
    "The annual audit policy requires an independent review of every financial "
    "statement before the board approves the final published report."
)


# ---------------------------------------------------------------------------
# 1-4: review modes, scope, deterministic findings
# ---------------------------------------------------------------------------

async def test_full_review_detects_repeated_sentence(test_db, user):
    document = build_document(
        (1, "Introduction", [REPEATED]),
        (1, "Findings", [REPEATED, "A short explanatory paragraph follows here."]),
    )
    await save_document(test_db, user.id, document)

    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.FULL)
    )

    repetition = [f for f in report.findings if f.category == ReviewCategory.REPETITION]
    assert repetition, "repeated sentence should be reported"
    assert all(f.source == FindingSource.DETERMINISTIC for f in repetition)
    assert repetition[0].severity in (Severity.MEDIUM, Severity.HIGH)
    assert report.session.status.value == "completed"
    assert report.summary.total == len(report.findings)


async def test_quick_mode_limits_categories(test_db, user):
    document = build_document((1, "Body", [REPEATED]))
    await save_document(test_db, user.id, document)

    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.QUICK)
    )
    assert set(report.session.categories) == {
        ReviewCategory.GRAMMAR,
        ReviewCategory.SPELLING,
        ReviewCategory.CLARITY,
    }
    assert all(
        f.category in (ReviewCategory.GRAMMAR, ReviewCategory.SPELLING, ReviewCategory.CLARITY)
        for f in report.findings
    )


async def test_custom_mode_uses_requested_categories(test_db, user):
    document = build_document((1, "Body", [REPEATED]), (1, "More", [REPEATED]))
    await save_document(test_db, user.id, document)

    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id,
        user.id,
        StartReviewRequest(mode=ReviewMode.CUSTOM, categories=[ReviewCategory.REPETITION]),
    )
    assert report.session.categories == [ReviewCategory.REPETITION]
    assert any(f.category == ReviewCategory.REPETITION for f in report.findings)


async def test_section_review_only_covers_that_section(test_db, user):
    long_sentence = " ".join(["word"] * 45) + "."
    document = build_document(
        (1, "First", ["Nothing wrong in this short sentence."]),
        (1, "Second", [long_sentence]),
    )
    await save_document(test_db, user.id, document)
    second_id = document.content[1].id

    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id,
        user.id,
        StartReviewRequest(
            mode=ReviewMode.QUICK, scope=ReviewScope.SECTION, section_id=second_id
        ),
    )
    assert report.session.scope == ReviewScope.SECTION
    assert report.findings, "the long sentence should be found"
    assert all(f.section_id == second_id for f in report.findings)


async def test_section_review_rejects_unknown_section(test_db, user):
    document = build_document((1, "Body", ["Text here."]))
    await save_document(test_db, user.id, document)
    service = ReviewService(test_db, provider=FakeProvider())
    with pytest.raises(ValueError):
        await service.start_review(
            document.id,
            user.id,
            StartReviewRequest(scope=ReviewScope.SECTION, section_id="does-not-exist"),
        )


async def test_structure_review_flags_heading_jump(test_db, user):
    document = DocumentIR(
        title="Jumping headings",
        content=[
            Section(level=1, title="Top", blocks=[Paragraph(content=[InlineContent(text="Body text here.")])]),
            Section(level=4, title="Deep", blocks=[Paragraph(content=[InlineContent(text="More body text.")])]),
        ],
        metadata=DocumentMetadata(document_type="general_report"),
    )
    await save_document(test_db, user.id, document)
    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.FULL)
    )
    titles = [f.title for f in report.findings]
    assert "Heading level skipped" in titles


async def test_completeness_flags_missing_required_section(test_db, user):
    document = build_document((1, "Introduction", ["Intro text that is long enough to be reasonable here."]))
    document.metadata.custom_fields = {"brief_id": "placeholder"}
    await save_document(test_db, user.id, document)
    brief = await seed_brief(
        test_db,
        user.id,
        document_id=document.id,
        required_sections=["Methodology", "Introduction"],
    )
    document.metadata.custom_fields = {"brief_id": brief.id}
    await DocumentRepository(test_db).update(document)

    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.FULL)
    )
    missing = [f for f in report.findings if "Missing required section" in f.title]
    assert any("Methodology" in f.title for f in missing)
    assert not any("Introduction" in f.title for f in missing)


# ---------------------------------------------------------------------------
# 5-8: AI output validation
# ---------------------------------------------------------------------------

async def test_ai_finding_with_valid_quote_gets_real_offsets(test_db, user):
    sentence = "This sentence is perfectly locatable in the document body."
    document = build_document((1, "Body", [sentence]))
    await save_document(test_db, user.id, document)

    provider = FakeProvider(
        findings=[
            {
                "category": "clarity",
                "severity": "low",
                "title": "Vague wording",
                "explanation": "Consider being more specific.",
                "original_text": sentence,
                "suggested_text": "A clearer sentence.",
            }
        ]
    )
    service = ReviewService(test_db, provider=provider)
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.QUICK)
    )

    ai = [f for f in report.findings if f.source == FindingSource.AI]
    assert len(ai) == 1
    finding = ai[0]
    assert finding.block_id == document.content[0].blocks[0].id
    assert finding.start_offset == 0
    assert finding.end_offset == len(sentence)
    assert finding.suggested_text == "A clearer sentence."


async def test_ai_finding_with_fabricated_quote_is_discarded(test_db, user):
    document = build_document((1, "Body", ["A completely ordinary sentence about audits."]))
    await save_document(test_db, user.id, document)

    provider = FakeProvider(
        findings=[
            {
                "category": "clarity",
                "severity": "high",
                "title": "Invented problem",
                "explanation": "This text does not exist.",
                "original_text": "This sentence was never written by the author at all.",
            }
        ]
    )
    service = ReviewService(test_db, provider=provider)
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.QUICK)
    )
    assert not [f for f in report.findings if f.source == FindingSource.AI]
    assert any("discarded" in limitation for limitation in report.limitations)


async def test_ai_finding_with_unsupported_category_is_discarded(test_db, user):
    document = build_document((1, "Body", ["Ordinary sentence for the document body."]))
    await save_document(test_db, user.id, document)

    provider = FakeProvider(
        findings=[
            {
                "category": "vibes",
                "severity": "high",
                "title": "Not a category",
                "explanation": "x",
                "original_text": "Ordinary sentence for the document body.",
            },
            {
                # valid category but outside the requested set (quick = grammar/spelling/clarity)
                "category": "citations",
                "severity": "high",
                "title": "Out of scope",
                "explanation": "x",
                "original_text": "Ordinary sentence for the document body.",
            },
        ]
    )
    service = ReviewService(test_db, provider=provider)
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.QUICK)
    )
    assert not [f for f in report.findings if f.source == FindingSource.AI]


async def test_ai_unknown_severity_falls_back_to_medium(test_db, user):
    text = "Locatable sentence about the audit process and its controls."
    document = build_document((1, "Body", [text]))
    await save_document(test_db, user.id, document)

    provider = FakeProvider(
        findings=[
            {
                "category": "clarity",
                "severity": "catastrophic",
                "title": "Weird severity",
                "explanation": "x",
                "original_text": text,
            }
        ]
    )
    service = ReviewService(test_db, provider=provider)
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.QUICK)
    )
    ai = [f for f in report.findings if f.source == FindingSource.AI]
    assert ai and ai[0].severity == Severity.MEDIUM


async def test_provider_error_is_reported_not_raised(test_db, user):
    document = build_document((1, "Body", ["A sentence long enough to be reviewed properly."]))
    await save_document(test_db, user.id, document)

    service = ReviewService(test_db, provider=FakeProvider(raise_on="review"))
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.FULL)
    )
    assert report.session.status.value == "completed"
    assert any("error" in limitation.lower() for limitation in report.limitations)


# ---------------------------------------------------------------------------
# 9-11: status changes, staleness, duplicate suppression
# ---------------------------------------------------------------------------

async def test_finding_status_changes(test_db, user):
    document = build_document((1, "A", [REPEATED]), (1, "B", [REPEATED]))
    await save_document(test_db, user.id, document)
    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.FULL)
    )
    finding = report.findings[0]

    updated = await service.update_finding_status(finding.id, user.id, FindingStatus.ACCEPTED)
    assert updated.status == FindingStatus.ACCEPTED

    ignored = await service.update_finding_status(finding.id, user.id, FindingStatus.IGNORED)
    assert ignored.status == FindingStatus.IGNORED

    assert await service.update_finding_status("nope", user.id, FindingStatus.REJECTED) is None


async def test_findings_become_stale_after_document_edit(test_db, user):
    document = build_document((1, "Body", [REPEATED, REPEATED]))
    await save_document(test_db, user.id, document)

    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.FULL)
    )
    assert report.findings

    # Change the document, then re-read the same review.
    document.content[0].blocks[0].content[0].text = "The text was edited afterwards."
    await DocumentRepository(test_db).update(document)

    reread = await service.report(report.session.id, user.id)
    assert reread.findings
    assert all(f.is_stale for f in reread.findings)
    assert reread.summary.stale == len(reread.findings)


async def test_duplicate_findings_are_suppressed(test_db, user):
    text = "A single sentence that is long enough to be repeated elsewhere in the document body."
    document = build_document((1, "One", [text]), (1, "Two", [text]))
    await save_document(test_db, user.id, document)
    service = ReviewService(test_db, provider=MockProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.FULL)
    )
    keys = [
        (f.category, f.block_id, f.start_offset, f.end_offset, f.original_text)
        for f in report.findings
    ]
    assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# 12-14: Phase 5 reuse (citations, verification)
# ---------------------------------------------------------------------------

async def test_factual_findings_reuse_verification_records(test_db, user):
    document = build_document((1, "Findings", ["The policy requires an independent review."]))
    await save_document(test_db, user.id, document)

    await VerificationRepository(test_db).upsert(
        ClaimVerification(
            user_id=user.id,
            document_id=document.id,
            claim_id="did:1",
            claim_text="The policy requires an independent review.",
            section_id=document.content[0].id,
            section_title="Findings",
            status=VerificationStatus.CONTRADICTED,
            explanation="The retrieved evidence says the opposite.",
        )
    )

    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.ACADEMIC)
    )
    factual = [f for f in report.findings if f.category == ReviewCategory.FACTUAL]
    assert factual and factual[0].severity == Severity.CRITICAL
    assert "contradicted" in factual[0].title.lower()


async def test_citation_review_surfaces_phase5_issues(test_db, user):
    document = build_document((1, "Findings", ["A cited claim appears here."]))
    await save_document(test_db, user.id, document)

    session = await ResearchRepository(test_db).create_session(
        ResearchSession(user_id=user.id, document_id=document.id, title="Research")
    )
    source = await ResearchSourceRepository(test_db).create(
        ResearchSource(
            session_id=session.id,
            user_id=user.id,
            retrieval_status=RetrievalStatus.FETCHED,
            title="Audit policy",
            url="https://example.org/a",
            content_text="Evidence text about the audit policy.",
        )
    )
    # A citation whose section no longer exists should surface as an anchor issue.
    await CitationRepository(test_db).create(
        CitationRecord(
            user_id=user.id,
            document_id=document.id,
            source_id=source.id,
            section_id="vanished-section",
            section_title="Old section",
            style="apa",
            in_text="(Example, 2023)",
        )
    )

    service = ReviewService(test_db, provider=FakeProvider())
    report = await service.start_review(
        document.id, user.id, StartReviewRequest(mode=ReviewMode.ACADEMIC)
    )
    citation_findings = [f for f in report.findings if f.category == ReviewCategory.CITATIONS]
    assert citation_findings, "Phase 5 citation integrity issues should be reused"
    # Issues carry whichever id Phase 5 attached: a citation id for broken
    # anchors, or a source id for uncited sources.
    assert any(f.citation_ids or f.evidence_ids for f in citation_findings)


# ---------------------------------------------------------------------------
# 15-18: DocumentBrief compliance
# ---------------------------------------------------------------------------

async def test_compliance_word_count_is_deterministic(test_db, user):
    document = build_document((1, "Body", ["word " * 100]))
    document.metadata.custom_fields = {"brief_id": "placeholder"}
    await save_document(test_db, user.id, document)
    brief = await seed_brief(test_db, user.id, document_id=document.id, desired_length="long")
    document.metadata.custom_fields = {"brief_id": brief.id}
    await DocumentRepository(test_db).update(document)

    service = ComplianceService(test_db, provider=FakeProvider())
    report = await service.check(document.id, user.id)
    length = [r for r in report.results if r.requirement.startswith("Approximate length")]
    assert length
    assert length[0].status in (ComplianceStatus.NOT_MET, ComplianceStatus.PARTIALLY_MET)


async def test_compliance_sections_and_forbidden_topics(test_db, user):
    document = build_document((1, "Introduction", ["This document mentions cryptocurrency casually."]))
    document.metadata.custom_fields = {"brief_id": "placeholder"}
    await save_document(test_db, user.id, document)
    brief = await seed_brief(
        test_db,
        user.id,
        document_id=document.id,
        required_sections=["Conclusion"],
        topics_to_avoid=["cryptocurrency"],
    )
    document.metadata.custom_fields = {"brief_id": brief.id}
    await DocumentRepository(test_db).update(document)

    service = ComplianceService(test_db, provider=FakeProvider())
    report = await service.check(document.id, user.id)

    by_requirement = {r.requirement: r for r in report.results}
    assert by_requirement['Include the section "Conclusion"'].status == ComplianceStatus.NOT_MET
    assert by_requirement['Avoid covering "cryptocurrency"'].status == ComplianceStatus.NOT_MET
    assert report.overall == ComplianceStatus.NOT_MET


async def test_compliance_without_brief_is_not_applicable(test_db, user):
    document = build_document((1, "Body", ["Some content here."]))
    await save_document(test_db, user.id, document)
    service = ComplianceService(test_db, provider=FakeProvider())
    report = await service.check(document.id, user.id)
    assert report.overall == ComplianceStatus.NOT_APPLICABLE
    assert report.results == []


async def test_compliance_qualitative_rows_are_labelled(test_db, user):
    document = build_document((1, "Body", ["Some content that should be assessed qualitatively."]))
    document.metadata.custom_fields = {"brief_id": "placeholder"}
    await save_document(test_db, user.id, document)
    brief = await seed_brief(
        test_db,
        user.id,
        document_id=document.id,
        tone="formal",
        audience="the board",
    )
    document.metadata.custom_fields = {"brief_id": brief.id}
    await DocumentRepository(test_db).update(document)

    service = ComplianceService(test_db, provider=FakeProvider())
    report = await service.check(document.id, user.id)
    qualitative = [r for r in report.results if r.requirement.startswith(("Use a", "Address the"))]
    assert qualitative
    # The mock cannot judge tone/audience, so it must say Needs Manual Review.
    assert all(r.status == ComplianceStatus.NEEDS_REVIEW for r in qualitative)
    assert all(r.method != "deterministic" for r in qualitative)


# ---------------------------------------------------------------------------
# 19-22: AI editing, versioning, conflicts
# ---------------------------------------------------------------------------

async def test_propose_edit_preserves_citation_markers(test_db, user):
    text = "The audit policy requires review [E1] before publication."
    document = build_document((1, "Body", [text]))
    await save_document(test_db, user.id, document)

    service = EditingService(test_db, provider=MockProvider())
    proposal = await service.propose(
        document.id,
        user.id,
        ProposeEditRequest(
            operation=EditOperation.FIX_GRAMMAR,
            target_type="section",
            section_id=document.content[0].id,
        ),
    )
    assert proposal.status == ProposalStatus.PROPOSED
    assert "[E1]" in proposal.proposed_text
    # Proposal creation must not touch the stored document.
    stored = await DocumentRepository(test_db).get_by_id(document.id, user.id)
    assert stored.content[0].blocks[0].content[0].text == text


async def test_apply_proposal_creates_versions_and_updates_document(test_db, user):
    document = build_document((1, "Body", ["the audit policy requires review."]))
    await save_document(test_db, user.id, document)

    service = EditingService(test_db, provider=MockProvider())
    proposal = await service.propose(
        document.id,
        user.id,
        ProposeEditRequest(operation=EditOperation.FIX_GRAMMAR, target_type="section", section_id=document.content[0].id),
    )
    updated, applied = await service.apply(proposal.id, user.id)

    assert applied.status == ProposalStatus.ACCEPTED
    assert updated.content[0].blocks[0].content[0].text == proposal.proposed_text

    stored = await DocumentRepository(test_db).get_by_id(document.id, user.id)
    assert stored.content[0].blocks[0].content[0].text == proposal.proposed_text

    versions = await VersionService(test_db).list_versions(document.id, user.id)
    assert len(versions) == 2
    assert all(v.origin == VersionOrigin.AI_ACCEPTED for v in versions)


async def test_apply_proposal_rejects_stale_fingerprint(test_db, user):
    document = build_document((1, "Body", ["the audit policy requires review."]))
    await save_document(test_db, user.id, document)

    service = EditingService(test_db, provider=MockProvider())
    proposal = await service.propose(
        document.id,
        user.id,
        ProposeEditRequest(operation=EditOperation.FIX_GRAMMAR, target_type="section", section_id=document.content[0].id),
    )

    # Another tab edits the document in the meantime.
    document.content[0].blocks[0].content[0].text = "Someone else rewrote this entirely."
    await DocumentRepository(test_db).update(document)

    with pytest.raises(EditConflict):
        await service.apply(proposal.id, user.id)


async def test_reject_proposal_does_not_change_document(test_db, user):
    document = build_document((1, "Body", ["the original text stays exactly as it is."]))
    await save_document(test_db, user.id, document)

    service = EditingService(test_db, provider=MockProvider())
    proposal = await service.propose(
        document.id,
        user.id,
        ProposeEditRequest(operation=EditOperation.FIX_GRAMMAR, target_type="section", section_id=document.content[0].id),
    )
    rejected = await service.reject(proposal.id, user.id)
    assert rejected.status == ProposalStatus.REJECTED

    stored = await DocumentRepository(test_db).get_by_id(document.id, user.id)
    assert stored.content[0].blocks[0].content[0].text == "the original text stays exactly as it is."


async def test_section_edit_preserves_tables(test_db, user):
    document = DocumentIR(
        title="With table",
        content=[
            Section(
                level=1,
                title="Data",
                blocks=[
                    Paragraph(content=[InlineContent(text="Prose that will be rewritten.")]),
                    Table(headers=["A", "B"], rows=[["1", "2"]]),
                ],
            )
        ],
        metadata=DocumentMetadata(document_type="general_report"),
    )
    await save_document(test_db, user.id, document)

    service = EditingService(test_db, provider=MockProvider())
    proposal = await service.propose(
        document.id,
        user.id,
        ProposeEditRequest(operation=EditOperation.IMPROVE_CLARITY, target_type="section", section_id=document.content[0].id),
    )
    updated, _ = await service.apply(proposal.id, user.id)
    types = [block.type for block in updated.content[0].blocks]
    assert "table" in types, "structured content must survive a prose rewrite"


async def test_targeted_block_edit_only_changes_that_block(test_db, user):
    document = build_document(
        (1, "Body", ["First paragraph stays.", "second paragraph gets fixed."])
    )
    await save_document(test_db, user.id, document)
    second = document.content[0].blocks[1].id

    service = EditingService(test_db, provider=MockProvider())
    proposal = await service.propose(
        document.id,
        user.id,
        ProposeEditRequest(operation=EditOperation.FIX_GRAMMAR, target_type="block", block_id=second),
    )
    updated, _ = await service.apply(proposal.id, user.id)
    assert updated.content[0].blocks[0].content[0].text == "First paragraph stays."
    assert updated.content[0].blocks[1].content[0].text == proposal.proposed_text


async def test_whole_document_rewrite_is_refused(test_db, user):
    document = build_document((1, "Body", ["Text."]))
    await save_document(test_db, user.id, document)
    service = EditingService(test_db, provider=MockProvider())
    with pytest.raises(ValueError):
        await service.propose(
            document.id,
            user.id,
            ProposeEditRequest(operation=EditOperation.SUMMARIZE, target_type="document"),
        )


async def test_transform_provider_failure_is_reported(test_db, user):
    document = build_document((1, "Body", ["Some text to rewrite."]))
    await save_document(test_db, user.id, document)
    service = EditingService(test_db, provider=FakeProvider(raise_on="transform"))
    with pytest.raises(ValueError):
        await service.propose(
            document.id,
            user.id,
            ProposeEditRequest(operation=EditOperation.SIMPLIFY, target_type="section", section_id=document.content[0].id),
        )


async def test_edit_marks_verification_for_recheck(test_db, user):
    document = build_document((1, "Body", ["the audit policy requires an independent review."]))
    await save_document(test_db, user.id, document)
    section_id = document.content[0].id
    verification = await VerificationRepository(test_db).upsert(
        ClaimVerification(
            user_id=user.id,
            document_id=document.id,
            claim_id="claim-1",
            claim_text="the audit policy requires an independent review.",
            section_id=section_id,
            status=VerificationStatus.SUPPORTED,
            explanation="Supported by the audit evidence.",
        )
    )

    service = EditingService(test_db, provider=MockProvider())
    proposal = await service.propose(
        document.id,
        user.id,
        ProposeEditRequest(operation=EditOperation.FIX_GRAMMAR, target_type="section", section_id=section_id),
    )
    await service.apply(proposal.id, user.id)

    refreshed = await VerificationRepository(test_db).get_by_id(verification.id, user.id)
    assert refreshed.status == VerificationStatus.NOT_CHECKED
    assert refreshed.manual_review is True
    assert refreshed.verification_method == "stale_after_ai_edit"


# ---------------------------------------------------------------------------
# 23-25: version history, comparison, restore
# ---------------------------------------------------------------------------

async def test_version_compare_reports_changes(test_db, user):
    document = build_document((1, "Body", ["Alpha text for the first version."]))
    await save_document(test_db, user.id, document)
    repo = DocumentRepository(test_db)
    await repo.create_version(document.id)

    document.content[0].blocks[0].content[0].text = "Beta text for the second version."
    await repo.update(document)
    await repo.create_version(document.id)

    comparison = await VersionService(test_db).compare(document.id, user.id, 1, 2)
    assert comparison.from_version == 1
    assert comparison.to_version == 2
    assert any("Alpha" in line for line in comparison.diff)
    assert any("Beta" in line for line in comparison.diff)
    assert comparison.changed_sections == ["Body"]


async def test_restore_preserves_history_and_is_undoable(test_db, user):
    document = build_document((1, "Body", ["Original text."]))
    await save_document(test_db, user.id, document)
    repo = DocumentRepository(test_db)
    await repo.create_version(document.id)          # v1 = original

    document.content[0].blocks[0].content[0].text = "Modified text."
    await repo.update(document)
    await repo.create_version(document.id)          # v2 = modified

    service = VersionService(test_db)
    restored = await service.restore(document.id, user.id, 1)
    assert restored.content[0].blocks[0].content[0].text == "Original text."

    # Restoring must add a snapshot of the pre-restore state, never delete one.
    versions = await service.list_versions(document.id, user.id)
    numbers = {v.version_number for v in versions}
    assert numbers == {1, 2, 3}
    assert any(v.origin == VersionOrigin.RESTORE for v in versions)

    # And the mutation before the restore is recoverable.
    back = await service.restore(document.id, user.id, 3)
    assert back.content[0].blocks[0].content[0].text == "Modified text."


async def test_restoring_unknown_version_raises(test_db, user):
    document = build_document((1, "Body", ["Text."]))
    await save_document(test_db, user.id, document)
    with pytest.raises(ValueError):
        await VersionService(test_db).restore(document.id, user.id, 99)


# ---------------------------------------------------------------------------
# 26-28: ownership isolation via the API
# ---------------------------------------------------------------------------

async def test_review_endpoints_enforce_ownership(
    test_db, user, other_user, api_client, api_client_factory
):
    document = build_document((1, "Body", [REPEATED, REPEATED]))
    await save_document(test_db, user.id, document)

    created = await api_client.post(
        f"/api/documents/{document.id}/reviews",
        json={"mode": "full"},
    )
    assert created.status_code == 201, created.text
    review_id = created.json()["session"]["id"]
    assert created.json()["summary"]["total"] >= 1

    # The other user cannot read it, review it, or touch its document.
    intruder = api_client_factory(other_user)
    assert (await intruder.get(f"/api/reviews/{review_id}")).status_code == 404
    assert (await intruder.post(f"/api/documents/{document.id}/reviews", json={"mode": "full"})).status_code == 404
    assert (await intruder.get(f"/api/documents/{document.id}/version-history")).status_code == 404


async def test_unauthenticated_review_is_rejected(test_db, user):
    """No dependency override -> the real cookie auth applies -> 401."""
    from httpx import ASGITransport, AsyncClient
    from main import app

    document = build_document((1, "Body", ["Text."]))
    await save_document(test_db, user.id, document)

    app.dependency_overrides.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/documents/{document.id}/reviews", json={"mode": "quick"})
    assert response.status_code == 401


async def test_missing_document_returns_404(api_client):
    response = await api_client.post("/api/documents/nope/reviews", json={"mode": "quick"})
    assert response.status_code == 404


async def test_finding_status_endpoint(test_db, user, api_client):
    document = build_document((1, "A", [REPEATED]), (1, "B", [REPEATED]))
    await save_document(test_db, user.id, document)
    created = await api_client.post(f"/api/documents/{document.id}/reviews", json={"mode": "full"})
    finding_id = created.json()["findings"][0]["id"]

    response = await api_client.patch(f"/api/findings/{finding_id}", json={"status": "accepted"})
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


# ---------------------------------------------------------------------------
# 29: text location behaviour
# ---------------------------------------------------------------------------

async def test_locate_is_whitespace_and_case_insensitive(test_db, user):
    document = build_document((1, "Body", ["The  Audit\nPolicy requires review."]))
    index = DocumentTextIndex(document)
    located = index.locate("the audit policy")
    assert located is not None
    assert located.start == 0
    assert located.text.strip()


async def test_locate_returns_none_for_absent_text(test_db, user):
    document = build_document((1, "Body", ["Some real text."]))
    assert DocumentTextIndex(document).locate("text that is not present") is None


async def test_fingerprint_changes_with_content(test_db, user):
    document = build_document((1, "Body", ["Original."]))
    before = DocumentTextIndex(document).fingerprint
    document.content[0].blocks[0].content[0].text = "Changed."
    after = DocumentTextIndex(document).fingerprint
    assert before != after
