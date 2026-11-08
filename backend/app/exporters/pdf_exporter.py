"""PDF exporter using ReportLab."""
from io import BytesIO
from typing import List, Optional
from pathlib import Path

from reportlab.lib.pagesizes import letter, A4, legal
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    ListFlowable, ListItem, PageBreak, Image as RLImage
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from app.models.document_ir import DocumentIR, Section, InlineContent, PageLayout
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
        
        # Determine page size and orientation from template
        page_size = self._get_page_size(document.metadata.page_layout)
        
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=page_size, 
            topMargin=self._get_margin(document.metadata.page_layout, "top"),
            bottomMargin=self._get_margin(document.metadata.page_layout, "bottom"),
            leftMargin=self._get_margin(document.metadata.page_layout, "left"),
            rightMargin=self._get_margin(document.metadata.page_layout, "right")
        )
        
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
    
    def _get_page_size(self, page_layout: Optional[PageLayout]):
        """Get ReportLab page size from PageLayout."""
        if not page_layout:
            return letter
        
        # Map page size
        size_map = {
            "letter": letter,
            "a4": A4,
            "legal": legal
        }
        base_size = size_map.get(page_layout.page_size.lower(), letter)
        
        # Handle orientation
        if page_layout.orientation == "landscape":
            return (base_size[1], base_size[0])  # Swap width and height
        return base_size
    
    def _get_margin(self, page_layout: Optional[PageLayout], side: str) -> float:
        """Get margin in points from PageLayout."""
        if not page_layout:
            return inch  # Default 1 inch
        
        # Get margin from individual fields
        margin_map = {
            "top": page_layout.margin_top,
            "bottom": page_layout.margin_bottom,
            "left": page_layout.margin_left,
            "right": page_layout.margin_right
        }
        margin_inches = margin_map.get(side, 1.0)
        return margin_inches * inch
    
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
            
            elif block.type == "image":
                # Handle image block
                try:
                    # Convert URL to local path if needed
                    image_path = self._resolve_image_path(block.url)
                    
                    # Load image
                    img = RLImage(image_path)
                    
                    # Set image size
                    if block.width and block.height:
                        img.drawWidth = block.width
                        img.drawHeight = block.height
                    elif block.width:
                        # Maintain aspect ratio
                        img.drawWidth = block.width
                        img.drawHeight = block.width * (img.imageHeight / img.imageWidth)
                    else:
                        # Default to fit page width with max size
                        max_width = 6 * inch
                        if img.imageWidth > max_width:
                            img.drawWidth = max_width
                            img.drawHeight = max_width * (img.imageHeight / img.imageWidth)
                    
                    # Apply alignment
                    if block.alignment == "center":
                        img.hAlign = 'CENTER'
                    elif block.alignment == "right":
                        img.hAlign = 'RIGHT'
                    else:
                        img.hAlign = 'LEFT'
                    
                    elements.append(img)
                    
                    # Add caption if present
                    if block.caption:
                        caption_style = ParagraphStyle(
                            'ImageCaption',
                            parent=styles['Normal'],
                            fontSize=9,
                            textColor=colors.grey,
                            alignment=TA_CENTER,
                            spaceAfter=12
                        )
                        elements.append(Paragraph(block.caption, caption_style))
                    
                    elements.append(Spacer(1, 0.1 * inch))
                    
                except Exception as e:
                    # If image fails to load, add error message
                    error_style = ParagraphStyle(
                        'Error',
                        parent=styles['Normal'],
                        textColor=colors.red
                    )
                    elements.append(Paragraph(f"[Image failed to load: {block.url}]", error_style))
                    elements.append(Spacer(1, 0.1 * inch))
            
            elif block.type == "page_break":
                # Add page break
                elements.append(PageBreak())
        
        return elements
    
    def _resolve_image_path(self, url: str) -> str:
        """
        Resolve image URL to local file path.
        
        Args:
            url: Image URL (can be local path, /api/images/{id}, or external URL)
            
        Returns:
            Local file path
        """
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
        
        # Otherwise return as-is and let ReportLab handle it (may support URLs)
        return url
    
    def _format_inline_content(self, content: List[InlineContent]) -> str:
        """Format inline content for PDF with ReportLab markup."""
        result = []
        for item in content:
            text = item.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            # Build inline styles
            font_tags = []
            
            # Bold and italic
            if item.bold and item.italic:
                text = f"<b><i>{text}</i></b>"
            elif item.bold:
                text = f"<b>{text}</b>"
            elif item.italic:
                text = f"<i>{text}</i>"
            
            # Underline
            if item.underline:
                text = f"<u>{text}</u>"
            
            # Strikethrough (use strike tag if supported, otherwise use unicode)
            if item.strikethrough:
                text = f"<strike>{text}</strike>"
            
            # Text color
            if item.color:
                try:
                    color_hex = item.color if item.color.startswith('#') else f"#{item.color}"
                    text = f'<font color="{color_hex}">{text}</font>'
                except:
                    pass  # Skip invalid colors
            
            # Background color (ReportLab doesn't support background in inline text well, skip)
            # Font size
            if item.font_size:
                text = f'<font size="{item.font_size}">{text}</font>'
            
            # Font family
            if item.font_family:
                # Map common fonts to ReportLab font names
                font_map = {
                    "serif": "Times-Roman",
                    "sans-serif": "Helvetica",
                    "monospace": "Courier",
                    "times": "Times-Roman",
                    "helvetica": "Helvetica",
                    "courier": "Courier"
                }
                font_name = font_map.get(item.font_family.lower(), "Helvetica")
                text = f'<font face="{font_name}">{text}</font>'
            
            # Links
            if item.link:
                text = f'<link href="{item.link}" color="blue">{text}</link>'
            
            result.append(text)
        
        return "".join(result)
