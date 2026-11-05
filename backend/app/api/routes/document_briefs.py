"""DocumentBrief CRUD and workflow endpoints."""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Response, Depends, Query
from typing import Optional

from app.models.document_brief import (
    DocumentBrief,
    CreateBriefRequest,
    UpdateBriefRequest,
    UpdateOutlineRequest,
    OutlineItem,
)
from app.models.generation import DocumentRequirements, OutlineResponse
from app.models.document_ir import DocumentIR
from app.models.auth import User
from app.core.database import get_database
from app.core.auth import get_current_user
from app.repositories.document_brief_repository import DocumentBriefRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.providers.factory import get_provider


router = APIRouter()


@router.post("/document-briefs", response_model=DocumentBrief, status_code=201)
async def create_brief(
    request: CreateBriefRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new document brief (requires authentication)."""
    try:
        db = await get_database()
        brief_repo = DocumentBriefRepository(db)
        
        # If conversation_id provided, verify ownership
        if request.conversation_id:
            conv_repo = ConversationRepository(db)
            conversation = await conv_repo.get_by_id(request.conversation_id, user_id=current_user.id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create brief
        brief_data = request.dict()
        brief = await brief_repo.create(brief_data, user_id=current_user.id)
        return brief
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document brief: {str(e)}")


@router.get("/document-briefs")
async def list_briefs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """List user's document briefs with pagination (requires authentication)."""
    try:
        db = await get_database()
        repo = DocumentBriefRepository(db)
        briefs, total = await repo.list_by_user(current_user.id, limit, offset)
        return {
            "briefs": briefs,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list document briefs: {str(e)}")


@router.get("/document-briefs/{brief_id}", response_model=DocumentBrief)
async def get_brief(
    brief_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a document brief by ID (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentBriefRepository(db)
        brief = await repo.get_by_id(brief_id, user_id=current_user.id)
        
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        return brief
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document brief: {str(e)}")


@router.patch("/document-briefs/{brief_id}", response_model=DocumentBrief)
async def update_brief(
    brief_id: str,
    request: UpdateBriefRequest,
    current_user: User = Depends(get_current_user)
):
    """Update a document brief (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentBriefRepository(db)
        
        # If conversation_id in update, verify ownership
        if request.conversation_id is not None:
            conv_repo = ConversationRepository(db)
            conversation = await conv_repo.get_by_id(request.conversation_id, user_id=current_user.id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Build updates dict, excluding None values
        updates = {k: v for k, v in request.dict(exclude_unset=True).items() if v is not None}
        
        if not updates:
            # No updates provided, just return existing
            brief = await repo.get_by_id(brief_id, user_id=current_user.id)
            if not brief:
                raise HTTPException(status_code=404, detail="Document brief not found")
            return brief
        
        brief = await repo.update(brief_id, current_user.id, updates)
        
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        return brief
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document brief: {str(e)}")


@router.delete("/document-briefs/{brief_id}", status_code=204)
async def delete_brief(
    brief_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document brief (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentBriefRepository(db)
        
        deleted = await repo.delete(brief_id, user_id=current_user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document brief: {str(e)}")


@router.post("/document-briefs/{brief_id}/outline", response_model=DocumentBrief)
async def generate_outline(
    brief_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate outline from document brief using AI (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentBriefRepository(db)
        
        # Get brief
        brief = await repo.get_by_id(brief_id, user_id=current_user.id)
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        # Convert brief to DocumentRequirements
        requirements = DocumentRequirements(
            document_type=brief.document_type,
            topic=brief.topic,
            title=brief.title,
            audience=brief.audience,
            tone=brief.tone,
            language=brief.language,
            length=brief.desired_length or "medium",
            additional_instructions=brief.additional_instructions,
        )
        
        # Generate outline using AI provider
        provider = get_provider()
        outline_response = await provider.generate_outline(requirements)
        
        # Update brief with generated outline
        updated_brief = await repo.update(
            brief_id,
            current_user.id,
            {"outline": outline_response.outline}
        )
        
        return updated_brief
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate outline: {str(e)}")


@router.patch("/document-briefs/{brief_id}/outline", response_model=DocumentBrief)
async def update_outline(
    brief_id: str,
    request: UpdateOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    """Update the outline manually (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentBriefRepository(db)
        
        # Update outline
        brief = await repo.update(
            brief_id,
            current_user.id,
            {"outline": request.outline, "outline_approved": False, "outline_approved_at": None}
        )
        
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        return brief
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update outline: {str(e)}")


@router.post("/document-briefs/{brief_id}/outline/approve", response_model=DocumentBrief)
async def approve_outline(
    brief_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark outline as approved (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentBriefRepository(db)
        
        # Get brief to verify it has an outline
        brief = await repo.get_by_id(brief_id, user_id=current_user.id)
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        if not brief.outline or len(brief.outline) == 0:
            raise HTTPException(status_code=400, detail="Cannot approve: outline has not been generated yet")
        
        # Approve outline
        updated_brief = await repo.update(
            brief_id,
            current_user.id,
            {"outline_approved": True, "outline_approved_at": datetime.utcnow()}
        )
        
        return updated_brief
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve outline: {str(e)}")


@router.post("/document-briefs/{brief_id}/generate", response_model=DocumentIR)
async def generate_document(
    brief_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate full document from approved brief (requires authentication and ownership)."""
    try:
        db = await get_database()
        brief_repo = DocumentBriefRepository(db)
        doc_repo = DocumentRepository(db)
        
        # Get brief
        brief = await brief_repo.get_by_id(brief_id, user_id=current_user.id)
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        # Verify outline is approved
        if not brief.outline_approved:
            raise HTTPException(status_code=400, detail="Cannot generate document: outline must be approved first")
        
        if not brief.outline or len(brief.outline) == 0:
            raise HTTPException(status_code=400, detail="Cannot generate document: outline is empty")
        
        # Convert brief to DocumentRequirements
        requirements = DocumentRequirements(
            document_type=brief.document_type,
            topic=brief.topic,
            title=brief.title,
            audience=brief.audience,
            tone=brief.tone,
            language=brief.language,
            length=brief.desired_length or "medium",
            additional_instructions=brief.additional_instructions,
        )
        
        # Generate document using AI provider
        provider = get_provider()
        outline_response = OutlineResponse(outline=brief.outline)
        document = await provider.generate_content(outline_response, requirements)
        
        # Inject brief_id into document metadata for bidirectional linking
        if not document.metadata.custom_fields:
            document.metadata.custom_fields = {}
        document.metadata.custom_fields['brief_id'] = brief_id
        
        # Save document
        created_doc = await doc_repo.create(
            document,
            user_id=current_user.id,
            conversation_id=brief.conversation_id
        )
        
        # Link document to brief
        await brief_repo.update(
            brief_id,
            current_user.id,
            {"document_id": created_doc.id}
        )
        
        return created_doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate document: {str(e)}")
