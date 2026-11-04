"""Document Intermediate Representation (IR) - Canonical document model."""
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal, Union
from uuid import uuid4
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document metadata."""
    author: Optional[str] = None
    document_type: str  # 'general_report', 'academic_report', etc.
    audience: Optional[str] = None
    tone: Optional[str] = None
    language: str = "en"
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class InlineContent(BaseModel):
    """Inline text with formatting."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    link: Optional[str] = None  # URL if this is a link


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


# Union of all block types for validation
BlockType = Union[Paragraph, Heading, ListBlock, Quote, CodeBlock, Table]


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
    schema_version: str = "1.0.0"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
