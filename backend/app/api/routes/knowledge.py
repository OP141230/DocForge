"""Knowledge base API endpoints."""
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query, Form
from fastapi.responses import StreamingResponse
import io

from app.models.auth import User
from app.models.knowledge import (
    KnowledgeFile,
    FileUploadResponse,
    FileListResponse,
    ExtractedContent,
    SearchResponse,
    SearchResult,
)
from app.core.auth import get_current_user
from app.core.database import get_database, Database
from app.repositories.knowledge_file_repository import KnowledgeFileRepository
from app.repositories.extracted_content_repository import ExtractedContentRepository
from app.repositories.content_chunk_repository import ContentChunkRepository
from app.repositories.brief_attachment_repository import BriefAttachmentRepository
from app.repositories.document_brief_repository import DocumentBriefRepository
from app.services.storage_service import get_storage_service
from app.services.extraction_service import get_extraction_service
from app.services.chunking_service import get_chunking_service
from app.services.retrieval_service import get_retrieval_service

logger = logging.getLogger(__name__)

router = APIRouter()


def get_allowed_extensions() -> set[str]:
    """Get allowed file extensions from environment."""
    extensions_str = os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "pdf,docx,txt,md,html,csv")
    return {ext.strip().lower() for ext in extensions_str.split(",")}


def get_max_file_size_bytes() -> int:
    """Get max file size from environment in bytes."""
    max_mb = int(os.getenv("UPLOAD_MAX_SIZE_MB", "50"))
    return max_mb * 1024 * 1024


def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check filename
    if not file.filename:
        return False, "No filename provided"
    
    # Extract extension
    file_extension = Path(file.filename).suffix.lower().lstrip('.')
    
    # Check extension
    allowed_extensions = get_allowed_extensions()
    if file_extension not in allowed_extensions:
        return False, f"File type .{file_extension} not supported. Allowed: {', '.join(f'.{ext}' for ext in allowed_extensions)}"
    
    # Check size (if available)
    if file.size:
        max_size = get_max_file_size_bytes()
        if file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb:.0f}MB"
    
    return True, None


@router.post("/knowledge/files", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    Upload a knowledge base file.
    
    Supported formats: PDF, DOCX, TXT, MD, HTML, CSV
    Maximum file size: 50MB (configurable)
    
    Security:
    - User must be authenticated
    - Files are stored in user-specific directories
    - Filenames are sanitized to prevent path traversal
    - Content hash enables deduplication
    """
    try:
        # Validate file
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Read file data
        file_data = await file.read()
        
        # Check if empty
        if len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file not allowed")
        
        # Check size
        max_size = get_max_file_size_bytes()
        if len(file_data) > max_size:
            max_mb = max_size / (1024 * 1024)
            raise HTTPException(status_code=400, detail=f"File too large. Maximum size: {max_mb:.0f}MB")
        
        # Get storage service
        storage = get_storage_service()
        
        # Save file to storage
        stored_filename, storage_path, content_hash = await storage.save_file(
            file_data,
            current_user.id,
            file.filename
        )
        
        # Check for duplicate (same hash for same user)
        repo = KnowledgeFileRepository(db)
        existing_file = await repo.get_by_hash(content_hash, current_user.id)
        
        if existing_file:
            # Return existing file instead of creating duplicate
            return FileUploadResponse(
                file_id=existing_file.id,
                original_filename=existing_file.original_filename,
                file_size_bytes=existing_file.file_size_bytes,
                upload_status=existing_file.upload_status,
                extraction_status=existing_file.extraction_status
            )
        
        # Extract extension and MIME type
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        mime_type = file.content_type
        
        # Create database record
        knowledge_file = KnowledgeFile(
            user_id=current_user.id,
            conversation_id=conversation_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_extension=file_extension,
            mime_type=mime_type,
            file_size_bytes=len(file_data),
            content_hash=content_hash,
            storage_path=storage_path,
            upload_status="uploaded",
            extraction_status="pending"
        )
        
        await repo.create(knowledge_file)
        
        # TODO: Trigger extraction in background (Sprint 2)
        
        return FileUploadResponse(
            file_id=knowledge_file.id,
            original_filename=knowledge_file.original_filename,
            file_size_bytes=knowledge_file.file_size_bytes,
            upload_status=knowledge_file.upload_status,
            extraction_status=knowledge_file.extraction_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/knowledge/files", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    conversation_id: Optional[str] = Query(None),
    file_extension: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    List user's knowledge base files with pagination.
    
    Filters:
    - conversation_id: Show only files from specific conversation
    - file_extension: Show only files of specific type (pdf, docx, etc.)
    """
    try:
        repo = KnowledgeFileRepository(db)
        
        offset = (page - 1) * page_size
        
        files, total = await repo.list_by_user(
            user_id=current_user.id,
            limit=page_size,
            offset=offset,
            conversation_id=conversation_id,
            file_extension=file_extension
        )
        
        return FileListResponse(
            files=files,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/knowledge/files/{file_id}")
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """Get file metadata by ID."""
    try:
        repo = KnowledgeFileRepository(db)
        file = await repo.get_by_id(file_id, current_user.id)
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        return file
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")


@router.delete("/knowledge/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    Delete a file and clean up storage.
    
    This deletes:
    - File metadata from database
    - Physical file from storage
    - Extracted content
    - Content chunks
    - All attachments
    
    (Cascading deletes handled by foreign key constraints)
    """
    try:
        repo = KnowledgeFileRepository(db)
        
        # Get file first
        file = await repo.get_by_id(file_id, current_user.id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete from storage
        storage = get_storage_service()
        await storage.delete_file(file.storage_path)
        
        # Delete from database (cascades to content, chunks, attachments)
        await repo.delete(file_id, current_user.id)
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/knowledge/files/{file_id}/status")
async def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    Get current processing status of a file.
    
    Useful for polling during extraction.
    """
    try:
        repo = KnowledgeFileRepository(db)
        file = await repo.get_by_id(file_id, current_user.id)
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "file_id": file.id,
            "upload_status": file.upload_status,
            "extraction_status": file.extraction_status,
            "extraction_error": file.extraction_error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/knowledge/files/{file_id}/extract-and-chunk")
async def extract_and_chunk_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    Extract text from a file and chunk it for search.
    
    This endpoint:
    1. Retrieves the file from storage
    2. Extracts text content using the appropriate extractor
    3. Saves extracted content to database
    4. Chunks the content with overlap
    5. Saves chunks to database (indexed in FTS5)
    6. Updates file extraction status
    
    Security:
    - User must be authenticated
    - Only file owner can trigger extraction
    """
    try:
        file_repo = KnowledgeFileRepository(db)
        content_repo = ExtractedContentRepository(db)
        chunk_repo = ContentChunkRepository(db)
        
        # Get file
        file = await file_repo.get_by_id(file_id, current_user.id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if already extracted
        existing_content = await content_repo.get_by_file_id(file_id, current_user.id)
        if existing_content:
            return {
                "message": "File already extracted",
                "content_id": existing_content.id,
                "word_count": existing_content.word_count,
                "chunk_count": len(await chunk_repo.get_by_content_id(file_id, current_user.id))
            }
        
        # Update status to processing
        await file_repo.update_status(
            file_id,
            current_user.id,
            extraction_status="processing"
        )
        
        try:
            # Get file data from storage
            storage = get_storage_service()
            file_data = await storage.get_file(file.storage_path)
            
            # Extract text
            extraction_service = get_extraction_service()
            extraction_result = await extraction_service.extract(file_data, file.file_extension)
            
            # Create extracted content record
            extracted_content = ExtractedContent(
                file_id=file_id,
                user_id=current_user.id,
                raw_text=extraction_result.text,
                page_count=extraction_result.page_count,
                word_count=extraction_result.word_count,
                extraction_metadata=extraction_result.metadata
            )
            
            await content_repo.create(extracted_content)
            
            # Chunk the content
            chunking_service = get_chunking_service()
            chunks = chunking_service.chunk_content(extracted_content)
            
            # Save chunks
            for chunk in chunks:
                await chunk_repo.create(chunk)
            
            # Update status to completed
            await file_repo.update_status(
                file_id,
                current_user.id,
                extraction_status="completed"
            )
            
            logger.info(f"Extracted and chunked file {file_id}: {len(chunks)} chunks created")
            
            return {
                "message": "File extracted and chunked successfully",
                "content_id": extracted_content.id,
                "word_count": extracted_content.word_count,
                "page_count": extracted_content.page_count,
                "chunk_count": len(chunks)
            }
            
        except Exception as extraction_error:
            # Update status to failed
            await file_repo.update_status(
                file_id,
                current_user.id,
                extraction_status="failed",
                extraction_error=str(extraction_error)
            )
            
            logger.error(f"Extraction failed for file {file_id}: {extraction_error}")
            raise HTTPException(status_code=500, detail=f"Extraction failed: {str(extraction_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract and chunk failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract and chunk: {str(e)}")


@router.get("/knowledge/search", response_model=SearchResponse)
async def search_knowledge(
    q: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    Search knowledge base using full-text search.
    
    Uses FTS5 (SQLite Full-Text Search) with BM25 ranking algorithm
    to find the most relevant chunks of content.
    
    Returns top N chunks with source metadata (filename, page, section).
    
    Security:
    - User must be authenticated
    - Search is scoped to user's own files only
    """
    try:
        if not q or not q.strip():
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
        
        # Search using retrieval service
        retrieval_service = get_retrieval_service(db)
        results = await retrieval_service.search(q, current_user.id, limit)
        
        # Convert to response model
        search_results = [
            SearchResult(
                chunk_id=r['chunk_id'],
                file_id=r['file_id'],
                original_filename=r['original_filename'],
                chunk_text=r['chunk_text'],
                page_number=r['page_number'],
                section_title=r['section_title'],
                relevance_score=r['relevance_score']
            )
            for r in results
        ]
        
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            query=q
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/knowledge/files/{file_id}/content")
async def get_file_content(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    Get extracted text content for a file.
    
    Returns the full extracted text and metadata.
    
    Security:
    - User must be authenticated
    - Only file owner can view content
    """
    try:
        file_repo = KnowledgeFileRepository(db)
        content_repo = ExtractedContentRepository(db)
        
        # Verify file ownership
        file = await file_repo.get_by_id(file_id, current_user.id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get extracted content
        content = await content_repo.get_by_file_id(file_id, current_user.id)
        if not content:
            raise HTTPException(
                status_code=404,
                detail="Content not extracted yet. Use /extract-and-chunk endpoint first."
            )
        
        return {
            "content_id": content.id,
            "file_id": content.file_id,
            "raw_text": content.raw_text,
            "word_count": content.word_count,
            "page_count": content.page_count,
            "extraction_metadata": content.extraction_metadata,
            "created_at": content.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get content failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get content: {str(e)}")


@router.post("/document-briefs/{brief_id}/attachments")
async def attach_file_to_brief(
    brief_id: str,
    file_id: str = Query(..., description="Knowledge file ID to attach"),
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    Attach a knowledge file to a document brief.
    
    This links an uploaded file to a brief so the file's content
    can be used as source material during document generation.
    
    Security:
    - User must be authenticated
    - User must own both the brief and the file
    - Duplicate attachments are prevented
    """
    try:
        brief_repo = DocumentBriefRepository(db)
        file_repo = KnowledgeFileRepository(db)
        attachment_repo = BriefAttachmentRepository(db)
        
        # Verify brief ownership
        brief = await brief_repo.get_by_id(brief_id, current_user.id)
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        # Verify file ownership
        file = await file_repo.get_by_id(file_id, current_user.id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if file extraction completed
        if file.extraction_status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"File extraction not completed. Current status: {file.extraction_status}"
            )
        
        # Check if already attached
        exists = await attachment_repo.exists(brief_id, file_id, current_user.id)
        if exists:
            raise HTTPException(status_code=400, detail="File already attached to this brief")
        
        # Create attachment
        attachment_id = await attachment_repo.create(brief_id, file_id, current_user.id)
        
        return {
            "attachment_id": attachment_id,
            "brief_id": brief_id,
            "file_id": file_id,
            "message": "File attached successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attach file failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to attach file: {str(e)}")


@router.get("/document-briefs/{brief_id}/attachments")
async def list_brief_attachments(
    brief_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    List all files attached to a document brief.
    
    Returns file metadata for all attached knowledge files.
    
    Security:
    - User must be authenticated
    - User must own the brief
    """
    try:
        brief_repo = DocumentBriefRepository(db)
        attachment_repo = BriefAttachmentRepository(db)
        
        # Verify brief ownership
        brief = await brief_repo.get_by_id(brief_id, current_user.id)
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        # Get attached files
        files = await attachment_repo.get_by_brief_id(brief_id, current_user.id)
        
        return {
            "brief_id": brief_id,
            "files": files,
            "total": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List attachments failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list attachments: {str(e)}")


@router.delete("/document-briefs/{brief_id}/attachments/{file_id}")
async def remove_attachment(
    brief_id: str,
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Database = Depends(get_database)
):
    """
    Remove a file attachment from a document brief.
    
    This only removes the link between the brief and file.
    The file itself remains in the knowledge base.
    
    Security:
    - User must be authenticated
    - User must own the brief
    """
    try:
        brief_repo = DocumentBriefRepository(db)
        attachment_repo = BriefAttachmentRepository(db)
        
        # Verify brief ownership
        brief = await brief_repo.get_by_id(brief_id, current_user.id)
        if not brief:
            raise HTTPException(status_code=404, detail="Document brief not found")
        
        # Delete attachment
        deleted = await attachment_repo.delete(brief_id, file_id, current_user.id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        return {"message": "Attachment removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove attachment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove attachment: {str(e)}")
