"""DOCX exporter using python-docx."""
from io import BytesIO
from typing import List

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

from app.models.document_ir import DocumentIR, Section, InlineContent
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
                # Light gray background effect (not perfect but reasonable)
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
    
    def _add_inline_content(self, paragraph, content: List[InlineContent]):
        """Add inline content to a paragraph with formatting."""
        for item in content:
            run = paragraph.add_run(item.text)
            
            if item.bold:
                run.font.bold = True
            if item.italic:
                run.font.italic = True
            if item.underline:
                run.font.underline = True
            if item.link:
                # Simple hyperlink representation (python-docx hyperlinks are complex)
                link_run = paragraph.add_run(f" ({item.link})")
                link_run.font.color.rgb = RGBColor(0, 0, 255)
                link_run.font.underline = True
