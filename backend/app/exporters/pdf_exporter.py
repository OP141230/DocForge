"""PDF exporter using ReportLab."""
from io import BytesIO
from typing import List

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.models.document_ir import DocumentIR, Section, InlineContent
from .base import Exporter


class PDFExporter(Exporter):
    """Export documents to PDF format."""
    
    @property
    def format_name(self) -> str:
        return "pdf"
    
    @property
    def mime_type(self) -> str:
        return "application/pdf"
    
    @property
    def file_extension(self) -> str:
        return ".pdf"
    
    def export(self, document: DocumentIR) -> bytes:
        """Export DocumentIR to PDF."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=inch, bottomMargin=inch)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        
        # Build story (content flow)
        story = []
        
        # Title
        story.append(Paragraph(document.title, title_style))
        
        # Metadata
        if document.metadata.author:
            author_style = ParagraphStyle('Author', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
            story.append(Paragraph(f"Author: {document.metadata.author}", author_style))
        
        story.append(Spacer(1, 0.5 * inch))
        
        # Content sections
        for section in document.content:
            story.extend(self._format_section(section, styles))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _format_section(self, section: Section, styles) -> List:
        """Format a section for PDF."""
        elements = []
        
        # Section heading
        heading_style = styles[f'Heading{min(section.level, 6)}']
        elements.append(Paragraph(section.title, heading_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Blocks
        for block in section.blocks:
            if block.type == "paragraph":
                text = self._format_inline_content(block.content)
                elements.append(Paragraph(text, styles['Normal']))
                elements.append(Spacer(1, 0.1 * inch))
            
            elif block.type == "heading":
                text = self._format_inline_content(block.content)
                heading_style = styles[f'Heading{min(block.level, 6)}']
                elements.append(Paragraph(text, heading_style))
                elements.append(Spacer(1, 0.1 * inch))
            
            elif block.type == "list":
                list_items = []
                for item in block.items:
                    text = self._format_inline_content(item)
                    list_items.append(ListItem(Paragraph(text, styles['Normal'])))
                
                flowable = ListFlowable(
                    list_items,
                    bulletType='1' if block.ordered else 'bullet',
                    start=1 if block.ordered else None,
                )
                elements.append(flowable)
                elements.append(Spacer(1, 0.1 * inch))
            
            elif block.type == "quote":
                text = self._format_inline_content(block.content)
                quote_style = ParagraphStyle(
                    'Quote',
                    parent=styles['Normal'],
                    leftIndent=0.5 * inch,
                    rightIndent=0.5 * inch,
                    textColor=colors.grey,
                    fontName='Times-Italic',
                )
                elements.append(Paragraph(text, quote_style))
                if block.attribution:
                    elements.append(Paragraph(f"— {block.attribution}", quote_style))
                elements.append(Spacer(1, 0.1 * inch))
            
            elif block.type == "code_block":
                code_style = ParagraphStyle(
                    'Code',
                    parent=styles['Code'],
                    leftIndent=0.5 * inch,
                    fontSize=9,
                    fontName='Courier',
                )
                # Preserve whitespace in code
                code_lines = block.code.split('\n')
                for line in code_lines:
                    elements.append(Paragraph(line or ' ', code_style))
                elements.append(Spacer(1, 0.1 * inch))
            
            elif block.type == "table":
                # Build table data
                data = []
                if block.headers:
                    data.append(block.headers)
                data.extend(block.rows)
                
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _format_inline_content(self, content: List[InlineContent]) -> str:
        """Format inline content for PDF with ReportLab markup."""
        result = []
        for item in content:
            text = item.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            if item.bold and item.italic:
                text = f"<b><i>{text}</i></b>"
            elif item.bold:
                text = f"<b>{text}</b>"
            elif item.italic:
                text = f"<i>{text}</i>"
            
            if item.underline:
                text = f"<u>{text}</u>"
            
            if item.link:
                text = f'<link href="{item.link}" color="blue">{text}</link>'
            
            result.append(text)
        
        return "".join(result)
