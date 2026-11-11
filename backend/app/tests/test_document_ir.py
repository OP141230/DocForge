"""Test Document IR models."""
import pytest
from pydantic import ValidationError

from app.models.document_ir import (
    DocumentIR,
    DocumentMetadata,
    Section,
    Paragraph,
    InlineContent,
)


def test_document_ir_creation():
    """Test creating a valid DocumentIR."""
    metadata = DocumentMetadata(
        document_type="general_report",
        audience="engineers",
        tone="professional",
        language="en",
    )
    
    section = Section(
        level=1,
        title="Introduction",
        blocks=[
            Paragraph(content=[InlineContent(text="Hello, world!")])
        ],
    )
    
    doc = DocumentIR(
        title="Test Document",
        content=[section],
        metadata=metadata,
    )
    
    assert doc.title == "Test Document"
    assert len(doc.content) == 1
    assert doc.content[0].title == "Introduction"
    assert doc.schema_version == "1.1.0"  # Phase 7 updated to v1.1.0
    assert doc.id is not None


def test_inline_content_formatting():
    """Test inline content with formatting."""
    content = InlineContent(
        text="Bold text",
        bold=True,
        italic=False,
        link="https://example.com",
    )
    
    assert content.text == "Bold text"
    assert content.bold is True
    assert content.italic is False
    assert content.link == "https://example.com"


def test_section_validation():
    """Test section level validation."""
    # Valid section
    section = Section(level=1, title="Title", blocks=[])
    assert section.level == 1
    
    # Invalid level (too high)
    with pytest.raises(ValidationError):
        Section(level=7, title="Title", blocks=[])
    
    # Invalid level (too low)
    with pytest.raises(ValidationError):
        Section(level=0, title="Title", blocks=[])


def test_document_serialization():
    """Test document serialization and deserialization."""
    metadata = DocumentMetadata(document_type="article")
    section = Section(
        level=1,
        title="Test",
        blocks=[Paragraph(content=[InlineContent(text="Content")])],
    )
    
    doc = DocumentIR(title="Test", content=[section], metadata=metadata)
    
    # Serialize
    json_data = doc.model_dump_json()
    assert isinstance(json_data, str)
    
    # Deserialize
    doc_restored = DocumentIR.model_validate_json(json_data)
    assert doc_restored.title == doc.title
    assert doc_restored.id == doc.id
