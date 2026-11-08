"""Phase 6 API: reviews, findings, edit proposals, compliance and versions.

Conventions match Phases 1-5: ``Depends(get_current_user)`` for authentication,
ownership verified by loading the record with the session user's id (never an id
from the request body), and ``404`` for anything the caller does not own.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_current_user
from app.core.database import get_database
from app.models.auth import User
from app.models.document_ir import DocumentIR
from app.models.review import (
    ComplianceReport,
    EditProposal,
    FindingStatus,
    ReviewCategory,
    ReviewFinding,
    ReviewReport,
    ReviewScope,
    Severity,
    StartReviewRequest,
    UpdateFindingRequest,
    ApplyProposalRequest,
    ProposeEditRequest,
    VersionComparison,
    VersionEntry,
)
from app.repositories.document_repository import DocumentRepository
from app.repositories.review_repository import EditProposalRepository
from app.services.compliance_service import ComplianceService
from app.services.editing_service import EditConflict, EditingService
from app.services.review_service import ReviewService
from app.services.version_service import VersionService

router = APIRouter()


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@router.post("/documents/{document_id}/reviews", response_model=ReviewReport, status_code=201)
async def start_review(
    document_id: str,
    request: StartReviewRequest,
    current_user: User = Depends(get_current_user),
):
    """Run a review (full document or one section) and store its findings."""
    db = await get_database()
    service = ReviewService(db)
    try:
        return await service.start_review(document_id, current_user.id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(exc)}")


@router.get("/documents/{document_id}/reviews", response_model=List[ReviewReport])
async def list_reviews(
    document_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """List recent reviews for a document, with findings and summaries."""
    db = await get_database()
    documents = DocumentRepository(db)
    if not await documents.get_by_id(document_id, current_user.id):
        raise HTTPException(status_code=404, detail="Document not found")

    service = ReviewService(db)
    sessions = await service.reviews.list_sessions(document_id, current_user.id, limit=limit)
    reports: List[ReviewReport] = []
    for session in sessions:
        reports.append(await service.report(session.id, current_user.id))
    return reports


@router.get("/documents/{document_id}/reviews/latest", response_model=Optional[ReviewReport])
async def latest_review(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return the most recent review, or ``null`` when none has run."""
    db = await get_database()
    documents = DocumentRepository(db)
    if not await documents.get_by_id(document_id, current_user.id):
        raise HTTPException(status_code=404, detail="Document not found")
    service = ReviewService(db)
    return await service.latest_report(document_id, current_user.id)


@router.get("/reviews/{review_id}", response_model=ReviewReport)
async def get_review(
    review_id: str,
    category: Optional[ReviewCategory] = None,
    severity: Optional[Severity] = None,
    status: Optional[FindingStatus] = None,
    current_user: User = Depends(get_current_user),
):
    """Read a stored review, optionally filtered by category/severity/status."""
    db = await get_database()
    service = ReviewService(db)
    try:
        return await service.report(
            review_id,
            current_user.id,
            category=category,
            severity=severity,
            status=status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/findings/{finding_id}", response_model=ReviewFinding)
async def update_finding(
    finding_id: str,
    request: UpdateFindingRequest,
    current_user: User = Depends(get_current_user),
):
    """Accept, reject, ignore, resolve or reopen a finding.

    Updating a finding's status never edits the document. Applying an accepted
    suggestion goes through the edit-proposal endpoints so it is versioned.
    """
    db = await get_database()
    service = ReviewService(db)
    finding = await service.update_finding_status(finding_id, current_user.id, request.status)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


# ---------------------------------------------------------------------------
# AI editing
# ---------------------------------------------------------------------------

@router.post("/documents/{document_id}/edit-proposals", response_model=EditProposal, status_code=201)
async def propose_edit(
    document_id: str,
    request: ProposeEditRequest,
    current_user: User = Depends(get_current_user),
):
    """Ask the AI for a rewrite. Nothing is changed until the proposal is applied."""
    db = await get_database()
    service = EditingService(db)
    try:
        return await service.propose(document_id, current_user.id, request)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message == "Document not found" else 400
        raise HTTPException(status_code=status_code, detail=message)


@router.get("/documents/{document_id}/edit-proposals", response_model=List[EditProposal])
async def list_proposals(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    db = await get_database()
    if not await DocumentRepository(db).get_by_id(document_id, current_user.id):
        raise HTTPException(status_code=404, detail="Document not found")
    return await EditProposalRepository(db).list_for_document(document_id, current_user.id)


@router.post("/edit-proposals/{proposal_id}/apply", response_model=DocumentIR)
async def apply_proposal(
    proposal_id: str,
    request: ApplyProposalRequest,
    current_user: User = Depends(get_current_user),
):
    """Apply an accepted suggestion: creates versions inside one transaction."""
    db = await get_database()
    service = EditingService(db)
    try:
        document, _ = await service.apply(
            proposal_id,
            current_user.id,
            expected_fingerprint=request.expected_fingerprint,
        )
        return document
    except EditConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message)


@router.post("/edit-proposals/{proposal_id}/reject", response_model=EditProposal)
async def reject_proposal(
    proposal_id: str,
    current_user: User = Depends(get_current_user),
):
    """Reject a suggestion. The document is not touched."""
    db = await get_database()
    service = EditingService(db)
    proposal = await service.reject(proposal_id, current_user.id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Edit proposal not found")
    return proposal


# ---------------------------------------------------------------------------
# DocumentBrief compliance
# ---------------------------------------------------------------------------

@router.post("/documents/{document_id}/compliance", response_model=ComplianceReport)
async def check_compliance(
    document_id: str,
    use_ai: bool = Query(True, description="Set false for deterministic checks only"),
    current_user: User = Depends(get_current_user),
):
    """Check the document against its linked DocumentBrief."""
    db = await get_database()
    service = ComplianceService(db)
    try:
        return await service.check(document_id, current_user.id, use_ai=use_ai)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/documents/{document_id}/compliance", response_model=Optional[ComplianceReport])
async def latest_compliance(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return the most recent compliance snapshot, if any."""
    db = await get_database()
    if not await DocumentRepository(db).get_by_id(document_id, current_user.id):
        raise HTTPException(status_code=404, detail="Document not found")
    return await ComplianceService(db).latest(document_id, current_user.id)


# ---------------------------------------------------------------------------
# Version history
# ---------------------------------------------------------------------------

@router.get("/documents/{document_id}/version-history", response_model=List[VersionEntry])
async def version_history(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    """List versions with provenance (manual / ai_accepted / restore)."""
    db = await get_database()
    try:
        return await VersionService(db).list_versions(document_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/documents/{document_id}/version-compare", response_model=VersionComparison)
async def compare_versions(
    document_id: str,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    current_user: User = Depends(get_current_user),
):
    """Diff two stored versions of a document."""
    db = await get_database()
    try:
        return await VersionService(db).compare(
            document_id, current_user.id, from_version, to_version
        )
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message)


@router.post("/documents/{document_id}/version-restore/{version_number}", response_model=DocumentIR)
async def restore_version(
    document_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user),
):
    """Restore a version. The current state is snapshotted first, so this is undoable."""
    db = await get_database()
    try:
        return await VersionService(db).restore(document_id, current_user.id, version_number)
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message)
