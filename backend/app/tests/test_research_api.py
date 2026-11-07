"""API-level tests for the Phase 5 routes.

Authentication and the database are overridden by fixtures, so these exercise
routing, validation, ownership and rate limiting without touching the real app
database or the network.
"""
import pytest

from app.core.config import get_settings
from app.models.document_ir import (
    DocumentIR,
    DocumentMetadata,
    InlineContent,
    Paragraph,
    Section,
)
from app.repositories.document_repository import DocumentRepository


@pytest.fixture(autouse=True)
def _stub_ai_provider(monkeypatch):
    """Never call Groq from tests, even if .env configures it."""

    class NoAssessor:
        async def assess_claim(self, claim, passages):
            return None

    monkeypatch.setattr(
        "app.services.verification_service.get_provider", lambda: NoAssessor()
    )


async def test_provider_status_endpoint(api_client):
    response = await api_client.get("/api/research/providers")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"]["name"] in {"none", "tavily", "searxng"}
    assert "apa" in body["supported_styles"]
    assert body["limits"]["max_sources"] > 0

    # Secrets must never leak through this endpoint: the configured key values
    # themselves must not appear anywhere in the payload.
    settings = get_settings()
    for secret in (settings.TAVILY_API_KEY, settings.GROQ_API_KEY, settings.OPENAI_API_KEY):
        if secret:
            assert secret not in response.text


async def test_status_labels_endpoint(api_client):
    response = await api_client.get("/api/research/status-labels")
    assert response.status_code == 200
    labels = {item["value"]: item["label"] for item in response.json()["statuses"]}
    assert labels["insufficient_evidence"] == "Insufficient Evidence"
    assert labels["not_checked"] == "Not Checked"


async def test_create_session_requires_a_title(api_client):
    response = await api_client.post("/api/research/sessions", json={})
    assert response.status_code == 400


async def test_create_and_fetch_session(api_client):
    created = await api_client.post(
        "/api/research/sessions",
        json={"title": "Quarterly research", "include_knowledge_base": True},
    )
    assert created.status_code == 201
    body = created.json()
    session_id = body["session"]["id"]
    assert body["session"]["status"] == "draft"
    assert body["questions"] == []

    fetched = await api_client.get(f"/api/research/sessions/{session_id}")
    assert fetched.status_code == 200
    assert fetched.json()["session"]["title"] == "Quarterly research"

    listing = await api_client.get("/api/research/sessions")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


async def test_rejects_private_url_at_input_time(api_client):
    response = await api_client.post(
        "/api/research/sessions",
        json={"title": "Unsafe", "urls": ["http://127.0.0.1:8000/api/auth/me"]},
    )
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]


async def test_plan_and_replace_questions(api_client):
    created = await api_client.post(
        "/api/research/sessions", json={"title": "Audit research"}
    )
    session_id = created.json()["session"]["id"]

    planned = await api_client.post(f"/api/research/sessions/{session_id}/plan")
    assert planned.status_code == 200
    questions = planned.json()["questions"]
    assert questions and "Audit research" in questions[0]["question"]

    replaced = await api_client.put(
        f"/api/research/sessions/{session_id}/questions",
        json={"questions": [{"question": "What does the audit cover?"}]},
    )
    assert replaced.status_code == 200
    assert len(replaced.json()["questions"]) == 1

    detail = await api_client.get(f"/api/research/sessions/{session_id}")
    assert len(detail.json()["questions"]) == 1


async def test_replace_questions_requires_at_least_one(api_client):
    created = await api_client.post("/api/research/sessions", json={"title": "Empty"})
    session_id = created.json()["session"]["id"]
    response = await api_client.put(
        f"/api/research/sessions/{session_id}/questions", json={"questions": []}
    )
    assert response.status_code == 400


async def test_run_wait_completes_without_external_provider(api_client):
    created = await api_client.post(
        "/api/research/sessions",
        json={"title": "Offline research", "external_research": False},
    )
    session_id = created.json()["session"]["id"]

    started = await api_client.post(
        f"/api/research/sessions/{session_id}/run?wait=true"
    )
    assert started.status_code == 202
    body = started.json()
    assert body["status"] in {"completed", "partial", "failed"}

    detail = await api_client.get(f"/api/research/sessions/{session_id}")
    assert detail.json()["session"]["status"] != "running"
    assert detail.json()["session"]["completed_at"] is not None


async def test_sources_and_evidence_endpoints_return_empty_lists(api_client):
    created = await api_client.post("/api/research/sessions", json={"title": "Nothing yet"})
    session_id = created.json()["session"]["id"]

    sources = await api_client.get(f"/api/research/sessions/{session_id}/sources")
    evidence = await api_client.get(f"/api/research/sessions/{session_id}/evidence")
    assert sources.json()["total"] == 0
    assert evidence.json()["total"] == 0


async def test_other_users_session_is_not_found(api_client_factory, user, other_user, test_db):
    from app.models.research import ResearchSession
    from app.repositories.research_repository import ResearchRepository

    session = await ResearchRepository(test_db).create_session(
        ResearchSession(user_id=user.id, title="Private")
    )

    intruder_client = api_client_factory(other_user)
    response = await intruder_client.get(f"/api/research/sessions/{session.id}")
    assert response.status_code == 404

    listing = await intruder_client.get("/api/research/sessions")
    assert listing.json()["total"] == 0

    owner_client = api_client_factory(user)
    assert (await owner_client.get(f"/api/research/sessions/{session.id}")).status_code == 200


async def test_unknown_session_returns_404(api_client):
    response = await api_client.get("/api/research/sessions/does-not-exist")
    assert response.status_code == 404


async def test_delete_session_removes_it(api_client):
    created = await api_client.post("/api/research/sessions", json={"title": "Temp"})
    session_id = created.json()["session"]["id"]
    deleted = await api_client.delete(f"/api/research/sessions/{session_id}")
    assert deleted.status_code == 204
    assert (await api_client.get(f"/api/research/sessions/{session_id}")).status_code == 404


async def test_document_citation_and_verification_endpoints(api_client, user, test_db):
    document = DocumentIR(
        title="Verification target",
        content=[
            Section(
                level=1,
                title="Findings",
                blocks=[
                    Paragraph(
                        content=[
                            InlineContent(
                                text="The report was published by the World Institute in March 2023."
                            )
                        ]
                    )
                ],
            )
        ],
        metadata=DocumentMetadata(document_type="general_report"),
    )
    await DocumentRepository(test_db).create(document, user_id=user.id)

    citations = await api_client.get(f"/api/documents/{document.id}/citations")
    assert citations.status_code == 200
    assert citations.json()["entries"] == []

    verified = await api_client.post(f"/api/documents/{document.id}/verify", json={})
    assert verified.status_code == 200
    body = verified.json()
    assert body["summary"]["total"] >= 1
    # With no evidence and no assessor, nothing may be claimed as supported.
    assert body["summary"]["supported"] == 0

    report = await api_client.get(
        f"/api/documents/{document.id}/verifications?status=insufficient_evidence"
    )
    assert report.status_code == 200

    bad_filter = await api_client.get(
        f"/api/documents/{document.id}/verifications?status=made_up"
    )
    assert bad_filter.status_code == 400


async def test_verification_endpoint_requires_document_ownership(
    api_client_factory, user, other_user, test_db
):
    document = DocumentIR(
        title="Owned by user",
        content=[Section(level=1, title="One", blocks=[])],
        metadata=DocumentMetadata(document_type="general_report"),
    )
    await DocumentRepository(test_db).create(document, user_id=user.id)

    intruder = api_client_factory(other_user)
    response = await intruder.post(f"/api/documents/{document.id}/verify", json={})
    assert response.status_code == 404


async def test_research_run_is_rate_limited(api_client):
    created = await api_client.post(
        "/api/research/sessions",
        json={"title": "Rate limited", "external_research": False},
    )
    session_id = created.json()["session"]["id"]

    statuses = []
    for _ in range(11):
        response = await api_client.post(
            f"/api/research/sessions/{session_id}/run?wait=true"
        )
        statuses.append(response.status_code)

    assert statuses[:10] == [202] * 10
    assert statuses[10] == 429
