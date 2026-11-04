"""Document CRUD and version management endpoints."""
from fastapi import APIRouter, HTTPException, Response, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
import io

from app.models.document_ir import DocumentIR
from app.models.auth import User
from app.core.database import get_database
from app.core.auth import get_current_user
from app.repositories.document_repository import DocumentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.exporters.factory import get_exporter

router = APIRouter()


@router.post("/documents", response_model=DocumentIR, status_code=201)
async def create_document(
    document: DocumentIR, 
    current_user: User = Depends(get_current_user),
    conversation_id: Optional[str] = Query(None, description="Optional conversation ID to associate with document")
):
    """Create a new document (requires authentication). Optionally link to a conversation."""
    try:
        db = await get_database()
        doc_repo = DocumentRepository(db)
        
        # If conversation_id provided, verify ownership
        if conversation_id:
            conv_repo = ConversationRepository(db)
            conversation = await conv_repo.get_by_id(conversation_id, user_id=current_user.id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        
        created = await doc_repo.create(document, user_id=current_user.id, conversation_id=conversation_id)
        return created
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/documents")
async def list_documents(
    limit: int = 20, 
    offset: int = 0, 
    current_user: User = Depends(get_current_user)
):
    """List user's documents with pagination (requires authentication)."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        documents, total = await repo.list_documents(limit, offset, user_id=current_user.id)
        return {
            "documents": documents,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/documents/{document_id}", response_model=DocumentIR)
async def get_document(document_id: str, current_user: User = Depends(get_current_user)):
    """Get a document by ID (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        document = await repo.get_by_id(document_id, user_id=current_user.id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


@router.put("/documents/{document_id}", response_model=DocumentIR)
async def update_document(
    document_id: str, 
    document: DocumentIR, 
    current_user: User = Depends(get_current_user)
):
    """Update a document (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        # Ensure document ID matches
        document.id = document_id
        
        # Check if document exists and user owns it
        existing = await repo.get_by_id(document_id, user_id=current_user.id)
        if not existing:
            raise HTTPException(status_code=404, detail="Document not found")
        
        updated = await repo.update(document)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: str, current_user: User = Depends(get_current_user)):
    """Delete a document (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        deleted = await repo.delete(document_id, user_id=current_user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.post("/documents/{document_id}/versions", status_code=201)
async def create_version(document_id: str, current_user: User = Depends(get_current_user)):
    """Create a version snapshot of a document (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        # Verify ownership
        document = await repo.get_by_id(document_id, user_id=current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        version = await repo.create_version(document_id)
        return version
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")


@router.get("/documents/{document_id}/versions")
async def list_versions(document_id: str, current_user: User = Depends(get_current_user)):
    """List all versions of a document (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        # Verify ownership
        document = await repo.get_by_id(document_id, user_id=current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        versions = await repo.list_versions(document_id)
        return versions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")


@router.post("/documents/{document_id}/versions/{version_number}/restore", response_model=DocumentIR)
async def restore_version(
    document_id: str, 
    version_number: int, 
    current_user: User = Depends(get_current_user)
):
    """Restore a document to a specific version (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        # Verify ownership
        existing = await repo.get_by_id(document_id, user_id=current_user.id)
        if not existing:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = await repo.restore_version(document_id, version_number)
        return document
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore version: {str(e)}")


@router.post("/documents/{document_id}/export")
async def export_document(
    document_id: str, 
    format: str, 
    current_user: User = Depends(get_current_user)
):
    """Export a document to specified format (requires authentication and ownership)."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        document = await repo.get_by_id(document_id, user_id=current_user.id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        exporter = get_exporter(format)
        if not exporter:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        # Export document
        file_bytes = exporter.export(document)
        
        # Create filename
        safe_title = "".join(c for c in document.title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}{exporter.file_extension}"
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=exporter.mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export document: {str(e)}")
