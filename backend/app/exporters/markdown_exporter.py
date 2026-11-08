"""Markdown exporter."""
from typing import List

from app.models.document_ir import DocumentIR, Section, Block, InlineContent
from .base import Exporter


class MarkdownExporter(Exporter):
    """Export documents to Markdown format."""
    
    @property
    def format_name(self) -> str:
        return "markdown"
    
    @property
    def mime_type(self) -> str:
        return "text/markdown"
    
    @property
    def file_extension(self) -> str:
        return ".md"
    
    def export(self, document: DocumentIR) -> bytes:
        """Export DocumentIR to Markdown."""
        lines = []
        
        # Title
        lines.append(f"# {document.title}\n")
        
        # Metadata if present
        if document.metadata.author:
            lines.append(f"**Author:** {document.metadata.author}\n")
        
        lines.append("")
        
        # Content sections
        for section in document.content:
            lines.extend(self._format_section(section))
            lines.append("")
        
        markdown = "\n".join(lines)
        return markdown.encode("utf-8")
    
    def _format_section(self, section: Section) -> List[str]:
        """Format a section to Markdown."""
        lines = []
        
        # Section heading
        heading_prefix = "#" * section.level
        lines.append(f"{heading_prefix} {section.title}\n")
        
        # Blocks
        for block in section.blocks:
            if block.type == "paragraph":
                lines.append(self._format_inline_content(block.content) + "\n")
            
            elif block.type == "heading":
                heading_prefix = "#" * block.level
                lines.append(f"{heading_prefix} {self._format_inline_content(block.content)}\n")
            
            elif block.type == "list":
                for i, item in enumerate(block.items):
                    if block.ordered:
                        lines.append(f"{i + 1}. {self._format_inline_content(item)}")
                    else:
                        lines.append(f"- {self._format_inline_content(item)}")
                lines.append("")
            
            elif block.type == "quote":
                quote_text = self._format_inline_content(block.content)
                for line in quote_text.split("\n"):
                    lines.append(f"> {line}")
                if block.attribution:
                    lines.append(f">\n> — {block.attribution}")
                lines.append("")
            
            elif block.type == "code_block":
                lang = block.language or ""
                lines.append(f"```{lang}")
                lines.append(block.code)
                lines.append("```\n")
            
            elif block.type == "table":
                if block.headers:
                    lines.append("| " + " | ".join(block.headers) + " |")
                    lines.append("| " + " | ".join(["---"] * len(block.headers)) + " |")
                for row in block.rows:
                    lines.append("| " + " | ".join(row) + " |")
                lines.append("")
            
            elif block.type == "image":
                # Markdown image syntax
                alt_text = block.alt_text or block.caption or "Image"
                lines.append(f"![{alt_text}]({block.url})")
                if block.caption and block.caption != block.alt_text:
                    lines.append(f"*{block.caption}*")
                lines.append("")
            
            elif block.type == "page_break":
                # Markdown doesn't have page breaks, use horizontal rule
                lines.append("---\n")
        
        return lines
    
    def _format_inline_content(self, content: List[InlineContent]) -> str:
        """Format inline content with Markdown formatting."""
        result = []
        for item in content:
            text = item.text
            
            # Strikethrough
            if item.strikethrough:
                text = f"~~{text}~~"
            
            # Bold and italic
            if item.bold and item.italic:
                text = f"***{text}***"
            elif item.bold:
                text = f"**{text}**"
            elif item.italic:
                text = f"*{text}*"
            
            # Underline (not standard Markdown, but HTML works)
            if item.underline:
                text = f"<u>{text}</u>"
            
            # Color and font (use HTML for advanced formatting)
            if item.color or item.font_size or item.font_family or item.background_color:
                style_parts = []
                if item.color:
                    style_parts.append(f"color: {item.color}")
                if item.background_color:
                    style_parts.append(f"background-color: {item.background_color}")
                if item.font_size:
                    style_parts.append(f"font-size: {item.font_size}px")
                if item.font_family:
                    style_parts.append(f"font-family: {item.font_family}")
                
                style = "; ".join(style_parts)
                text = f'<span style="{style}">{text}</span>'
            
            # Links
            if item.link:
                text = f"[{text}]({item.link})"
            
            result.append(text)
        
        return "".join(result)
