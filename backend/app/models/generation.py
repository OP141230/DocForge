"""Generation request and response models."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentRequirements(BaseModel):
    """Requirements for document generation."""
    document_type: str  # 'general_report', 'academic_report', 'project_report', etc.
    topic: str
    title: str
    audience: Optional[str] = None
    tone: Optional[str] = "professional"
    language: str = "en"
    length: str = "medium"  # 'short', 'medium', 'long'
    additional_instructions: Optional[str] = None


class OutlineItem(BaseModel):
    """Single item in document outline."""
    level: int = Field(ge=1, le=6)
    title: str


class OutlineResponse(BaseModel):
    """Response containing generated outline."""
    outline: List[OutlineItem]


class ContentGenerationRequest(BaseModel):
    """Request to generate full document content."""
    outline: List[OutlineItem]
    requirements: DocumentRequirements


class SectionGenerationRequest(BaseModel):
    """Request to generate or transform a single section."""
    section_title: str
    context: Dict[str, Any]  # Surrounding document context
    instruction: str  # 'expand', 'shorten', 'change_tone:casual', etc.
    requirements: Optional[DocumentRequirements] = None
