"""Plain text exporter."""
from typing import List

from app.models.document_ir import DocumentIR, Section, InlineContent
from .base import Exporter


class TextExporter(Exporter):
    """Export documents to plain text format."""
    
    @property
    def format_name(self) -> str:
        return "text"
    
    @property
    def mime_type(self) -> str:
        return "text/plain"
    
    @property
    def file_extension(self) -> str:
        return ".txt"
    
    @property
    def supports_formatting(self) -> dict:
        return {
            "headings": True,
            "lists": True,
            "tables": True,
            "formatting": False,  # No bold/italic in plain text
            "links": True,  # Show URL
            "code_blocks": True,
            "quotes": True,
        }
    
    def export(self, document: DocumentIR) -> bytes:
        """Export DocumentIR to plain text."""
        lines = []
        
        # Title
        lines.append(document.title.upper())
        lines.append("=" * len(document.title))
        lines.append("")
        
        # Metadata
        if document.metadata.author:
            lines.append(f"Author: {document.metadata.author}")
            lines.append("")
        
        # Content sections
        for section in document.content:
            lines.extend(self._format_section(section))
            lines.append("")
        
        text = "\n".join(lines)
        return text.encode("utf-8")
    
    def _format_section(self, section: Section) -> List[str]:
        """Format a section to plain text."""
        lines = []
        
        # Section heading with indentation
        indent = "  " * (section.level - 1)
        lines.append(f"{indent}{section.title}")
        lines.append(f"{indent}{'-' * len(section.title)}")
        lines.append("")
        
        # Blocks
        for block in section.blocks:
            if block.type == "paragraph":
                lines.append(self._format_inline_content(block.content))
                lines.append("")
            
            elif block.type == "heading":
                lines.append(self._format_inline_content(block.content))
                lines.append("")
            
            elif block.type == "list":
                for i, item in enumerate(block.items):
                    if block.ordered:
                        lines.append(f"  {i + 1}. {self._format_inline_content(item)}")
                    else:
                        lines.append(f"  • {self._format_inline_content(item)}")
                lines.append("")
            
            elif block.type == "quote":
                quote_text = self._format_inline_content(block.content)
                for line in quote_text.split("\n"):
                    lines.append(f"  | {line}")
                if block.attribution:
                    lines.append(f"  | — {block.attribution}")
                lines.append("")
            
            elif block.type == "code_block":
                lines.append("  [Code]")
                for line in block.code.split("\n"):
                    lines.append(f"  {line}")
                lines.append("")
            
            elif block.type == "table":
                # Simple table representation
                if block.headers:
                    lines.append("  | " + " | ".join(block.headers) + " |")
                    lines.append("  " + "-" * (sum(len(h) for h in block.headers) + len(block.headers) * 3 + 1))
                for row in block.rows:
                    lines.append("  | " + " | ".join(row) + " |")
                lines.append("")
        
        return lines
    
    def _format_inline_content(self, content: List[InlineContent]) -> str:
        """Format inline content as plain text."""
        result = []
        for item in content:
            text = item.text
            if item.link:
                text = f"{text} ({item.link})"
            result.append(text)
        return "".join(result)
