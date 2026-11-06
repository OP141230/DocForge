"""Knowledge base models for file uploads and extracted content."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
from pydantic import BaseModel, Field


class KnowledgeFile(BaseModel):
    """Uploaded file metadata."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    conversation_id: Optional[str] = None
    original_filename: str
    stored_filename: str
    file_extension: str
    mime_type: Optional[str] = None
    file_size_bytes: int
    content_hash: str
    storage_path: str
    upload_status: str = "uploaded"  # 'uploaded', 'processing', 'completed', 'failed'
    extraction_status: str = "pending"  # 'pending', 'processing', 'completed', 'failed'
    extraction_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExtractedContent(BaseModel):
    """Extracted text content from a file."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    file_id: str
    user_id: str
    raw_text: str
    page_count: Optional[int] = None
    word_count: int
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ContentChunk(BaseModel):
    """Searchable chunk of extracted content."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    file_id: str
    user_id: str
    chunk_index: int
    chunk_text: str
    chunk_size: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BriefFileAttachment(BaseModel):
    """Links a knowledge file to a document brief."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    brief_id: str
    file_id: str
    user_id: str
    attached_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request/Response models

class FileUploadResponse(BaseModel):
    """Response after file upload."""
    file_id: str
    original_filename: str
    file_size_bytes: int
    upload_status: str
    extraction_status: str


class FileListResponse(BaseModel):
    """Response for file list."""
    files: List[KnowledgeFile]
    total: int
    page: int
    page_size: int


class SearchResult(BaseModel):
    """Single search result with chunk and source metadata."""
    chunk_id: str
    file_id: str
    original_filename: str
    chunk_text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    relevance_score: float


class SearchResponse(BaseModel):
    """Response for knowledge base search."""
    results: List[SearchResult]
    total: int
    query: str


class AttachFilesRequest(BaseModel):
    """Request to attach files to a brief."""
    file_ids: List[str]
