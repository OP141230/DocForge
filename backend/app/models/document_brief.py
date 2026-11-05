"""DocumentBrief model - represents user's requirements for document generation."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field


class OutlineItem(BaseModel):
    """Single item in document outline."""
    level: int = Field(ge=1, le=6)
    title: str


class DocumentBrief(BaseModel):
    """Complete document brief - what the user wants to create."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    conversation_id: Optional[str] = None
    
    # Core document definition
    document_type: str = Field(description="Type of document: general_report, academic_report, etc.")
    title: str = Field(description="Document title")
    topic: str = Field(description="Main topic or subject")
    purpose: Optional[str] = Field(None, description="Purpose of the document")
    audience: Optional[str] = Field(None, description="Target audience")
    language: str = Field(default="en", description="Document language code")
    desired_length: Optional[str] = Field(None, description="Desired length: short, medium, long, or specific page count")
    tone: Optional[str] = Field(None, description="Writing tone: formal, casual, technical, etc.")
    writing_style: Optional[str] = Field(None, description="Writing style preferences")
    
    # Additional requirements
    document_specific_data: Dict[str, Any] = Field(default_factory=dict, description="Document type-specific fields")
    required_sections: List[str] = Field(default_factory=list, description="Sections that must be included")
    important_points: List[str] = Field(default_factory=list, description="Key points to cover")
    topics_to_avoid: List[str] = Field(default_factory=list, description="Topics to exclude")
    additional_instructions: Optional[str] = Field(None, description="Free-form additional instructions")
    citation_style: Optional[str] = Field(None, description="Citation style: APA, MLA, Chicago, etc.")
    
    # Outline and approval
    outline: Optional[List[OutlineItem]] = Field(None, description="Generated outline")
    outline_approved: bool = Field(default=False, description="Whether user approved the outline")
    outline_approved_at: Optional[datetime] = Field(None, description="When outline was approved")
    
    # Link to generated document
    document_id: Optional[str] = Field(None, description="ID of generated DocumentIR")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CreateBriefRequest(BaseModel):
    """Request to create a new document brief."""
    conversation_id: Optional[str] = None
    document_type: str
    title: str
    topic: str
    purpose: Optional[str] = None
    audience: Optional[str] = None
    language: str = "en"
    desired_length: Optional[str] = None
    tone: Optional[str] = None
    writing_style: Optional[str] = None
    document_specific_data: Dict[str, Any] = Field(default_factory=dict)
    required_sections: List[str] = Field(default_factory=list)
    important_points: List[str] = Field(default_factory=list)
    topics_to_avoid: List[str] = Field(default_factory=list)
    additional_instructions: Optional[str] = None
    citation_style: Optional[str] = None


class UpdateBriefRequest(BaseModel):
    """Request to update a document brief."""
    conversation_id: Optional[str] = None
    document_type: Optional[str] = None
    title: Optional[str] = None
    topic: Optional[str] = None
    purpose: Optional[str] = None
    audience: Optional[str] = None
    language: Optional[str] = None
    desired_length: Optional[str] = None
    tone: Optional[str] = None
    writing_style: Optional[str] = None
    document_specific_data: Optional[Dict[str, Any]] = None
    required_sections: Optional[List[str]] = None
    important_points: Optional[List[str]] = None
    topics_to_avoid: Optional[List[str]] = None
    additional_instructions: Optional[str] = None
    citation_style: Optional[str] = None


class UpdateOutlineRequest(BaseModel):
    """Request to update the outline."""
    outline: List[OutlineItem]
