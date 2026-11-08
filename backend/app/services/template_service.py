"""Template service - manage document templates."""
from typing import List, Optional
from uuid import uuid4

from app.models.template import (
    DocumentTemplate,
    TypographyStyle,
    HeadingStyle,
    PageLayout
)


class TemplateService:
    """Service for managing document templates."""
    
    # Built-in system templates
    _SYSTEM_TEMPLATES = None
    
    @classmethod
    def get_system_templates(cls) -> List[DocumentTemplate]:
        """Get all built-in system templates."""
        if cls._SYSTEM_TEMPLATES is None:
            cls._SYSTEM_TEMPLATES = cls._create_system_templates()
        return cls._SYSTEM_TEMPLATES
    
    @classmethod
    def get_template_by_id(cls, template_id: str) -> Optional[DocumentTemplate]:
        """Get a template by ID."""
        templates = cls.get_system_templates()
        for template in templates:
            if template.id == template_id:
                return template
        return None
    
    @classmethod
    def get_templates_by_category(cls, category: str) -> List[DocumentTemplate]:
        """Get templates filtered by category."""
        templates = cls.get_system_templates()
        return [t for t in templates if t.category == category]
    
    @classmethod
    def _create_system_templates(cls) -> List[DocumentTemplate]:
        """Create all built-in system templates."""
        return [
            # Academic templates
            cls._create_academic_essay_template(),
            cls._create_research_paper_template(),
            cls._create_thesis_template(),
            
            # Technical documentation
            cls._create_technical_doc_template(),
            cls._create_api_doc_template(),
            
            # Project reports
            cls._create_project_report_template(),
            cls._create_internship_report_template(),
            
            # Business documents
            cls._create_business_proposal_template(),
            cls._create_professional_report_template(),
            
            # User documentation
            cls._create_user_manual_template(),
            cls._create_tutorial_template(),
            
            # General
            cls._create_clean_modern_template(),
        ]
    
    @staticmethod
    def _create_academic_essay_template() -> DocumentTemplate:
        """Academic Essay template - classic university assignment style."""
        return DocumentTemplate(
            id="academic-essay",
            name="Academic Essay",
            description="Traditional academic essay format with standard margins and double spacing",
            category="academic",
            typography=TypographyStyle(
                font_family="Times New Roman",
                base_font_size=12,
                text_color="#000000",
                line_spacing=2.0,  # Double-spaced
                paragraph_spacing=0.0
            ),
            heading_styles={
                1: HeadingStyle(font_size=14, bold=True, spacing_before=0.5, spacing_after=0.25),
                2: HeadingStyle(font_size=13, bold=True, spacing_before=0.4, spacing_after=0.2),
                3: HeadingStyle(font_size=12, bold=True, spacing_before=0.3, spacing_after=0.15),
            },
            page_layout=PageLayout(
                page_size="Letter",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0,
                page_numbers=True,
                page_number_position="bottom-center"
            ),
            primary_color="#000000",
            secondary_color="#333333",
            table_header_background="#F5F5F5",
            table_border_color="#000000",
            default_citation_style="mla",
            is_system_template=True
        )
    
    @staticmethod
    def _create_research_paper_template() -> DocumentTemplate:
        """Research Paper template - formal academic research."""
        return DocumentTemplate(
            id="research-paper",
            name="Research Paper",
            description="Formal research paper with APA-style formatting",
            category="academic",
            typography=TypographyStyle(
                font_family="Times New Roman",
                base_font_size=12,
                text_color="#000000",
                line_spacing=2.0,
                paragraph_spacing=0.0
            ),
            heading_styles={
                1: HeadingStyle(font_size=14, bold=True, spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=13, bold=True, spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=12, bold=True, italic=False, spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="Letter",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0,
                header_text="Running head: DOCUMENT TITLE",
                page_numbers=True,
                page_number_position="bottom-right"
            ),
            primary_color="#000000",
            table_header_background="#E8E8E8",
            table_border_color="#000000",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_thesis_template() -> DocumentTemplate:
        """Thesis/Dissertation template."""
        return DocumentTemplate(
            id="thesis",
            name="Thesis/Dissertation",
            description="Formal thesis or dissertation format with chapter structure",
            category="academic",
            typography=TypographyStyle(
                font_family="Times New Roman",
                base_font_size=12,
                text_color="#000000",
                line_spacing=1.5,
                paragraph_spacing=0.1
            ),
            heading_styles={
                1: HeadingStyle(font_size=18, bold=True, uppercase=True, spacing_before=1.0, spacing_after=0.5),
                2: HeadingStyle(font_size=16, bold=True, spacing_before=0.6, spacing_after=0.3),
                3: HeadingStyle(font_size=14, bold=True, spacing_before=0.4, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=1.5,
                margin_bottom=1.5,
                margin_left=1.5,
                margin_right=1.0,
                page_numbers=True,
                page_number_position="bottom-center"
            ),
            primary_color="#000000",
            table_header_background="#F0F0F0",
            table_border_color="#333333",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_technical_doc_template() -> DocumentTemplate:
        """Technical Documentation template."""
        return DocumentTemplate(
            id="technical-doc",
            name="Technical Documentation",
            description="Clean technical documentation with code-friendly formatting",
            category="technical",
            typography=TypographyStyle(
                font_family="Arial",
                base_font_size=11,
                text_color="#333333",
                line_spacing=1.3,
                paragraph_spacing=0.15
            ),
            heading_styles={
                1: HeadingStyle(font_size=20, bold=True, color="#2C3E50", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=16, bold=True, color="#34495E", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=14, bold=True, color="#7F8C8D", spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0,
                footer_text="Internal Documentation | Confidential",
                page_numbers=True,
                page_number_position="bottom-right"
            ),
            primary_color="#2C3E50",
            secondary_color="#34495E",
            accent_color="#3498DB",
            table_header_background="#ECF0F1",
            table_border_color="#BDC3C7",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_api_doc_template() -> DocumentTemplate:
        """API Documentation template."""
        return DocumentTemplate(
            id="api-doc",
            name="API Documentation",
            description="API reference documentation with endpoint formatting",
            category="technical",
            typography=TypographyStyle(
                font_family="Segoe UI",
                base_font_size=11,
                text_color="#24292E",
                line_spacing=1.4,
                paragraph_spacing=0.15
            ),
            heading_styles={
                1: HeadingStyle(font_size=24, bold=True, color="#0366D6", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=18, bold=True, color="#0366D6", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=14, bold=True, color="#586069", spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=0.75,
                margin_bottom=0.75,
                margin_left=0.75,
                margin_right=0.75,
                page_numbers=True,
                page_number_position="bottom-center"
            ),
            primary_color="#0366D6",
            secondary_color="#586069",
            accent_color="#28A745",
            table_header_background="#F6F8FA",
            table_border_color="#E1E4E8",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_project_report_template() -> DocumentTemplate:
        """Project Report template."""
        return DocumentTemplate(
            id="project-report",
            name="Project Report",
            description="Professional project report for engineering and technical projects",
            category="project",
            typography=TypographyStyle(
                font_family="Calibri",
                base_font_size=11,
                text_color="#000000",
                line_spacing=1.15,
                paragraph_spacing=0.1
            ),
            heading_styles={
                1: HeadingStyle(font_size=18, bold=True, color="#1F4E78", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=14, bold=True, color="#2E75B5", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=12, bold=True, color="#5B9BD5", spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0,
                header_text="Project Report",
                page_numbers=True,
                page_number_position="bottom-right"
            ),
            primary_color="#1F4E78",
            secondary_color="#2E75B5",
            accent_color="#5B9BD5",
            table_header_background="#DEEBF7",
            table_border_color="#9BC2E6",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_internship_report_template() -> DocumentTemplate:
        """Internship Report template."""
        return DocumentTemplate(
            id="internship-report",
            name="Internship Report",
            description="Professional internship or work experience report",
            category="project",
            typography=TypographyStyle(
                font_family="Calibri",
                base_font_size=12,
                text_color="#000000",
                line_spacing=1.5,
                paragraph_spacing=0.15
            ),
            heading_styles={
                1: HeadingStyle(font_size=16, bold=True, color="#44546A", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=14, bold=True, color="#5B738B", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=12, bold=True, spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.25,
                margin_right=1.0,
                page_numbers=True,
                page_number_position="bottom-center"
            ),
            primary_color="#44546A",
            table_header_background="#D6DCE4",
            table_border_color="#8FAADC",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_business_proposal_template() -> DocumentTemplate:
        """Business Proposal template."""
        return DocumentTemplate(
            id="business-proposal",
            name="Business Proposal",
            description="Professional business proposal with executive summary format",
            category="business",
            typography=TypographyStyle(
                font_family="Calibri",
                base_font_size=11,
                text_color="#000000",
                line_spacing=1.15,
                paragraph_spacing=0.1
            ),
            heading_styles={
                1: HeadingStyle(font_size=20, bold=True, color="#203864", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=16, bold=True, color="#385E9D", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=13, bold=True, color="#4472C4", spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="Letter",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0,
                footer_text="Confidential Business Proposal",
                page_numbers=True,
                page_number_position="bottom-right"
            ),
            primary_color="#203864",
            secondary_color="#385E9D",
            accent_color="#4472C4",
            table_header_background="#D9E2F3",
            table_border_color="#8EA9DB",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_professional_report_template() -> DocumentTemplate:
        """Professional Report template."""
        return DocumentTemplate(
            id="professional-report",
            name="Professional Report",
            description="Clean professional report for business and corporate use",
            category="business",
            typography=TypographyStyle(
                font_family="Arial",
                base_font_size=11,
                text_color="#000000",
                line_spacing=1.15,
                paragraph_spacing=0.15
            ),
            heading_styles={
                1: HeadingStyle(font_size=18, bold=True, color="#000000", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=14, bold=True, color="#333333", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=12, bold=True, color="#666666", spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0,
                page_numbers=True,
                page_number_position="bottom-right"
            ),
            primary_color="#000000",
            secondary_color="#333333",
            table_header_background="#E7E6E6",
            table_border_color="#BFBFBF",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_user_manual_template() -> DocumentTemplate:
        """User Manual template."""
        return DocumentTemplate(
            id="user-manual",
            name="User Manual",
            description="User-friendly manual with clear instructions and screenshots",
            category="documentation",
            typography=TypographyStyle(
                font_family="Verdana",
                base_font_size=11,
                text_color="#333333",
                line_spacing=1.3,
                paragraph_spacing=0.15
            ),
            heading_styles={
                1: HeadingStyle(font_size=18, bold=True, color="#0078D4", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=14, bold=True, color="#106EBE", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=12, bold=True, color="#2B88D8", spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=0.75,
                margin_bottom=0.75,
                margin_left=1.0,
                margin_right=1.0,
                header_text="User Manual",
                page_numbers=True,
                page_number_position="bottom-center"
            ),
            primary_color="#0078D4",
            secondary_color="#106EBE",
            accent_color="#50E6FF",
            table_header_background="#E5F1FB",
            table_border_color="#A6CCF1",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_tutorial_template() -> DocumentTemplate:
        """Tutorial/Guide template."""
        return DocumentTemplate(
            id="tutorial",
            name="Tutorial Guide",
            description="Step-by-step tutorial with examples and exercises",
            category="documentation",
            typography=TypographyStyle(
                font_family="Segoe UI",
                base_font_size=11,
                text_color="#333333",
                line_spacing=1.4,
                paragraph_spacing=0.15
            ),
            heading_styles={
                1: HeadingStyle(font_size=20, bold=True, color="#FF6B35", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=16, bold=True, color="#F7931E", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=13, bold=True, color="#FDC82F", spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0,
                page_numbers=True,
                page_number_position="bottom-right"
            ),
            primary_color="#FF6B35",
            secondary_color="#F7931E",
            accent_color="#FDC82F",
            table_header_background="#FFF3CD",
            table_border_color="#FFE5A1",
            default_citation_style="apa",
            is_system_template=True
        )
    
    @staticmethod
    def _create_clean_modern_template() -> DocumentTemplate:
        """Clean Modern template - general purpose."""
        return DocumentTemplate(
            id="clean-modern",
            name="Clean Modern",
            description="Modern, minimalist design suitable for any document type",
            category="general",
            typography=TypographyStyle(
                font_family="Helvetica",
                base_font_size=11,
                text_color="#2C3E50",
                line_spacing=1.3,
                paragraph_spacing=0.15
            ),
            heading_styles={
                1: HeadingStyle(font_size=22, bold=True, color="#1ABC9C", spacing_before=0.5, spacing_after=0.3),
                2: HeadingStyle(font_size=17, bold=True, color="#16A085", spacing_before=0.4, spacing_after=0.25),
                3: HeadingStyle(font_size=14, bold=True, color="#27AE60", spacing_before=0.3, spacing_after=0.2),
            },
            page_layout=PageLayout(
                page_size="A4",
                orientation="portrait",
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0,
                page_numbers=True,
                page_number_position="bottom-center"
            ),
            primary_color="#1ABC9C",
            secondary_color="#16A085",
            accent_color="#27AE60",
            table_header_background="#E8F8F5",
            table_border_color="#A9DFBF",
            default_citation_style="apa",
            is_system_template=True
        )
