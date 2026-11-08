"""HTML exporter."""
from typing import List
from html import escape

from app.models.document_ir import DocumentIR, Section, InlineContent
from .base import Exporter


class HTMLExporter(Exporter):
    """Export documents to HTML format."""
    
    @property
    def format_name(self) -> str:
        return "html"
    
    @property
    def mime_type(self) -> str:
        return "text/html"
    
    @property
    def file_extension(self) -> str:
        return ".html"
    
    def export(self, document: DocumentIR) -> bytes:
        """Export DocumentIR to HTML."""
        html = f"""<!DOCTYPE html>
<html lang="{document.metadata.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(document.title)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 0.5rem; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 0.3rem; margin-top: 2rem; }}
        h3 {{ color: #34495e; margin-top: 1.5rem; }}
        h4, h5, h6 {{ color: #555; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
        pre {{ background-color: #f4f4f4; padding: 1rem; border-radius: 5px; overflow-x: auto; }}
        pre code {{ background: none; padding: 0; }}
        blockquote {{ border-left: 4px solid #3498db; padding-left: 1rem; margin-left: 0; color: #555; font-style: italic; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #ddd; padding: 0.75rem; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        a {{ color: #3498db; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .metadata {{ color: #777; font-size: 0.9rem; margin-bottom: 2rem; }}
        figure {{ margin: 1rem 0; }}
        figure.align-center {{ text-align: center; }}
        figure.align-right {{ text-align: right; }}
        figcaption {{ font-size: 0.9rem; color: #666; font-style: italic; margin-top: 0.5rem; }}
        img {{ max-width: 100%; height: auto; }}
        @media print {{
            [style*="page-break-after: always"] {{ page-break-after: always; }}
        }}
    </style>
</head>
<body>
    <h1>{escape(document.title)}</h1>
"""
        
        # Metadata
        if document.metadata.author:
            html += f'    <div class="metadata">Author: {escape(document.metadata.author)}</div>\n'
        
        # Content sections
        for section in document.content:
            html += self._format_section(section)
        
        html += """
</body>
</html>"""
        
        return html.encode("utf-8")
    
    def _format_section(self, section: Section) -> str:
        """Format a section to HTML."""
        html = f"    <h{section.level}>{escape(section.title)}</h{section.level}>\n"
        
        for block in section.blocks:
            if block.type == "paragraph":
                html += f"    <p>{self._format_inline_content(block.content)}</p>\n"
            
            elif block.type == "heading":
                html += f"    <h{block.level}>{self._format_inline_content(block.content)}</h{block.level}>\n"
            
            elif block.type == "list":
                tag = "ol" if block.ordered else "ul"
                html += f"    <{tag}>\n"
                for item in block.items:
                    html += f"        <li>{self._format_inline_content(item)}</li>\n"
                html += f"    </{tag}>\n"
            
            elif block.type == "quote":
                html += "    <blockquote>\n"
                html += f"        <p>{self._format_inline_content(block.content)}</p>\n"
                if block.attribution:
                    html += f"        <footer>— {escape(block.attribution)}</footer>\n"
                html += "    </blockquote>\n"
            
            elif block.type == "code_block":
                lang = escape(block.language) if block.language else ""
                html += f"    <pre><code class='language-{lang}'>{escape(block.code)}</code></pre>\n"
            
            elif block.type == "table":
                html += "    <table>\n"
                if block.headers:
                    html += "        <thead><tr>\n"
                    for header in block.headers:
                        html += f"            <th>{escape(header)}</th>\n"
                    html += "        </tr></thead>\n"
                html += "        <tbody>\n"
                for row in block.rows:
                    html += "            <tr>\n"
                    for cell in row:
                        html += f"                <td>{escape(cell)}</td>\n"
                    html += "            </tr>\n"
                html += "        </tbody>\n"
                html += "    </table>\n"
            
            elif block.type == "image":
                # Image tag with optional styling
                style_parts = []
                if block.width:
                    style_parts.append(f"width: {block.width}px")
                if block.height:
                    style_parts.append(f"height: {block.height}px")
                
                style_attr = f' style="{"; ".join(style_parts)}"' if style_parts else ''
                alt_text = escape(block.alt_text or block.caption or "Image")
                
                # Alignment
                align_class = f' class="align-{block.alignment}"' if block.alignment else ''
                
                html += f'    <figure{align_class}>\n'
                html += f'        <img src="{escape(block.url)}" alt="{alt_text}"{style_attr}>\n'
                if block.caption:
                    html += f'        <figcaption>{escape(block.caption)}</figcaption>\n'
                html += '    </figure>\n'
            
            elif block.type == "page_break":
                # Page break for print media
                html += '    <div style="page-break-after: always;"></div>\n'
        
        return html
    
    def _format_inline_content(self, content: List[InlineContent]) -> str:
        """Format inline content with HTML tags."""
        result = []
        for item in content:
            text = escape(item.text)
            
            # Build inline styles
            style_parts = []
            if item.color:
                style_parts.append(f"color: {item.color}")
            if item.background_color:
                style_parts.append(f"background-color: {item.background_color}")
            if item.font_size:
                style_parts.append(f"font-size: {item.font_size}px")
            if item.font_family:
                style_parts.append(f"font-family: {item.font_family}")
            
            # Wrap in span with styles if needed
            if style_parts:
                style_attr = "; ".join(style_parts)
                text = f'<span style="{style_attr}">{text}</span>'
            
            # Apply text formatting
            if item.bold:
                text = f"<strong>{text}</strong>"
            if item.italic:
                text = f"<em>{text}</em>"
            if item.underline:
                text = f"<u>{text}</u>"
            if item.strikethrough:
                text = f"<s>{text}</s>"
            if item.link:
                text = f'<a href="{escape(item.link)}">{text}</a>'
            
            result.append(text)
        
        return "".join(result)
