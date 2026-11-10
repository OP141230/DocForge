"""PDF exporter using ReportLab."""
from io import BytesIO
from typing import List, Optional
from pathlib import Path
import re

from reportlab.lib.pagesizes import letter, A4, legal
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    ListFlowable, ListItem, PageBreak, Image as RLImage
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

try:
    from sympy import sympify, pretty
    from sympy.parsing.latex import parse_latex
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False

from app.models.document_ir import DocumentIR, Section, InlineContent, PageLayout
from .base import Exporter


def latex_to_unicode(latex_str: str) -> str:
    """
    Convert LaTeX mathematical expression to Unicode mathematical symbols.
    
    Args:
        latex_str: LaTeX equation string
        
    Returns:
        Unicode representation with mathematical symbols, or formatted LaTeX as fallback
    """
    if not latex_str or not latex_str.strip():
        return ""
    
    # If sympy is not available, fall back to formatted LaTeX
    if not SYMPY_AVAILABLE:
        return _format_latex_fallback(latex_str)
    
    try:
        # Try parsing with sympy's LaTeX parser
        expr = parse_latex(latex_str)
        
        # Convert to Unicode using sympy's pretty printer
        unicode_str = pretty(expr, use_unicode=True)
        
        # If the result is multiline (for complex expressions), return it
        if '\n' in unicode_str:
            return unicode_str
        
        # For single-line expressions, clean up extra spaces
        return unicode_str.strip()
        
    except Exception as e:
        # If parsing fails, try manual conversion for common patterns
        try:
            return _manual_latex_to_unicode(latex_str)
        except:
            # Final fallback: return formatted LaTeX
            return _format_latex_fallback(latex_str)


def _manual_latex_to_unicode(latex_str: str) -> str:
    """
    Manually convert common LaTeX patterns to Unicode.
    Handles superscripts, subscripts, fractions, Greek letters, and common symbols.
    """
    result = latex_str
    
    # Greek letters mapping
    greek_letters = {
        r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
        r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
        r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
        r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
        r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
        r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
        r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
        r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Phi': 'Φ',
        r'\Psi': 'Ψ', r'\Omega': 'Ω'
    }
    
    # Replace Greek letters
    for latex, unicode_char in greek_letters.items():
        result = result.replace(latex, unicode_char)
    
    # Common math symbols
    math_symbols = {
        r'\infty': '∞', r'\pm': '±', r'\mp': '∓',
        r'\times': '×', r'\div': '÷', r'\cdot': '·',
        r'\leq': '≤', r'\geq': '≥', r'\neq': '≠',
        r'\approx': '≈', r'\equiv': '≡', r'\propto': '∝',
        r'\sum': '∑', r'\prod': '∏', r'\int': '∫',
        r'\partial': '∂', r'\nabla': '∇', r'\sqrt': '√',
        r'\in': '∈', r'\notin': '∉', r'\subset': '⊂',
        r'\supset': '⊃', r'\cap': '∩', r'\cup': '∪',
        r'\forall': '∀', r'\exists': '∃', r'\neg': '¬',
        r'\wedge': '∧', r'\vee': '∨', r'\rightarrow': '→',
        r'\leftarrow': '←', r'\leftrightarrow': '↔',
        r'\Rightarrow': '⇒', r'\Leftarrow': '⇐', r'\Leftrightarrow': '⇔'
    }
    
    for latex, unicode_char in math_symbols.items():
        result = result.replace(latex, unicode_char)
    
    # Superscripts (Unicode superscript characters)
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
        'n': 'ⁿ', 'i': 'ⁱ'
    }
    
    # Subscripts (Unicode subscript characters)
    subscript_map = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
        'a': 'ₐ', 'e': 'ₑ', 'o': 'ₒ', 'x': 'ₓ', 'h': 'ₕ',
        'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'p': 'ₚ',
        's': 'ₛ', 't': 'ₜ'
    }
    
    # Convert superscripts: ^{...} or ^x
    def replace_superscript(match):
        content = match.group(1) if match.group(1) else match.group(2)
        return ''.join(superscript_map.get(c, f'^{c}') for c in content)
    
    result = re.sub(r'\^{([^}]+)}|\^(.)', replace_superscript, result)
    
    # Convert subscripts: _{...} or _x
    def replace_subscript(match):
        content = match.group(1) if match.group(1) else match.group(2)
        return ''.join(subscript_map.get(c, f'_{c}') for c in content)
    
    result = re.sub(r'_{([^}]+)}|_(.)', replace_subscript, result)
    
    # Handle fractions \frac{a}{b}
    def replace_fraction(match):
        numerator = match.group(1)
        denominator = match.group(2)
        return f"({numerator})/({denominator})"
    
    result = re.sub(r'\\frac{([^}]+)}{([^}]+)}', replace_fraction, result)
    
    # Handle square root \sqrt{x} or \sqrt[n]{x}
    def replace_sqrt(match):
        root = match.group(1) if match.group(1) else None
        content = match.group(2)
        if root:
            return f"{root}√({content})"
        return f"√({content})"
    
    result = re.sub(r'\\sqrt(?:\[([^\]]+)\])?{([^}]+)}', replace_sqrt, result)
    
    # Clean up remaining braces
    result = result.replace('{', '').replace('}', '')
    
    # Clean up backslashes from unrecognized commands
    result = re.sub(r'\\([a-zA-Z]+)', r'\1', result)
    
    return result


def _format_latex_fallback(latex_str: str) -> str:
    """
    Format LaTeX string for display when conversion is not possible.
    Makes it more readable by cleaning up LaTeX commands.
    """
    # Remove common LaTeX delimiters
    result = latex_str.strip()
    for delimiter in ['$$', '$', '\\[', '\\]', '\\(', '\\)']:
        result = result.replace(delimiter, '')
    
    return f"LaTeX: {result.strip()}"


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
            
            elif block.type == "math_equation":
                # Convert LaTeX to Unicode mathematical symbols
                unicode_math = latex_to_unicode(block.equation)
                
                # Check if the result is multiline (complex expression)
                is_multiline = '\n' in unicode_math
                
                if is_multiline:
                    # For complex multiline expressions, use preformatted style
                    math_style = ParagraphStyle(
                        'MathEquation',
                        parent=styles['Code'],
                        fontSize=11,
                        fontName='Courier',
                        alignment=TA_CENTER if block.display_mode else TA_LEFT,
                        borderColor=colors.HexColor('#e8e8e8'),
                        borderWidth=1,
                        borderPadding=10,
                        backColor=colors.HexColor('#f9f9f9'),
                        spaceAfter=12
                    )
                    
                    # Render each line separately to preserve formatting
                    lines = unicode_math.split('\n')
                    for line in lines:
                        # Escape XML characters but preserve unicode math
                        safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        elements.append(Paragraph(safe_line or ' ', math_style))
                else:
                    # For single-line expressions, use a cleaner style
                    math_style = ParagraphStyle(
                        'MathEquationInline',
                        parent=styles['Normal'],
                        fontSize=12,
                        alignment=TA_CENTER if block.display_mode else TA_LEFT,
                        borderColor=colors.HexColor('#e8e8e8'),
                        borderWidth=1,
                        borderPadding=8,
                        backColor=colors.HexColor('#f9f9f9'),
                        spaceAfter=12,
                        spaceBefore=6
                    )
                    
                    # Escape XML characters but preserve unicode math
                    safe_math = unicode_math.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    # Add label if present
                    if block.label:
                        safe_math = f"{safe_math}  <i>({block.label})</i>"
                    
                    elements.append(Paragraph(safe_math, math_style))
                
                elements.append(Spacer(1, 0.1 * inch))
            
            elif block.type == "diagram":
                # Render diagram description
                # For Mermaid rendering, we'd need a Mermaid-to-image converter
                # For now, display the diagram code in a formatted box
                diagram_style = ParagraphStyle(
                    'Diagram',
                    parent=styles['Code'],
                    fontSize=9,
                    fontName='Courier',
                    borderColor=colors.HexColor('#d0e8f0'),
                    borderWidth=1,
                    borderPadding=10,
                    backColor=colors.HexColor('#f0f8ff'),
                )
                
                diagram_text = f"[{block.diagram_type.title()} Diagram]"
                elements.append(Paragraph(diagram_text, ParagraphStyle(
                    'DiagramTitle',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.HexColor('#2c3e50'),
                    spaceAfter=6
                )))
                
                # Add the Mermaid code
                code_lines = block.mermaid_code.split('\n')
                for line in code_lines:
                    elements.append(Paragraph(line or ' ', diagram_style))
                
                if block.caption:
                    caption_style = ParagraphStyle(
                        'DiagramCaption',
                        parent=styles['Normal'],
                        fontSize=9,
                        textColor=colors.grey,
                        alignment=TA_CENTER,
                        spaceAfter=12
                    )
                    elements.append(Paragraph(block.caption, caption_style))
                
                elements.append(Spacer(1, 0.1 * inch))
        
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
