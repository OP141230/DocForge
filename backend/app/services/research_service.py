"""Research orchestration: plan -> discover -> extract -> evaluate -> evidence.

Pipeline
--------
1. **Plan** - derive research questions from the DocumentBrief and its approved
   outline (deterministic, editable by the user before any network call).
2. **Discover** - three independent source channels:
   * Phase 4 knowledge base (reuses ``RetrievalService``/FTS5),
   * URLs the user supplied,
   * the configured external search provider (optional).
3. **Extract** - fetch pages through :func:`app.services.source_fetcher.fetch_url`
   (SSRF guarded, size limited) and pull readable text + passages.
4. **Evaluate** - attach factual notes (domain type, missing date, length) and a
   lexical relevance score. No opaque "credibility score" is invented.
5. **Evidence** - store the passages that actually support a research question as
   :class:`~app.models.research.EvidenceRecord` rows, de-duplicated per source.

Failure policy: one broken source never fails a run. The session ends
``completed``, ``partial`` (some failures) or ``failed`` (nothing usable), and the
errors are recorded so the UI can show them.
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.url_validation import UnsafeUrlError, normalize_url, validate_url_syntax
from app.models.document_brief import DocumentBrief
from app.models.research import (
    EvidenceRecord,
    EvidenceType,
    ResearchQuestion,
    ResearchSession,
    ResearchSource,
    ResearchStatus,
    RetrievalStatus,
    SourceType,
)
from app.providers.research import (
    ResearchNotConfigured,
    ResearchProvider,
    ResearchProviderError,
    ResearchTimeout,
    SearchCandidate,
    get_research_provider,
)
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.services.html_extraction import build_passages
from app.services.retrieval_service import RetrievalService
from app.services.source_fetcher import FetchResult, fetch_url

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "had", "not", "but", "you", "your", "our", "its", "their",
    "what", "which", "who", "how", "why", "when", "where", "into", "than",
    "about", "also", "can", "will", "would", "should", "could", "does", "did",
    "they", "them", "there", "here", "such", "more", "most", "some", "any",
}

MAX_EVIDENCE_PER_SOURCE = 2
EVIDENCE_MIN_SCORE = 0.08


def tokens(text: str) -> set[str]:
    """Tokenize for lexical relevance (lowercase, stopwords removed)."""
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9'-]{2,}", (text or "").lower())
        if token not in STOPWORDS
    }


def lexical_overlap(a: str, b: str) -> float:
    """Share of ``a``'s content words present in ``b`` (0..1)."""
    left = tokens(a)
    if not left:
        return 0.0
    return len(left & tokens(b)) / len(left)


@dataclass
class RunOutcome:
    """Summary of one research run."""

    status: ResearchStatus
    sources_created: int = 0
    evidence_created: int = 0
    failures: List[str] = field(default_factory=list)
    provider_message: Optional[str] = None


def derive_research_questions(
    brief: Optional[DocumentBrief],
    *,
    title: str,
    topic: Optional[str] = None,
    max_questions: int = 6,
) -> List[Dict[str, Optional[str]]]:
    """Build a deterministic starting set of research questions.

    Deterministic by design: it is free, reproducible, and the user can edit the
    questions before research runs. An LLM could produce "nicer" questions, but
    it would also add cost and a failure mode for no factual benefit.
    """
    subject = (topic or (brief.topic if brief else None) or title).strip()
    questions: List[Dict[str, Optional[str]]] = []

    def add(question: str, rationale: Optional[str]) -> None:
        normalized = " ".join(question.lower().split())
        if any(" ".join((q["question"] or "").lower().split()) == normalized for q in questions):
            return
        questions.append({"question": question, "rationale": rationale})

    add(
        f"What are the key established facts about {subject}?",
        "Baseline facts that the document is likely to assert.",
    )
    add(
        f"What do authoritative sources say about the current state of {subject}?",
        "Establishes recency and the mainstream position.",
    )

    if brief:
        for point in brief.important_points[:3]:
            add(
                f"What evidence supports or challenges this point: {point}?",
                "Directly tied to an important point in the brief.",
            )
        for item in (brief.outline or [])[:4]:
            if item.level <= 2:
                add(
                    f"What sources cover '{item.title}' in the context of {subject}?",
                    "Maps evidence to an approved outline section.",
                )
        if brief.audience:
            add(
                f"What background does a {brief.audience} audience need about {subject}?",
                "Keeps the evidence appropriate to the intended reader.",
            )

    return questions[:max_questions]


class ResearchService:
    """Executes research runs for a session."""

    def __init__(
        self,
        db: Database,
        *,
        provider: Optional[ResearchProvider] = None,
        fetcher: Optional[Callable[..., Any]] = None,
        settings: Optional[Settings] = None,
    ):
        self.db = db
        self.settings = settings or get_settings()
        self.provider = provider or get_research_provider(self.settings)
        self.fetch = fetcher or fetch_url
        self.sessions = ResearchRepository(db)
        self.sources = ResearchSourceRepository(db)
        self.evidence = EvidenceRepository(db)
        self.retrieval = RetrievalService(db)

    # -- planning ---------------------------------------------------------
    async def plan_questions(self, session: ResearchSession, brief: Optional[DocumentBrief]) -> List[ResearchQuestion]:
        """(Re)generate research questions from the brief or session title."""
        derived = derive_research_questions(
            brief,
            title=session.title,
            max_questions=self.settings.RESEARCH_MAX_QUESTIONS,
        )
        return await self.sessions.replace_questions(
            session.id, session.user_id, derived
        )

    # -- running ----------------------------------------------------------
    async def run(self, session_id: str, user_id: str) -> RunOutcome:
        """Execute the full research pipeline for a session."""
        session = await self.sessions.get_session(session_id, user_id)
        if not session:
            raise ValueError("Research session not found")

        if session.status == ResearchStatus.RUNNING:
            return RunOutcome(
                status=ResearchStatus.RUNNING,
                failures=["A research run is already in progress."],
            )

        await self.sessions.update_session(
            session_id,
            user_id,
            {
                "status": ResearchStatus.RUNNING,
                "started_at": datetime.utcnow(),
                "error": None,
                "progress_message": "Preparing research questions",
            },
        )

        outcome = RunOutcome(status=ResearchStatus.RUNNING)

        try:
            questions = await self.sessions.list_questions(session_id, user_id)
            if not questions:
                brief = await self._load_brief(session)
                questions = await self.plan_questions(session, brief)

            if not questions:
                outcome.status = ResearchStatus.FAILED
                outcome.failures.append("No research questions could be derived.")
                await self._finish(session, outcome)
                return outcome

            await self.sessions.update_session(
                session_id, user_id, {"progress_message": "Searching sources"}
            )

            discovered, discovery_failures = await self._discover(
                session, questions, outcome
            )
            outcome.failures.extend(discovery_failures)

            await self.sessions.update_session(
                session_id, user_id, {"progress_message": "Reading sources"}
            )
            fetched, fetch_failures = await self._read_sources(
                session, discovered, outcome
            )
            outcome.failures.extend(fetch_failures)

            await self.sessions.update_session(
                session_id, user_id, {"progress_message": "Extracting evidence"}
            )
            await self._build_evidence(session, questions, fetched, outcome)

            usable = [source for source in fetched if source.retrieval_status == RetrievalStatus.FETCHED]
            if not usable and outcome.failures:
                outcome.status = ResearchStatus.FAILED
            elif outcome.failures:
                outcome.status = ResearchStatus.PARTIAL
            else:
                outcome.status = ResearchStatus.COMPLETED

            await self._finish(session, outcome)
            return outcome

        except asyncio.CancelledError:
            await self.sessions.update_session(
                session_id,
                user_id,
                {
                    "status": ResearchStatus.FAILED,
                    "error": "Research run was cancelled.",
                    "completed_at": datetime.utcnow(),
                },
            )
            raise
        except Exception as exc:  # never leak a traceback to the client
            logger.exception("Research run failed for session %s", session_id)
            outcome.status = ResearchStatus.FAILED
            outcome.failures.append(f"Unexpected error: {type(exc).__name__}")
            await self._finish(session, outcome)
            return outcome

    async def _finish(self, session: ResearchSession, outcome: RunOutcome) -> None:
        message = None
        if outcome.failures:
            message = "; ".join(outcome.failures[:3])
        await self.sessions.update_session(
            session.id,
            session.user_id,
            {
                "status": outcome.status,
                "provider": self.provider.name,
                "provider_message": outcome.provider_message,
                "error": message,
                "progress_message": f"{outcome.sources_created} sources, {outcome.evidence_created} evidence passages",
                "completed_at": datetime.utcnow(),
            },
        )

    async def _load_brief(self, session: ResearchSession) -> Optional[DocumentBrief]:
        if not session.brief_id:
            return None
        from app.repositories.document_brief_repository import DocumentBriefRepository

        repo = DocumentBriefRepository(self.db)
        return await repo.get_by_id(session.brief_id, session.user_id)

    # -- discovery --------------------------------------------------------
    async def _discover(
        self,
        session: ResearchSession,
        questions: List[ResearchQuestion],
        outcome: RunOutcome,
    ) -> Tuple[List[ResearchSource], List[str]]:
        """Collect candidate sources from all enabled channels."""
        created: List[ResearchSource] = []
        failures: List[str] = []

        if session.include_knowledge_base:
            kb_sources, kb_failures = await self._discover_knowledge_base(session, questions)
            created.extend(kb_sources)
            failures.extend(kb_failures)

        if session.requested_urls:
            url_sources, url_failures = await self._discover_user_urls(session)
            created.extend(url_sources)
            failures.extend(url_failures)

        if session.external_research:
            web_sources, web_failures, provider_message = await self._discover_web(
                session, questions
            )
            created.extend(web_sources)
            failures.extend(web_failures)
            outcome.provider_message = provider_message

        outcome.sources_created = len(created)
        return created, failures

    async def _discover_knowledge_base(
        self,
        session: ResearchSession,
        questions: List[ResearchQuestion],
    ) -> Tuple[List[ResearchSource], List[str]]:
        """Reuse Phase 4 retrieval - no second copy of the file store."""
        sources: List[ResearchSource] = []
        failures: List[str] = []

        for question in questions[: self.settings.RESEARCH_MAX_QUESTIONS]:
            try:
                results = await self.retrieval.search(
                    question.question,
                    session.user_id,
                    limit=3,
                    file_ids=session.knowledge_file_ids or None,
                )
            except Exception as exc:
                failures.append(f"Knowledge-base search failed: {type(exc).__name__}")
                continue

            for result in results:
                existing = await self.sources.find_knowledge_source(
                    session.id, session.user_id, result["file_id"], result["chunk_id"]
                )
                if existing:
                    sources.append(existing)
                    continue

                source = ResearchSource(
                    session_id=session.id,
                    user_id=session.user_id,
                    research_question_id=question.id,
                    source_type=SourceType.KNOWLEDGE_BASE,
                    retrieval_status=RetrievalStatus.FETCHED,
                    title=result["original_filename"],
                    url=None,
                    canonical_url=None,
                    publisher="Uploaded document",
                    content_text=result["chunk_text"],
                    excerpt=result["chunk_text"][:400],
                    word_count=len(result["chunk_text"].split()),
                    source_type_label="knowledge_base",
                    evaluation_notes=[
                        "From your own knowledge base (Phase 4 upload).",
                        "Ownership verified against the authenticated user.",
                    ],
                    relevance_score=round(1.0 / (1.0 + float(result.get("relevance_score") or 0.0)), 4),
                    knowledge_file_id=result["file_id"],
                    chunk_id=result["chunk_id"],
                    page_number=result.get("page_number"),
                    section_title=result.get("section_title"),
                    accessed_at=datetime.utcnow(),
                )
                try:
                    sources.append(await self.sources.create(source))
                except Exception as exc:
                    failures.append(f"Could not store a knowledge-base source: {type(exc).__name__}")

        return sources, failures

    async def _discover_user_urls(
        self, session: ResearchSession
    ) -> Tuple[List[ResearchSource], List[str]]:
        """Create placeholder sources for URLs the user added."""
        sources: List[ResearchSource] = []
        failures: List[str] = []

        for raw_url in session.requested_urls[: self.settings.RESEARCH_MAX_USER_URLS]:
            try:
                normalized, _host = validate_url_syntax(raw_url)
            except UnsafeUrlError as exc:
                failures.append(f"URL rejected ({raw_url[:80]}): {exc}")
                continue

            existing = await self.sources.find_by_canonical(
                session.id, session.user_id, normalized
            )
            if existing:
                sources.append(existing)
                continue

            source = ResearchSource(
                session_id=session.id,
                user_id=session.user_id,
                source_type=SourceType.USER_URL,
                retrieval_status=RetrievalStatus.DISCOVERED,
                title=normalized,
                url=normalized,
                canonical_url=normalized,
                evaluation_notes=["URL supplied by you."],
                selected=True,
            )
            try:
                sources.append(await self.sources.create(source))
            except Exception as exc:
                failures.append(f"Could not store a URL source: {type(exc).__name__}")

        return sources, failures

    async def _discover_web(
        self,
        session: ResearchSession,
        questions: List[ResearchQuestion],
    ) -> Tuple[List[ResearchSource], List[str], Optional[str]]:
        """Query the external provider. Failures are reported, never faked."""
        available, message = await self.provider.health()
        if not available:
            return [], [], message

        sources: List[ResearchSource] = []
        failures: List[str] = []
        seen_urls: set[str] = set()

        for question in questions[: self.settings.RESEARCH_MAX_QUESTIONS]:
            if len(sources) >= self.settings.RESEARCH_MAX_SOURCES:
                break
            try:
                candidates: Sequence[SearchCandidate] = await asyncio.wait_for(
                    self.provider.search(
                        question.question,
                        self.settings.RESEARCH_RESULTS_PER_QUESTION,
                    ),
                    timeout=float(self.settings.RESEARCH_FETCH_TIMEOUT_SECONDS) + 5,
                )
            except ResearchNotConfigured as exc:
                return sources, failures, str(exc)
            except ResearchTimeout:
                failures.append(f"Search timed out for: {question.question[:80]}")
                continue
            except ResearchProviderError as exc:
                failures.append(f"Search failed: {exc}")
                continue
            except asyncio.TimeoutError:
                failures.append(f"Search timed out for: {question.question[:80]}")
                continue

            for candidate in candidates:
                if len(sources) >= self.settings.RESEARCH_MAX_SOURCES:
                    break
                try:
                    normalized, _host = validate_url_syntax(candidate.url)
                except UnsafeUrlError:
                    continue
                if normalized in seen_urls:
                    continue
                seen_urls.add(normalized)

                existing = await self.sources.find_by_canonical(
                    session.id, session.user_id, normalized
                )
                if existing:
                    sources.append(existing)
                    continue

                source = ResearchSource(
                    session_id=session.id,
                    user_id=session.user_id,
                    research_question_id=question.id,
                    source_type=SourceType.WEB,
                    retrieval_status=RetrievalStatus.DISCOVERED,
                    title=candidate.title or normalized,
                    url=candidate.url,
                    canonical_url=normalized,
                    publisher=candidate.publisher,
                    published_date=candidate.published_date,
                    excerpt=candidate.snippet,
                    source_type_label=candidate.source_type_label,
                    evaluation_notes=[f"Found by {self.provider.display_name}."],
                    relevance_score=round(
                        lexical_overlap(question.question, f"{candidate.title} {candidate.snippet or ''}"),
                        4,
                    ),
                )
                try:
                    sources.append(await self.sources.create(source))
                except Exception as exc:
                    failures.append(f"Could not store a web source: {type(exc).__name__}")

        return sources, failures, None

    # -- extraction -------------------------------------------------------
    async def _read_sources(
        self,
        session: ResearchSession,
        sources: List[ResearchSource],
        outcome: RunOutcome,
    ) -> Tuple[List[ResearchSource], List[str]]:
        """Fetch every discovered web/user source and persist what we learned."""
        failures: List[str] = []
        updated: List[ResearchSource] = []

        for source in sources:
            if source.retrieval_status == RetrievalStatus.FETCHED and source.content_text:
                updated.append(source)
                continue

            if not source.url:
                updated.append(source)
                continue

            result: FetchResult = await self.fetch(
                source.url,
                timeout_seconds=float(self.settings.RESEARCH_FETCH_TIMEOUT_SECONDS),
                max_bytes=int(self.settings.RESEARCH_MAX_PAGE_BYTES),
                max_redirects=int(self.settings.RESEARCH_MAX_REDIRECTS),
            )

            if not result.ok:
                failures.append(
                    f"{source.title[:60]}: {result.error or result.status.value}"
                )
                refreshed = await self.sources.update(
                    source.id,
                    session.user_id,
                    {
                        "retrieval_status": result.status,
                        "error": (result.error or result.status.value)[:500],
                        "http_status": result.http_status,
                        "accessed_at": datetime.utcnow(),
                        "evaluation_notes": source.evaluation_notes + result.notes,
                    },
                )
                updated.append(refreshed or source)
                continue

            page = result.page
            text = (page.text if page else result.text) or ""
            title = (page.title if page else None) or source.title
            notes = list(source.evaluation_notes)
            notes.extend(result.notes)

            if page:
                if page.author and not source.author:
                    notes.append("Author found in page metadata.")
                if not page.published_date:
                    notes.append("No publication date found; citations will show n.d.")
                if page.source_type_label != "unknown":
                    notes.append(f"Source type hint: {page.source_type_label}.")

            refreshed = await self.sources.update(
                source.id,
                session.user_id,
                {
                    "retrieval_status": RetrievalStatus.FETCHED,
                    "title": title[:500],
                    "canonical_url": normalize_url(result.final_url or source.canonical_url or source.url),
                    "publisher": (page.publisher if page else None) or source.publisher,
                    "author": (page.author if page else None) or source.author,
                    "published_date": (page.published_date if page else None) or source.published_date,
                    "content_text": text[: self.settings.RESEARCH_MAX_PAGE_BYTES],
                    "excerpt": (page.passages[0].text[:400] if page and page.passages else text[:400]),
                    "word_count": len(text.split()),
                    "http_status": result.http_status,
                    "source_type_label": (page.source_type_label if page else source.source_type_label),
                    "evaluation_notes": notes,
                    "accessed_at": datetime.utcnow(),
                    "error": None,
                },
            )
            updated.append(refreshed or source)

        return updated, failures

    # -- evidence ---------------------------------------------------------
    async def _build_evidence(
        self,
        session: ResearchSession,
        questions: List[ResearchQuestion],
        sources: List[ResearchSource],
        outcome: RunOutcome,
    ) -> None:
        """Turn fetched text into traceable evidence rows."""
        question_by_id = {question.id: question for question in questions}
        created_count = 0

        for source in sources:
            if not source.content_text or source.retrieval_status != RetrievalStatus.FETCHED:
                continue

            question = question_by_id.get(source.research_question_id or "")
            query = question.question if question else session.title

            passages = build_passages(
                source.content_text,
                min_chars=int(self.settings.RESEARCH_MIN_PASSAGE_CHARS),
            )
            scored = sorted(
                (
                    (lexical_overlap(query, passage.text), passage)
                    for passage in passages
                ),
                key=lambda pair: pair[0],
                reverse=True,
            )

            kept = 0
            for score, passage in scored:
                if kept >= MAX_EVIDENCE_PER_SOURCE:
                    break
                if score < EVIDENCE_MIN_SCORE and kept > 0:
                    continue

                finding = passage.text.split(". ")[0][:300]
                record = EvidenceRecord(
                    session_id=session.id,
                    source_id=source.id,
                    user_id=session.user_id,
                    research_question_id=source.research_question_id,
                    claim_or_finding=finding,
                    passage=passage.text,
                    evidence_type=EvidenceType.CONTEXT,
                    url=source.url,
                    knowledge_file_id=source.knowledge_file_id,
                    page_number=source.page_number,
                    section_title=passage.section_title or source.section_title,
                    retrieved_at=datetime.utcnow(),
                )
                stored = await self.evidence.create(record)
                if stored:
                    created_count += 1
                    kept += 1

        outcome.evidence_created = created_count
