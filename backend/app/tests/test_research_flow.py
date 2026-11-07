"""Research pipeline tests: planning, discovery, extraction, evidence, failures.

All network access is replaced with fakes, so these tests are deterministic and
offline. They assert the *honesty* properties too: a failing provider must not
produce sources, and unsafe URLs must never be fetched.
"""
import pytest

from app.core.config import Settings
from app.models.knowledge import ContentChunk, KnowledgeFile
from app.models.research import (
    ResearchSession,
    ResearchStatus,
    RetrievalStatus,
    SourceType,
)
from app.providers.research import (
    ResearchProvider,
    ResearchProviderError,
    SearchCandidate,
)
from app.repositories.content_chunk_repository import ContentChunkRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.knowledge_file_repository import KnowledgeFileRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.services.html_extraction import extract_readable
from app.services.research_service import (
    ResearchService,
    derive_research_questions,
    lexical_overlap,
)
from app.services.source_fetcher import FetchResult

PUBLIC_URL = "https://93.184.216.34/report"

ARTICLE_HTML = """
<html><head>
  <title>Annual audit policy review</title>
  <meta name="author" content="Jane Doe">
  <meta property="article:published_time" content="2023-03-05">
  <meta property="og:site_name" content="World Institute">
</head><body><article>
  <p>The annual audit policy requires every system to be reviewed by an independent
  auditor each year. The policy also defines escalation paths for unresolved findings
  and requires the results to be published to the board within thirty days.</p>
  <p>Independent auditors reviewed the annual audit policy in 2023 and confirmed that
  the established facts about the policy match the published procedure.</p>
</article></body></html>
"""


class FakeProvider(ResearchProvider):
    name = "fake"
    display_name = "Fake search"

    def __init__(self, candidates=None, error=None):
        self.candidates = candidates or []
        self.error = error
        self.queries = []

    async def health(self):
        return True, "fake provider ready"

    async def search(self, query, limit):
        self.queries.append(query)
        if self.error:
            raise self.error
        return self.candidates[:limit]


def make_fetcher(result: FetchResult):
    async def _fetch(url, **kwargs):
        return result

    return _fetch


def fetched_page(url: str = PUBLIC_URL) -> FetchResult:
    page = extract_readable(ARTICLE_HTML, url)
    return FetchResult(
        url=url,
        status=RetrievalStatus.FETCHED,
        final_url=url,
        http_status=200,
        content_type="text/html",
        text=page.text,
        page=page,
    )


def local_settings() -> Settings:
    return Settings(
        RESEARCH_MAX_QUESTIONS=3,
        RESEARCH_RESULTS_PER_QUESTION=3,
        RESEARCH_MAX_SOURCES=5,
        RESEARCH_MIN_PASSAGE_CHARS=80,
        RESEARCH_FETCH_TIMEOUT_SECONDS=2,
    )


async def make_session(db, user_id, **overrides) -> ResearchSession:
    session = ResearchSession(
        user_id=user_id,
        title=overrides.pop("title", "Annual audit policy"),
        **overrides,
    )
    return await ResearchRepository(db).create_session(session)


def test_derive_questions_is_deterministic_and_deduplicated():
    first = derive_research_questions(None, title="Annual audit policy", max_questions=5)
    second = derive_research_questions(None, title="Annual audit policy", max_questions=5)
    assert first == second
    assert len(first) <= 5
    questions = [item["question"] for item in first]
    assert len(questions) == len(set(questions))
    assert all("Annual audit policy" in question for question in questions)


def test_lexical_overlap_scores_relevance():
    assert lexical_overlap("annual audit policy", "the annual audit policy is required") > 0.9
    assert lexical_overlap("annual audit policy", "completely unrelated cooking recipe") == 0.0


async def test_run_collects_sources_and_evidence(db, user):
    provider = FakeProvider(
        candidates=[
            SearchCandidate(
                title="Annual audit policy review",
                url=PUBLIC_URL,
                snippet="The annual audit policy requires independent review.",
            )
        ]
    )
    session = await make_session(db, user.id, external_research=True, include_knowledge_base=False)

    service = ResearchService(
        db, provider=provider, fetcher=make_fetcher(fetched_page()), settings=local_settings()
    )
    await service.plan_questions(session, None)
    outcome = await service.run(session.id, user.id)

    assert outcome.status == ResearchStatus.COMPLETED
    sources = await ResearchSourceRepository(db).list_by_session(session.id, user.id)
    assert len(sources) == 1
    assert sources[0].retrieval_status == RetrievalStatus.FETCHED
    assert sources[0].source_type == SourceType.WEB
    assert sources[0].author == "Jane Doe"
    assert sources[0].published_date == "2023-03-05"

    evidence = await EvidenceRepository(db).list_by_session(session.id, user.id)
    assert evidence, "expected at least one evidence passage"
    assert all(item.passage for item in evidence)
    assert all(item.source_id == sources[0].id for item in evidence)

    refreshed = await ResearchRepository(db).get_session(session.id, user.id)
    assert refreshed.status == ResearchStatus.COMPLETED
    assert refreshed.completed_at is not None


async def test_provider_failure_creates_no_sources(db, user):
    provider = FakeProvider(error=ResearchProviderError("search backend down"))
    session = await make_session(db, user.id, external_research=True, include_knowledge_base=False)

    service = ResearchService(
        db, provider=provider, fetcher=make_fetcher(fetched_page()), settings=local_settings()
    )
    await service.plan_questions(session, None)
    outcome = await service.run(session.id, user.id)

    assert outcome.status == ResearchStatus.FAILED
    assert outcome.failures
    sources = await ResearchSourceRepository(db).list_by_session(session.id, user.id)
    assert sources == []
    refreshed = await ResearchRepository(db).get_session(session.id, user.id)
    assert refreshed.error


async def test_blocked_fetch_is_recorded_not_hidden(db, user):
    provider = FakeProvider(
        candidates=[SearchCandidate(title="Blocked page", url=PUBLIC_URL)]
    )
    blocked = FetchResult(
        url=PUBLIC_URL,
        status=RetrievalStatus.BLOCKED,
        error="URL resolves to a non-public address",
    )
    session = await make_session(db, user.id, external_research=True, include_knowledge_base=False)

    service = ResearchService(
        db, provider=provider, fetcher=make_fetcher(blocked), settings=local_settings()
    )
    await service.plan_questions(session, None)
    outcome = await service.run(session.id, user.id)

    sources = await ResearchSourceRepository(db).list_by_session(session.id, user.id)
    assert len(sources) == 1
    assert sources[0].retrieval_status == RetrievalStatus.BLOCKED
    assert "non-public" in (sources[0].error or "")
    assert outcome.status == ResearchStatus.FAILED


async def test_unsafe_user_url_is_rejected_before_fetch(db, user):
    session = await make_session(
        db,
        user.id,
        include_knowledge_base=False,
        requested_urls=["http://127.0.0.1/secret"],
    )

    called = {"count": 0}

    async def _fetch(url, **kwargs):
        called["count"] += 1
        return fetched_page(url)

    service = ResearchService(
        db, provider=FakeProvider(), fetcher=_fetch, settings=local_settings()
    )
    await service.plan_questions(session, None)
    outcome = await service.run(session.id, user.id)

    assert called["count"] == 0
    assert any("rejected" in failure.lower() for failure in outcome.failures)
    sources = await ResearchSourceRepository(db).list_by_session(session.id, user.id)
    assert sources == []


async def test_knowledge_base_sources_are_reused_and_deduplicated(db, user):
    file_repo = KnowledgeFileRepository(db)
    chunk_repo = ContentChunkRepository(db)

    knowledge_file = KnowledgeFile(
        user_id=user.id,
        original_filename="audit-policy.md",
        stored_filename="stored.md",
        file_extension="md",
        file_size_bytes=120,
        content_hash="hash-1",
        storage_path="uploads/hash-1.md",
        extraction_status="completed",
    )
    await file_repo.create(knowledge_file)
    await chunk_repo.create(
        ContentChunk(
            file_id=knowledge_file.id,
            user_id=user.id,
            chunk_index=0,
            chunk_text=(
                "The annual audit policy requires an independent review of every system "
                "and defines the established facts that must be reported to the board."
            ),
            chunk_size=140,
        )
    )

    session = await make_session(db, user.id, include_knowledge_base=True)
    service = ResearchService(
        db, provider=FakeProvider(), fetcher=make_fetcher(fetched_page()), settings=local_settings()
    )
    await service.plan_questions(session, None)

    first = await service.run(session.id, user.id)
    assert first.status == ResearchStatus.COMPLETED
    sources = await ResearchSourceRepository(db).list_by_session(session.id, user.id)
    assert len(sources) == 1
    assert sources[0].source_type == SourceType.KNOWLEDGE_BASE
    assert sources[0].knowledge_file_id == knowledge_file.id

    evidence_after_first = await EvidenceRepository(db).count_for_session(session.id, user.id)
    assert evidence_after_first >= 1

    second = await service.run(session.id, user.id)
    assert second.status == ResearchStatus.COMPLETED
    sources_after = await ResearchSourceRepository(db).list_by_session(session.id, user.id)
    evidence_after_second = await EvidenceRepository(db).count_for_session(session.id, user.id)

    assert len(sources_after) == 1, "re-running must not duplicate sources"
    assert evidence_after_second == evidence_after_first, "re-running must not duplicate evidence"


async def test_session_is_not_visible_to_another_user(db, user, other_user):
    session = await make_session(db, user.id)
    repo = ResearchRepository(db)
    assert await repo.get_session(session.id, other_user.id) is None
    assert await repo.get_session(session.id, user.id) is not None
