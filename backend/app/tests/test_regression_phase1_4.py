"""Regression tests: Phases 1-4 must keep working after Phase 5.

These exercise the code paths Phase 5 touched (brief generation, retrieval,
knowledge search) plus the read-only endpoints most likely to break when routers
or dependencies change.
"""
from app.models.document_brief import OutlineItem
from app.models.knowledge import ContentChunk, KnowledgeFile
from app.models.research import EvidenceRecord, ResearchSession, ResearchSource, RetrievalStatus
from app.providers.mock_provider import MockProvider
from app.repositories.content_chunk_repository import ContentChunkRepository
from app.repositories.document_brief_repository import DocumentBriefRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.knowledge_file_repository import KnowledgeFileRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.research_source_repository import ResearchSourceRepository


async def seed_knowledge_base(db, user_id, text: str = "The annual audit policy requires review."):
    knowledge_file = KnowledgeFile(
        user_id=user_id,
        original_filename="policy.md",
        stored_filename="policy.md",
        file_extension="md",
        file_size_bytes=len(text),
        content_hash="hash-policy",
        storage_path="uploads/policy.md",
        extraction_status="completed",
    )
    await KnowledgeFileRepository(db).create(knowledge_file)
    await ContentChunkRepository(db).create(
        ContentChunk(
            file_id=knowledge_file.id,
            user_id=user_id,
            chunk_index=0,
            chunk_text=text,
            chunk_size=len(text),
        )
    )
    return knowledge_file


async def seed_brief(db, user_id, *, approved: bool = True):
    repo = DocumentBriefRepository(db)
    brief = await repo.create(
        {
            "document_type": "general_report",
            "title": "Audit report",
            "topic": "Annual audit policy",
            "audience": "Board",
            "language": "en",
            "tone": "formal",
        },
        user_id=user_id,
    )
    await repo.update(
        brief.id,
        user_id,
        {
            "outline": [OutlineItem(level=1, title="Findings")],
            "outline_approved": approved,
        },
    )
    # Refresh the in-memory object: after repo.update() the in-memory row can be
    # stale, and the route looks it up through the shared Database.
    return await repo.get_by_id(brief.id, user_id)


async def test_health_endpoint(api_client):
    response = await api_client.get("/health")
    assert response.status_code == 200


async def test_current_user_endpoint(api_client, user):
    response = await api_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == user.email


async def test_list_documents_and_briefs(api_client):
    assert (await api_client.get("/api/documents")).status_code == 200
    assert (await api_client.get("/api/document-briefs")).status_code == 200
    assert (await api_client.get("/api/conversations")).status_code == 200
    assert (await api_client.get("/api/knowledge/files")).status_code == 200


async def test_knowledge_search_handles_punctuation(api_client, test_db, user):
    """FTS5 raises on raw punctuation; the query must be sanitized."""
    await seed_knowledge_base(test_db, user.id)

    for query in ["audit", "What's the annual audit policy?", "policy-review?"]:
        response = await api_client.get("/api/knowledge/search", params={"q": query})
        assert response.status_code == 200, response.text
        assert response.json()["total"] >= 1


async def test_brief_generation_without_research_still_works(api_client, test_db, user, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.document_briefs.get_provider", lambda: MockProvider()
    )
    brief = await seed_brief(test_db, user.id)

    response = await api_client.post(f"/api/document-briefs/{brief.id}/generate")
    assert response.status_code == 200, response.text
    document = response.json()
    assert document["content"]
    assert document["metadata"]["custom_fields"]["brief_id"] == brief.id

    # No research session, so no citations are created.
    citations = await api_client.get(f"/api/documents/{document['id']}/citations")
    assert citations.json()["entries"] == []


async def test_brief_generation_requires_approved_outline(api_client, test_db, user, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.document_briefs.get_provider", lambda: MockProvider()
    )
    brief = await seed_brief(test_db, user.id, approved=False)
    response = await api_client.post(f"/api/document-briefs/{brief.id}/generate")
    assert response.status_code == 400


async def test_brief_generation_with_research_creates_citations(
    api_client, test_db, user, monkeypatch
):
    monkeypatch.setattr(
        "app.api.routes.document_briefs.get_provider", lambda: MockProvider()
    )
    brief = await seed_brief(test_db, user.id)

    session = await ResearchRepository(test_db).create_session(
        ResearchSession(user_id=user.id, brief_id=brief.id, title="Audit research")
    )
    source = await ResearchSourceRepository(test_db).create(
        ResearchSource(
            session_id=session.id,
            user_id=user.id,
            retrieval_status=RetrievalStatus.FETCHED,
            title="Annual audit policy review",
            url="https://example.org/report",
            author="Jane Doe",
            publisher="World Institute",
            published_date="2023-03-05",
            content_text="The annual audit policy requires an independent review every year.",
            selected=True,
        )
    )
    await EvidenceRepository(test_db).create(
        EvidenceRecord(
            session_id=session.id,
            source_id=source.id,
            user_id=user.id,
            claim_or_finding="The policy requires an independent review.",
            passage="The annual audit policy requires an independent review every year.",
        )
    )

    response = await api_client.post(
        f"/api/document-briefs/{brief.id}/generate",
        json={"research_session_id": session.id, "citation_style": "apa", "use_research": True},
    )
    assert response.status_code == 200, response.text
    document = response.json()
    assert document["metadata"]["custom_fields"]["research_session_id"] == session.id
    assert document["metadata"]["custom_fields"]["citations_created"] >= 1

    citations = await api_client.get(f"/api/documents/{document['id']}/citations")
    body = citations.json()
    assert len(body["entries"]) == 1
    assert "Doe" in body["entries"][0]["text"]


async def test_document_export_still_works(api_client, test_db, user, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.document_briefs.get_provider", lambda: MockProvider()
    )
    brief = await seed_brief(test_db, user.id)
    created = await api_client.post(f"/api/document-briefs/{brief.id}/generate")
    document_id = created.json()["id"]

    response = await api_client.post(f"/api/documents/{document_id}/export?format=markdown")
    assert response.status_code == 200
    assert len(response.content) > 0


async def test_research_session_with_unknown_brief_is_rejected(api_client):
    response = await api_client.post(
        "/api/research/sessions", json={"title": "x", "brief_id": "missing"}
    )
    assert response.status_code == 404
