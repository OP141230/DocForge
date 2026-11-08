"""Document Intermediate Representation (IR) - Canonical document model."""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal, Union
from uuid import uuid4
from pydantic import BaseModel, Field


class PageLayout(BaseModel):
    """Page layout configuration."""
    page_size: str = "A4"  # A4, Letter, Legal, A3
    orientation: str = "portrait"  # portrait, landscape
    margin_top: float = 1.0  # inches
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    page_numbers: bool = True
    page_number_position: str = "bottom-center"  # bottom-center, bottom-right, etc.


class DocumentMetadata(BaseModel):
    """Document metadata."""
    author: Optional[str] = None
    document_type: str  # 'general_report', 'academic_report', etc.
    audience: Optional[str] = None
    tone: Optional[str] = None
    language: str = "en"
    template_id: Optional[str] = None  # Reference to template used
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    page_layout: PageLayout = Field(default_factory=PageLayout)


class InlineContent(BaseModel):
    """Inline text with formatting."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    link: Optional[str] = None  # URL if this is a link
    color: Optional[str] = None  # Text color (hex, e.g., "#FF0000")
    background_color: Optional[str] = None  # Highlight color
    font_size: Optional[int] = None  # Font size in points
    font_family: Optional[str] = None  # Font family name


class Block(BaseModel):
    """Base block type."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str


class Paragraph(Block):
    """Paragraph block."""
    type: Literal["paragraph"] = "paragraph"
    content: List[InlineContent]


class Heading(Block):
    """Heading block."""
    type: Literal["heading"] = "heading"
    level: int = Field(ge=1, le=6)
    content: List[InlineContent]


class ListBlock(Block):
    """List block (ordered or unordered)."""
    type: Literal["list"] = "list"
    ordered: bool
    items: List[List[InlineContent]]


class Quote(Block):
    """Quote block."""
    type: Literal["quote"] = "quote"
    content: List[InlineContent]
    attribution: Optional[str] = None


class CodeBlock(Block):
    """Code block with optional syntax highlighting."""
    type: Literal["code_block"] = "code_block"
    language: Optional[str] = None
    code: str


class Table(Block):
    """Table block."""
    type: Literal["table"] = "table"
    headers: Optional[List[str]] = None
    rows: List[List[str]]
    caption: Optional[str] = None  # Table caption
    alignment: Optional[List[str]] = None  # Column alignments: left, center, right


class Image(Block):
    """Image block."""
    type: Literal["image"] = "image"
    url: str  # URL or data URL or storage path
    alt_text: Optional[str] = None  # Alternative text for accessibility
    caption: Optional[str] = None  # Image caption
    width: Optional[int] = None  # Width in pixels or percentage
    height: Optional[int] = None  # Height in pixels
    alignment: Optional[str] = "center"  # left, center, right


class PageBreak(Block):
    """Page break marker."""
    type: Literal["page_break"] = "page_break"


# Union of all block types for validation
BlockType = Union[Paragraph, Heading, ListBlock, Quote, CodeBlock, Table, Image, PageBreak]


class Section(BaseModel):
    """Document section with heading and content blocks."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: Literal["section"] = "section"
    level: int = Field(ge=1, le=6)  # Heading level
    title: str
    blocks: List[BlockType]


class DocumentIR(BaseModel):
    """Complete document in intermediate representation."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    content: List[Section]
    metadata: DocumentMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.1.0"  # Updated for Phase 7: images, page layout, advanced formatting
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
