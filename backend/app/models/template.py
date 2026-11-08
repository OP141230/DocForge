"""Document template models."""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4

from app.models.document_ir import PageLayout


class TemplateCategory(str, Enum):
    """Template categories."""
    ACADEMIC = "academic"
    TECHNICAL = "technical"
    BUSINESS = "business"
    DOCUMENTATION = "documentation"


class TypographyStyle(BaseModel):
    """Typography configuration."""
    font_family: str = "Arial"
    base_font_size: int = 12  # points
    heading_color: Optional[str] = None
    text_color: str = "#000000"
    line_spacing: float = 1.15
    paragraph_spacing: float = 0.5  # inches


class HeadingStyle(BaseModel):
    """Heading style configuration."""
    font_family: Optional[str] = None  # None = inherit from typography
    font_size: int = 16  # points
    color: Optional[str] = None
    bold: bool = True
    uppercase: bool = False
    spacing_before: float = 0.5  # inches
    spacing_after: float = 0.25  # inches


class DocumentTemplate(BaseModel):
    """Reusable document template."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    category: str  # academic, technical, business, project, documentation, general
    
    # Visual settings
    typography: TypographyStyle = Field(default_factory=TypographyStyle)
    heading_styles: Dict[int, HeadingStyle] = Field(default_factory=dict)  # keyed by level (1-6)
    page_layout: PageLayout = Field(default_factory=PageLayout)
    
    # Color palette
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    
    # Table styling
    table_header_background: str = "#F0F0F0"
    table_border_color: str = "#CCCCCC"
    
    # Figure styling
    figure_caption_style: str = "italic"  # normal, italic, bold
    
    # Citation style preference
    default_citation_style: str = "apa"  # apa, mla, chicago
    
    # Metadata
    is_system_template: bool = True  # False for user-created templates
    created_by: Optional[str] = None  # user_id if user-created
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TemplateListResponse(BaseModel):
    """List of templates."""
    templates: list[DocumentTemplate]
    total: int


class ApplyTemplateRequest(BaseModel):
    """Request to apply a template to a document."""
    template_id: str
    preserve_content: bool = True  # Always true, just for API clarity
