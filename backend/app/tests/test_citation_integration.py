"""Marker -> citation -> reference-list integration tests."""
import pytest

from app.models.research import (
    CitationStyle,
    EvidenceRecord,
    ResearchSession,
    ResearchSource,
    RetrievalStatus,
)
from app.repositories.citation_repository import CitationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.services.citation_service import CitationService, document_text


async def build_source_and_evidence(db, user_id, *, title="Climate report", **source_overrides):
    session = await ResearchRepository(db).create_session(
        ResearchSession(user_id=user_id, title="Citations session")
    )
    defaults = dict(
        session_id=session.id,
        user_id=user_id,
        retrieval_status=RetrievalStatus.FETCHED,
        title=title,
        url="https://example.org/report",
        author="Jane Doe",
        publisher="World Institute",
        published_date="2023-03-05",
        content_text="The report confirms the annual audit was completed independently.",
        selected=True,
    )
    defaults.update(source_overrides)
    source = await ResearchSourceRepository(db).create(ResearchSource(**defaults))
    evidence = await EvidenceRepository(db).create(
        EvidenceRecord(
            session_id=session.id,
            source_id=source.id,
            user_id=user_id,
            claim_or_finding="The annual audit was completed independently.",
            passage="The report confirms the annual audit was completed independently.",
        )
    )
    return session, source, evidence


async def save_document(db, user_id, document):
    return await DocumentRepository(db).create(document, user_id=user_id)


async def test_markers_become_source_linked_citations(db, user, document_factory):
    session, source, evidence = await build_source_and_evidence(db, user.id)
    document = document_factory(
        paragraphs=["The audit was completed independently [E1]."]
    )
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    result = await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style=CitationStyle.APA
    )

    assert result.markers_replaced == 1
    assert result.citations_created == 1
    assert "(Doe, 2023)" in document.content[0].blocks[0].content[0].text
    assert "[E1]" not in document_text(document)

    citations = await CitationRepository(db).list_for_document(document.id, user.id)
    assert len(citations) == 1
    assert citations[0].source_id == source.id
    assert citations[0].evidence_id == evidence.id
    assert citations[0].in_text == "(Doe, 2023)"


async def test_unknown_markers_are_removed_not_invented(db, user, document_factory):
    session, source, evidence = await build_source_and_evidence(db, user.id)
    document = document_factory(paragraphs=["A real claim [E1] and a fake one [E9]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    result = await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style=CitationStyle.APA
    )

    text = document_text(document)
    assert result.markers_removed == 1
    assert "[E9]" not in text
    assert "[E1]" not in text


async def test_markers_are_stripped_when_no_evidence_exists(db, user, document_factory):
    document = document_factory(paragraphs=["A claim with a fabricated marker [E1]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    result = await service.apply_evidence_markers(document, document.id, user.id, [], style="apa")

    assert result.markers_removed == 1
    assert "[E1]" not in document_text(document)


async def test_reference_list_is_rendered_and_checked(db, user, document_factory):
    session, source, evidence = await build_source_and_evidence(db, user.id)
    document = document_factory(paragraphs=["The audit was completed independently [E1]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style="apa"
    )
    await DocumentRepository(db).update(document)

    response = await service.reference_list(document.id, user.id, "apa", session_id=session.id)
    assert len(response.entries) == 1
    assert response.entries[0].text.startswith("Doe, J. (2023, March 5). Climate report.")
    assert response.issues == []
    assert response.uncited_source_ids == []


async def test_missing_metadata_is_reported(db, user, document_factory):
    session, source, evidence = await build_source_and_evidence(
        db,
        user.id,
        title="Anonymous memo",
        author=None,
        publisher=None,
        published_date=None,
        url=None,
    )
    document = document_factory(paragraphs=["A statement [E1]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style="apa"
    )

    response = await service.reference_list(document.id, user.id, "apa")
    codes = {issue.code for issue in response.issues}
    assert "missing_metadata" in codes
    # The entry is rendered with an explicit placeholder rather than a fake date.
    assert "(n.d.)" in response.entries[0].text


async def test_uncited_selected_source_is_reported(db, user, document_factory):
    session, source, evidence = await build_source_and_evidence(db, user.id, title="Cited source")
    extra = await ResearchSourceRepository(db).create(
        ResearchSource(
            session_id=session.id,
            user_id=user.id,
            retrieval_status=RetrievalStatus.FETCHED,
            title="Never cited source",
            url="https://example.org/other",
            content_text="Unused.",
            selected=True,
        )
    )

    document = document_factory(paragraphs=["Cited claim [E1]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style="apa"
    )
    response = await service.reference_list(document.id, user.id, "apa", session_id=session.id)

    assert extra.id in response.uncited_source_ids
    assert any(issue.code == "source_not_cited" for issue in response.issues)


async def test_leftover_marker_is_reported_as_broken_reference(db, user, document_factory):
    session, source, evidence = await build_source_and_evidence(db, user.id)
    document = document_factory(paragraphs=["The audit was completed independently [E1]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style="apa"
    )
    # Simulate a hand edit that reintroduced a raw marker.
    document.content[0].blocks[0].content[0].text += " Extra [E4]."
    await DocumentRepository(db).update(document)

    response = await service.reference_list(document.id, user.id, "apa")
    assert any(issue.code == "broken_reference" for issue in response.issues)


async def test_restyle_rewrites_in_text_citations(db, user, document_factory):
    session, source, evidence = await build_source_and_evidence(db, user.id)
    document = document_factory(paragraphs=["The audit was completed independently [E1]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style="apa"
    )
    await DocumentRepository(db).update(document)

    response = await service.restyle(document.id, user.id, "ieee")
    assert response.style == CitationStyle.IEEE
    assert response.entries[0].text.startswith("[1]")

    reloaded = await DocumentRepository(db).get_by_id(document.id, user.id)
    assert "[1]" in document_text(reloaded)
    assert "(Doe, 2023)" not in document_text(reloaded)


async def test_deleting_a_citation_keeps_the_source(db, user, document_factory):
    session, source, evidence = await build_source_and_evidence(db, user.id)
    document = document_factory(paragraphs=["The audit was completed independently [E1]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style="apa"
    )
    citations = await CitationRepository(db).list_for_document(document.id, user.id)

    deleted = await CitationRepository(db).delete(citations[0].id, user.id)
    assert deleted is True
    assert await CitationRepository(db).list_for_document(document.id, user.id) == []
    assert await ResearchSourceRepository(db).get_by_id(source.id, user.id) is not None


async def test_citation_ownership_is_enforced(db, user, other_user, document_factory):
    session, source, evidence = await build_source_and_evidence(db, user.id)
    document = document_factory(paragraphs=["The audit was completed independently [E1]."])
    document = await save_document(db, user.id, document)

    service = CitationService(db)
    await service.apply_evidence_markers(
        document, document.id, user.id, [(evidence, source)], style="apa"
    )

    # Another user cannot read the reference list of this document.
    with pytest.raises(ValueError):
        await service.reference_list(document.id, other_user.id, "apa")
