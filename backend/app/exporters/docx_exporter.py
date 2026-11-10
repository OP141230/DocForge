"""DOCX exporter using python-docx."""
from io import BytesIO
from typing import List, Optional
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from app.models.document_ir import DocumentIR, Section, InlineContent, PageLayout
from .base import Exporter


class DOCXExporter(Exporter):
    """Export documents to Microsoft Word format."""
    
    @property
    def format_name(self) -> str:
        return "docx"
    
    @property
    def mime_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    @property
    def file_extension(self) -> str:
        return ".docx"
    
    def export(self, document: DocumentIR) -> bytes:
        """Export DocumentIR to DOCX."""
        doc = Document()
        
        # Apply page layout settings
        if document.metadata.page_layout:
            self._apply_page_layout(doc, document.metadata.page_layout)
        
        # Title
        title = doc.add_heading(document.title, level=0)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Metadata
        if document.metadata.author:
            author_para = doc.add_paragraph(f"Author: {document.metadata.author}")
            author_para.runs[0].font.italic = True
            author_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        doc.add_paragraph()  # Spacing
        
        # Content sections
        for section in document.content:
            self._format_section(doc, section)
        
        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _apply_page_layout(self, doc: Document, layout: PageLayout):
        """Apply page layout settings to document."""
        section = doc.sections[0]
        
        # Set page size
        if layout.page_size == "letter":
            section.page_width = Inches(8.5)
            section.page_height = Inches(11)
        elif layout.page_size == "a4":
            section.page_width = Inches(8.27)
            section.page_height = Inches(11.69)
        elif layout.page_size == "legal":
            section.page_width = Inches(8.5)
            section.page_height = Inches(14)
        
        # Handle orientation
        if layout.orientation == "landscape":
            # Swap width and height
            section.page_width, section.page_height = section.page_height, section.page_width
        
        # Set margins from individual fields
        section.top_margin = Inches(layout.margin_top)
        section.bottom_margin = Inches(layout.margin_bottom)
        section.left_margin = Inches(layout.margin_left)
        section.right_margin = Inches(layout.margin_right)
    
    def _format_section(self, doc: Document, section: Section):
        """Format a section in DOCX."""
        # Section heading
        doc.add_heading(section.title, level=section.level)
        
        # Blocks
        for block in section.blocks:
            if block.type == "paragraph":
                para = doc.add_paragraph()
                self._add_inline_content(para, block.content)
            
            elif block.type == "heading":
                heading = doc.add_heading(level=block.level)
                self._add_inline_content(heading, block.content)
            
            elif block.type == "list":
                for item in block.items:
                    para = doc.add_paragraph(style='List Bullet' if not block.ordered else 'List Number')
                    self._add_inline_content(para, item)
            
            elif block.type == "quote":
                para = doc.add_paragraph()
                para.paragraph_format.left_indent = Pt(36)
                para.paragraph_format.right_indent = Pt(36)
                self._add_inline_content(para, block.content)
                if para.runs:
                    para.runs[0].font.italic = True
                if block.attribution:
                    attr_para = doc.add_paragraph(f"— {block.attribution}")
                    attr_para.paragraph_format.left_indent = Pt(36)
                    attr_para.runs[0].font.italic = True
            
            elif block.type == "code_block":
                para = doc.add_paragraph(block.code, style='Normal')
                para.runs[0].font.name = 'Courier New'
                para.runs[0].font.size = Pt(10)
                para.paragraph_format.left_indent = Pt(36)
                para.runs[0].font.color.rgb = RGBColor(0, 0, 0)
            
            elif block.type == "table":
                rows = len(block.rows) + (1 if block.headers else 0)
                cols = len(block.headers) if block.headers else (len(block.rows[0]) if block.rows else 1)
                table = doc.add_table(rows=rows, cols=cols)
                table.style = 'Light Grid Accent 1'
                
                row_idx = 0
                if block.headers:
                    for col_idx, header in enumerate(block.headers):
                        cell = table.rows[row_idx].cells[col_idx]
                        cell.text = header
                        # Make header bold
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.font.bold = True
                    row_idx += 1
                
                for data_row in block.rows:
                    for col_idx, cell_text in enumerate(data_row):
                        table.rows[row_idx].cells[col_idx].text = cell_text
                    row_idx += 1
            
            elif block.type == "image":
                # Handle image block
                try:
                    # Resolve image path
                    image_path = self._resolve_image_path(block.url)
                    
                    # Add image
                    if block.width:
                        img = doc.add_picture(image_path, width=Inches(block.width / 96))  # Assuming 96 DPI
                    else:
                        img = doc.add_picture(image_path)
                    
                    # Set alignment
                    last_paragraph = doc.paragraphs[-1]
                    if block.alignment == "center":
                        last_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                    elif block.alignment == "right":
                        last_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
                    else:
                        last_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
                    
                    # Add caption if present
                    if block.caption:
                        caption_para = doc.add_paragraph(block.caption)
                        caption_para.runs[0].font.size = Pt(9)
                        caption_para.runs[0].font.italic = True
                        caption_para.runs[0].font.color.rgb = RGBColor(128, 128, 128)
                        caption_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                
                except Exception as e:
                    # If image fails, add error message
                    error_para = doc.add_paragraph(f"[Image failed to load: {block.url}]")
                    error_para.runs[0].font.color.rgb = RGBColor(255, 0, 0)
            
            elif block.type == "page_break":
                # Add page break
                doc.add_page_break()
            
            elif block.type == "math_equation":
                # Convert LaTeX to Unicode for better rendering
                # Import here to avoid circular dependencies
                from .pdf_exporter import latex_to_unicode
                
                try:
                    # Convert LaTeX equation to Unicode
                    unicode_equation = latex_to_unicode(block.equation)
                    
                    para = doc.add_paragraph()
                    
                    # Add equation label if present
                    if block.label:
                        label_run = para.add_run(f"[{block.label}] ")
                        label_run.font.size = Pt(9)
                        label_run.font.color.rgb = RGBColor(128, 128, 128)
                    
                    # Add the equation itself (now in Unicode)
                    eq_run = para.add_run(unicode_equation)
                    eq_run.font.name = 'Cambria Math'
                    eq_run.font.size = Pt(11)
                    
                    # Center if display mode
                    if block.display_mode:
                        para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                        # Add some spacing
                        para.paragraph_format.space_before = Pt(6)
                        para.paragraph_format.space_after = Pt(6)
                    
                    # Add visual distinction
                    para.paragraph_format.left_indent = Pt(18)
                    para.paragraph_format.right_indent = Pt(18)
                    
                except Exception as e:
                    # Fallback: render as plain text if conversion fails
                    para = doc.add_paragraph()
                    if block.label:
                        label_run = para.add_run(f"[{block.label}] ")
                        label_run.font.size = Pt(9)
                        label_run.font.color.rgb = RGBColor(128, 128, 128)
                    
                    eq_run = para.add_run(block.equation)
                    eq_run.font.name = 'Courier New'
                    eq_run.font.size = Pt(10)
                    
                    if block.display_mode:
                        para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            elif block.type == "diagram":
                # Render diagram description
                # Word doesn't support Mermaid directly, so we'll add a formatted text representation
                
                # Add diagram title
                title_para = doc.add_paragraph()
                title_run = title_para.add_run(f"[{block.diagram_type.title()} Diagram]")
                title_run.font.bold = True
                title_run.font.size = Pt(11)
                title_run.font.color.rgb = RGBColor(44, 62, 80)
                
                # Add the Mermaid code in a formatted block
                code_para = doc.add_paragraph(block.mermaid_code)
                code_para.runs[0].font.name = 'Courier New'
                code_para.runs[0].font.size = Pt(9)
                code_para.paragraph_format.left_indent = Pt(36)
                code_para.paragraph_format.space_before = Pt(6)
                code_para.paragraph_format.space_after = Pt(6)
                
                # Add shading/background
                from docx.oxml.shared import OxmlElement
                from docx.oxml.ns import qn
                shading_elm = OxmlElement('w:shd')
                shading_elm.set(qn('w:fill'), 'F0F8FF')
                code_para._element.get_or_add_pPr().append(shading_elm)
                
                # Add caption if present
                if block.caption:
                    caption_para = doc.add_paragraph(block.caption)
                    caption_para.runs[0].font.size = Pt(9)
                    caption_para.runs[0].font.italic = True
                    caption_para.runs[0].font.color.rgb = RGBColor(128, 128, 128)
                    caption_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    
    def _resolve_image_path(self, url: str) -> str:
        """Resolve image URL to local file path."""
        # If it's already a local file path
        if Path(url).exists():
            return url
        
        # If it's an API URL like /api/images/{id}
        if url.startswith("/api/images/"):
            image_id = url.split("/")[-1]
            # Look in uploads directory
            uploads_dir = Path("uploads/images")
            for ext in ["png", "jpg", "jpeg", "gif", "webp", "bmp"]:
                image_path = uploads_dir / f"{image_id}.{ext}"
                if image_path.exists():
                    return str(image_path)
        
        # Otherwise return as-is
        return url
    
    def _add_inline_content(self, paragraph, content: List[InlineContent]):
        """Add inline content to a paragraph with formatting."""
        # Import here to avoid circular dependencies
        from .pdf_exporter import parse_inline_latex
        
        for item in content:
            # Parse and convert inline LaTeX expressions
            text = parse_inline_latex(item.text)
            run = paragraph.add_run(text)
            
            # Basic formatting
            if item.bold:
                run.font.bold = True
            if item.italic:
                run.font.italic = True
            if item.underline:
                run.font.underline = True
            
            # Strike through
            if item.strikethrough:
                run.font.strike = True
            
            # Text color
            if item.color:
                try:
                    color_hex = item.color.lstrip('#')
                    r = int(color_hex[0:2], 16)
                    g = int(color_hex[2:4], 16)
                    b = int(color_hex[4:6], 16)
                    run.font.color.rgb = RGBColor(r, g, b)
                except:
                    pass  # Skip invalid colors
            
            # Background color (highlight)
            if item.background_color:
                try:
                    # python-docx supports limited highlight colors
                    # We'll skip this or use shading if needed
                    pass
                except:
                    pass
            
            # Font size
            if item.font_size:
                run.font.size = Pt(item.font_size)
            
            # Font family
            if item.font_family:
                run.font.name = item.font_family
            
            # Links
            if item.link:
                # Simple hyperlink representation (python-docx hyperlinks are complex)
                link_run = paragraph.add_run(f" ({item.link})")
                link_run.font.color.rgb = RGBColor(0, 0, 255)
                link_run.font.underline = True
