"""Document CRUD and version management endpoints."""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import List
import io

from app.models.document_ir import DocumentIR
from app.core.database import get_database
from app.repositories.document_repository import DocumentRepository
from app.exporters.factory import get_exporter

router = APIRouter()


@router.post("/documents", response_model=DocumentIR, status_code=201)
async def create_document(document: DocumentIR):
    """Create a new document."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        created = await repo.create(document)
        return created
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/documents")
async def list_documents(limit: int = 20, offset: int = 0):
    """List documents with pagination."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        documents, total = await repo.list_documents(limit, offset)
        return {
            "documents": documents,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/documents/{document_id}", response_model=DocumentIR)
async def get_document(document_id: str):
    """Get a document by ID."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        document = await repo.get_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


@router.put("/documents/{document_id}", response_model=DocumentIR)
async def update_document(document_id: str, document: DocumentIR):
    """Update a document."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        # Ensure document ID matches
        document.id = document_id
        
        # Check if document exists
        existing = await repo.get_by_id(document_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Document not found")
        
        updated = await repo.update(document)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: str):
    """Delete a document."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        deleted = await repo.delete(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.post("/documents/{document_id}/versions", status_code=201)
async def create_version(document_id: str):
    """Create a version snapshot of a document."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        version = await repo.create_version(document_id)
        return version
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")


@router.get("/documents/{document_id}/versions")
async def list_versions(document_id: str):
    """List all versions of a document."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        versions = await repo.list_versions(document_id)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")


@router.post("/documents/{document_id}/versions/{version_number}/restore", response_model=DocumentIR)
async def restore_version(document_id: str, version_number: int):
    """Restore a document to a specific version."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        document = await repo.restore_version(document_id, version_number)
        return document
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore version: {str(e)}")


@router.post("/documents/{document_id}/export")
async def export_document(document_id: str, format: str):
    """Export a document to specified format."""
    try:
        db = await get_database()
        repo = DocumentRepository(db)
        
        document = await repo.get_by_id(document_id)
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
