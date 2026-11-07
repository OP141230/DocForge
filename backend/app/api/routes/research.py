"""Phase 5 API: research sessions, sources, evidence, citations, verification.

Conventions follow the existing routes: the router is mounted under ``/api``,
authentication comes from :func:`app.core.auth.get_current_user`, and every
lookup is scoped by the authenticated user's id. A resource that belongs to
someone else returns **404** (not 403) so IDs cannot be probed.

Route shape
-----------
``/research/...``   research sessions, questions, sources, evidence
``/documents/{id}/...``  citations and verification for one document

Long operations (research runs, verification) are never faked: a run returns
``202`` and the client polls the session, and verification returns the findings
it actually produced.
"""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.database import Database, get_database
from app.core.rate_limit import RateLimitExceeded, enforce
from app.core.url_validation import UnsafeUrlError, validate_url_syntax
from app.models.auth import User
from app.models.research import (
    ChangeCitationStyleRequest,
    ClaimVerification,
    CreateEvidenceRequest,
    CreateResearchSessionRequest,
    EvidenceRecord,
    ResearchQuestion,
    ResearchRunResponse,
    ResearchSession,
    ResearchSessionDetail,
    ResearchSource,
    ResearchStatus,
    SourceType,
    UpdateEvidenceRequest,
    UpdateQuestionsRequest,
    UpdateResearchSessionRequest,
    UpdateSourceRequest,
    UpdateVerificationRequest,
    VerificationReport,
    VerificationStatus,
    VerifyDocumentRequest,
)
from app.providers.research import get_provider_status
from app.repositories.document_brief_repository import DocumentBriefRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.knowledge_file_repository import KnowledgeFileRepository
from app.repositories.research_repository import ResearchRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.repositories.verification_repository import VerificationRepository
from app.services.citation_service import CitationService
from app.services.citations import SUPPORTED_STYLES, normalize_style
from app.services.research_service import ResearchService
from app.services.verification_service import VerificationService

logger = logging.getLogger(__name__)
router = APIRouter()

# Strong references so background tasks are not garbage-collected mid-run.
_running_tasks: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    task = asyncio.create_task(coro)
    _running_tasks.add(task)
    task.add_done_callback(_running_tasks.discard)


def _enforce_rate_limit(bucket: str, user_id: str, limit: int) -> None:
    try:
        enforce(bucket, user_id, limit)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc


async def _get_session_or_404(db: Database, session_id: str, user_id: str) -> ResearchSession:
    session = await ResearchRepository(db).get_session(session_id, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session


async def _detail(db: Database, session: ResearchSession, user_id: str) -> ResearchSessionDetail:
    repo = ResearchRepository(db)
    questions = await repo.list_questions(session.id, user_id)
    source_counts = await ResearchSourceRepository(db).count_by_status(session.id, user_id)
    evidence_count = await EvidenceRepository(db).count_for_session(session.id, user_id)
    return ResearchSessionDetail(
        session=session,
        questions=questions,
        source_counts=source_counts,
        evidence_count=evidence_count,
    )


# ---------------------------------------------------------------------------
# Provider status
# ---------------------------------------------------------------------------

@router.get("/research/providers")
async def research_provider_status(current_user: User = Depends(get_current_user)):
    """Report whether external search is configured, without leaking keys."""
    provider_status = await get_provider_status()
    settings = get_settings()
    return {
        "provider": provider_status,
        "supported_styles": [style.value for style in SUPPORTED_STYLES],
        "limits": {
            "max_questions": settings.RESEARCH_MAX_QUESTIONS,
            "results_per_question": settings.RESEARCH_RESULTS_PER_QUESTION,
            "max_sources": settings.RESEARCH_MAX_SOURCES,
            "max_user_urls": settings.RESEARCH_MAX_USER_URLS,
            "max_page_bytes": settings.RESEARCH_MAX_PAGE_BYTES,
            "verification_max_claims": settings.VERIFICATION_MAX_CLAIMS,
        },
    }


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@router.post("/research/sessions", response_model=ResearchSessionDetail, status_code=201)
async def create_session(
    request: CreateResearchSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Create a research session, optionally bound to a brief or document."""
    title = (request.title or "").strip()

    if request.brief_id:
        brief = await DocumentBriefRepository(db).get_by_id(request.brief_id, current_user.id)
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        title = title or brief.title

    if request.document_id:
        document = await DocumentRepository(db).get_by_id(request.document_id, current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        title = title or document.title

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Provide a title, a brief_id or a document_id",
        )

    # Validate every file the session is allowed to use.
    file_repo = KnowledgeFileRepository(db)
    for file_id in request.knowledge_file_ids:
        if not await file_repo.get_by_id(file_id, current_user.id):
            raise HTTPException(status_code=404, detail=f"Knowledge file not found: {file_id}")

    # Reject unsafe URLs at input time rather than during the run.
    normalized_urls = []
    for raw_url in request.urls:
        try:
            normalized, _host = validate_url_syntax(raw_url)
        except UnsafeUrlError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid URL: {exc}") from exc
        if normalized not in normalized_urls:
            normalized_urls.append(normalized)

    style = request.citation_style
    if request.brief_id:
        brief = await DocumentBriefRepository(db).get_by_id(request.brief_id, current_user.id)
        if brief and brief.citation_style:
            try:
                style = normalize_style(brief.citation_style)
            except ValueError:
                pass

    session = ResearchSession(
        user_id=current_user.id,
        brief_id=request.brief_id,
        document_id=request.document_id,
        title=title[:200],
        external_research=request.external_research,
        include_knowledge_base=request.include_knowledge_base,
        citation_style=style,
        requested_urls=normalized_urls,
        knowledge_file_ids=request.knowledge_file_ids,
    )
    session = await ResearchRepository(db).create_session(session)
    return await _detail(db, session, current_user.id)


@router.get("/research/sessions")
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """List the current user's research sessions."""
    sessions, total = await ResearchRepository(db).list_sessions(
        current_user.id, limit, offset
    )
    return {"sessions": sessions, "total": total, "limit": limit, "offset": offset}


@router.get("/research/sessions/{session_id}", response_model=ResearchSessionDetail)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    session = await _get_session_or_404(db, session_id, current_user.id)
    return await _detail(db, session, current_user.id)


@router.patch("/research/sessions/{session_id}", response_model=ResearchSessionDetail)
async def update_session(
    session_id: str,
    request: UpdateResearchSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Update research settings. Content changes are ignored while a run is active."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    if session.status == ResearchStatus.RUNNING:
        raise HTTPException(
            status_code=409,
            detail="Research is running; wait for it to finish before changing settings.",
        )

    updates = request.model_dump(exclude_unset=True)

    if "knowledge_file_ids" in updates and updates["knowledge_file_ids"] is not None:
        file_repo = KnowledgeFileRepository(db)
        for file_id in updates["knowledge_file_ids"]:
            if not await file_repo.get_by_id(file_id, current_user.id):
                raise HTTPException(status_code=404, detail=f"Knowledge file not found: {file_id}")

    if "urls" in updates:
        normalized_urls = []
        for raw_url in updates.pop("urls") or []:
            try:
                normalized, _host = validate_url_syntax(raw_url)
            except UnsafeUrlError as exc:
                raise HTTPException(status_code=400, detail=f"Invalid URL: {exc}") from exc
            if normalized not in normalized_urls:
                normalized_urls.append(normalized)
        updates["requested_urls"] = normalized_urls

    updated = await ResearchRepository(db).update_session(session_id, current_user.id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Research session not found")
    return await _detail(db, updated, current_user.id)


@router.delete("/research/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Delete a session, its sources, evidence and citations (never the files)."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    if session.status == ResearchStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Cannot delete a running research session.")
    deleted = await ResearchRepository(db).delete_session(session_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Research session not found")
    return Response(status_code=204)


@router.post("/research/sessions/{session_id}/document/{document_id}", response_model=ResearchSession)
async def link_document(
    session_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Attach a generated document to an existing research session."""
    await _get_session_or_404(db, session_id, current_user.id)
    document = await DocumentRepository(db).get_by_id(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    updated = await ResearchRepository(db).update_session(
        session_id, current_user.id, {"document_id": document_id}
    )
    return updated


# ---------------------------------------------------------------------------
# Research questions
# ---------------------------------------------------------------------------

@router.post("/research/sessions/{session_id}/plan")
async def plan_questions(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """(Re)derive research questions from the brief and approved outline."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    if session.status == ResearchStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Research is running.")

    brief = None
    if session.brief_id:
        brief = await DocumentBriefRepository(db).get_by_id(session.brief_id, current_user.id)

    service = ResearchService(db)
    questions = await service.plan_questions(session, brief)
    return {"session_id": session_id, "questions": questions}


@router.put("/research/sessions/{session_id}/questions")
async def replace_questions(
    session_id: str,
    request: UpdateQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Replace the session's research questions (order preserved)."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    if session.status == ResearchStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Research is running.")

    settings = get_settings()
    if not request.questions:
        raise HTTPException(status_code=400, detail="At least one research question is required")
    if len(request.questions) > settings.RESEARCH_MAX_QUESTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"At most {settings.RESEARCH_MAX_QUESTIONS} research questions are allowed",
        )

    created = await ResearchRepository(db).replace_questions(
        session_id,
        current_user.id,
        [question.model_dump() for question in request.questions],
    )
    return {"session_id": session_id, "questions": created}


# ---------------------------------------------------------------------------
# Running research
# ---------------------------------------------------------------------------

@router.post(
    "/research/sessions/{session_id}/run",
    response_model=ResearchRunResponse,
    status_code=202,
)
async def run_research(
    session_id: str,
    wait: bool = Query(False, description="Wait for completion (used by tests/CLI)"),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Start a research run.

    By default the run happens in the background and the client polls the
    session. ``wait=true`` runs it inline, which is convenient for scripts.
    """
    session = await _get_session_or_404(db, session_id, current_user.id)
    if session.status == ResearchStatus.RUNNING:
        raise HTTPException(status_code=409, detail="A research run is already in progress")

    settings = get_settings()
    _enforce_rate_limit(
        "research_run", current_user.id, settings.RESEARCH_REQUEST_LIMIT_PER_MINUTE
    )

    service = ResearchService(db)

    if wait:
        outcome = await service.run(session_id, current_user.id)
        return ResearchRunResponse(
            session_id=session_id,
            status=outcome.status,
            message="; ".join(outcome.failures[:3]) or "Research finished",
        )

    _spawn(service.run(session_id, current_user.id))
    return ResearchRunResponse(
        session_id=session_id,
        status=ResearchStatus.RUNNING,
        message="Research started. Poll the session for progress.",
    )


# ---------------------------------------------------------------------------
# Sources & evidence
# ---------------------------------------------------------------------------

@router.get("/research/sessions/{session_id}/sources")
async def list_sources(
    session_id: str,
    selected_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    await _get_session_or_404(db, session_id, current_user.id)
    sources = await ResearchSourceRepository(db).list_by_session(
        session_id, current_user.id, selected_only=selected_only
    )
    return {"session_id": session_id, "sources": sources, "total": len(sources)}


@router.get("/research/sources/{source_id}", response_model=ResearchSource)
async def get_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    source = await ResearchSourceRepository(db).get_by_id(source_id, current_user.id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/research/sources/{source_id}", response_model=ResearchSource)
async def update_source(
    source_id: str,
    request: UpdateSourceRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Include or exclude a source. Excluded sources are not used for generation."""
    updated = await ResearchSourceRepository(db).update(
        source_id, current_user.id, {"selected": request.selected}
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Source not found")
    return updated


@router.get("/research/sessions/{session_id}/evidence")
async def list_evidence(
    session_id: str,
    selected_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    await _get_session_or_404(db, session_id, current_user.id)
    evidence = await EvidenceRepository(db).list_by_session(
        session_id, current_user.id, selected_only=selected_only
    )
    return {"session_id": session_id, "evidence": evidence, "total": len(evidence)}


@router.post(
    "/research/sessions/{session_id}/evidence",
    response_model=EvidenceRecord,
    status_code=201,
)
async def create_evidence(
    session_id: str,
    request: CreateEvidenceRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Add a manual evidence passage taken from a source you inspected."""
    session = await _get_session_or_404(db, session_id, current_user.id)
    source = await ResearchSourceRepository(db).get_by_id(request.source_id, current_user.id)
    if not source or source.session_id != session_id:
        raise HTTPException(status_code=404, detail="Source not found in this session")

    from app.models.research import EvidenceRecord as EvidenceModel

    record = EvidenceModel(
        session_id=session_id,
        source_id=source.id,
        user_id=current_user.id,
        research_question_id=request.research_question_id,
        claim_or_finding=request.claim_or_finding,
        passage=request.passage,
        evidence_type=request.evidence_type,
        url=source.url,
        knowledge_file_id=source.knowledge_file_id,
        page_number=source.page_number,
        section_title=source.section_title,
    )
    stored = await EvidenceRepository(db).create(record)
    if not stored:
        raise HTTPException(
            status_code=409,
            detail="This passage already exists as evidence for that source.",
        )
    return stored


@router.patch("/research/evidence/{evidence_id}", response_model=EvidenceRecord)
async def update_evidence(
    evidence_id: str,
    request: UpdateEvidenceRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    updates = request.model_dump(exclude_unset=True)
    updated = await EvidenceRepository(db).update(evidence_id, current_user.id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return updated


@router.delete("/research/evidence/{evidence_id}", status_code=204)
async def delete_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    deleted = await EvidenceRepository(db).delete(evidence_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------

async def _reference_list(db: Database, document_id: str, user: User, style: Optional[str]):
    document = await DocumentRepository(db).get_by_id(document_id, user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    service = CitationService(db)
    session = await ResearchRepository(db).get_latest_for_document(document_id, user.id)
    try:
        return await service.reference_list(
            document_id,
            user.id,
            style or (session.citation_style if session else "apa"),
            document=document,
            session_id=session.id if session else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/documents/{document_id}/citations")
async def get_citations(
    document_id: str,
    style: Optional[str] = Query(None, description="apa | ieee | mla | chicago"),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Reference list + citation-integrity findings for one document."""
    return await _reference_list(db, document_id, current_user, style)


@router.patch("/documents/{document_id}/citation-style")
async def change_citation_style(
    document_id: str,
    request: ChangeCitationStyleRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Re-render in-text citations and the reference list in a new style."""
    document = await DocumentRepository(db).get_by_id(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    service = CitationService(db)
    try:
        response = await service.restyle(document_id, current_user.id, request.style)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session = await ResearchRepository(db).get_latest_for_document(document_id, current_user.id)
    if session:
        await ResearchRepository(db).update_session(
            session.id, current_user.id, {"citation_style": request.style}
        )
    return response


@router.delete("/citations/{citation_id}", status_code=204)
async def delete_citation(
    citation_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Remove a citation. The source itself is kept."""
    from app.repositories.citation_repository import CitationRepository

    deleted = await CitationRepository(db).delete(citation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Citation not found")
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

@router.post("/documents/{document_id}/verify", response_model=VerificationReport)
async def verify_document(
    document_id: str,
    request: Optional[VerifyDocumentRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Check a document's factual claims against retrieved evidence."""
    settings = get_settings()
    _enforce_rate_limit(
        "verification", current_user.id, settings.VERIFICATION_REQUEST_LIMIT_PER_MINUTE
    )

    document = await DocumentRepository(db).get_by_id(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    payload = request or VerifyDocumentRequest()
    service = VerificationService(db)
    try:
        return await service.verify_document(
            document_id,
            current_user.id,
            research_session_id=payload.research_session_id,
            max_claims=payload.max_claims,
            section_titles=payload.section_titles,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/documents/{document_id}/verifications", response_model=VerificationReport)
async def get_verifications(
    document_id: str,
    status_filter: Optional[str] = Query(
        None, alias="status", description="supported | contradicted | insufficient_evidence | not_checked"
    ),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Read existing findings (optionally filtered by status)."""
    parsed: Optional[VerificationStatus] = None
    if status_filter:
        try:
            parsed = VerificationStatus(status_filter)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid status filter. Use supported, contradicted, "
                "insufficient_evidence or not_checked.",
            ) from exc

    service = VerificationService(db)
    try:
        return await service.report(document_id, current_user.id, parsed)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/verifications/{verification_id}", response_model=ClaimVerification)
async def update_verification(
    verification_id: str,
    request: UpdateVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Flag a finding for manual review (verification never edits content)."""
    updates = request.model_dump(exclude_unset=True)
    updated = await VerificationRepository(db).update(
        verification_id, current_user.id, updates
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Verification finding not found")
    return updated


@router.post("/verifications/{verification_id}/recheck", response_model=ClaimVerification)
async def recheck_verification(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database),
):
    """Re-run verification for one claim."""
    settings = get_settings()
    _enforce_rate_limit(
        "verification", current_user.id, settings.VERIFICATION_REQUEST_LIMIT_PER_MINUTE
    )
    service = VerificationService(db)
    finding = await service.recheck(verification_id, current_user.id)
    if not finding:
        raise HTTPException(status_code=404, detail="Verification finding not found")
    return finding


@router.get("/research/status-labels")
async def verification_status_labels(current_user: User = Depends(get_current_user)):
    """Labels used by the UI so front and back ends cannot drift apart."""
    from app.models.research import VERIFICATION_STATUS_LABELS

    return {
        "statuses": [
            {"value": key.value, "label": label}
            for key, label in VERIFICATION_STATUS_LABELS.items()
        ]
    }
