"""Exporter factory and initialization."""
from typing import Optional

from .base import Exporter
from .registry import ExporterRegistry
from .markdown_exporter import MarkdownExporter
from .html_exporter import HTMLExporter
from .text_exporter import TextExporter
from .docx_exporter import DOCXExporter
from .pdf_exporter import PDFExporter


# Initialize registry with all exporters
_registry = ExporterRegistry()
_registry.register(MarkdownExporter())
_registry.register(HTMLExporter())
_registry.register(TextExporter())
_registry.register(DOCXExporter())
_registry.register(PDFExporter())


def get_exporter(format_name: str) -> Optional[Exporter]:
    """Get an exporter by format name."""
    return _registry.get_exporter(format_name)


def list_formats():
    """List all available export formats."""
    return _registry.list_formats()


def get_capabilities(format_name: str):
    """Get capabilities of a specific format."""
    return _registry.get_capabilities(format_name)
