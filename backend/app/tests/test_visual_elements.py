"""Test visual elements support in Document IR and exporters."""
import pytest
from app.models.document_ir import (
    DocumentIR, 
    DocumentMetadata, 
    Section, 
    Paragraph, 
    InlineContent,
    MathEquation,
    Diagram,
    Table
)
from app.exporters.pdf_exporter import PDFExporter
from app.exporters.html_exporter import HTMLExporter
from app.exporters.docx_exporter import DOCXExporter


def test_math_equation_block_creation():
    """Test creating math equation blocks."""
    # Display mode equation
    eq1 = MathEquation(
        equation=r"\int_{a}^{b} f(x) dx = F(b) - F(a)",
        display_mode=True,
        label="Fundamental Theorem of Calculus"
    )
    assert eq1.type == "math_equation"
    assert eq1.display_mode is True
    assert eq1.label == "Fundamental Theorem of Calculus"
    
    # Inline equation
    eq2 = MathEquation(
        equation=r"E = mc^2",
        display_mode=False
    )
    assert eq2.type == "math_equation"
    assert eq2.display_mode is False
    assert eq2.label is None


def test_diagram_block_creation():
    """Test creating diagram blocks."""
    diagram = Diagram(
        diagram_type="flowchart",
        mermaid_code="""graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]""",
        caption="Simple decision flowchart"
    )
    assert diagram.type == "diagram"
    assert diagram.diagram_type == "flowchart"
    assert "graph TD" in diagram.mermaid_code
    assert diagram.caption == "Simple decision flowchart"


def test_document_with_visual_elements():
    """Test creating a document with all visual element types."""
    doc = DocumentIR(
        title="Visual Elements Test Document",
        metadata=DocumentMetadata(
            author="DocForge Test Suite",
            language="en",
            document_type="general_report"
        ),
        content=[
            Section(
                title="Mathematics",
                level=1,
                blocks=[
                    Paragraph(content=[
                        InlineContent(text="Here is an important equation:")
                    ]),
                    MathEquation(
                        equation=r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
                        display_mode=True,
                        label="Quadratic Formula"
                    ),
                    Paragraph(content=[
                        InlineContent(text="This shows the solutions to a quadratic equation.")
                    ])
                ]
            ),
            Section(
                title="Data Visualization",
                level=1,
                blocks=[
                    Paragraph(content=[
                        InlineContent(text="Below is a sample data table:")
                    ]),
                    Table(
                        headers=["Item", "Quantity", "Price"],
                        rows=[
                            ["Widget A", "10", "$5.00"],
                            ["Widget B", "20", "$3.50"],
                            ["Widget C", "15", "$7.25"]
                        ]
                    )
                ]
            ),
            Section(
                title="Process Flow",
                level=1,
                blocks=[
                    Paragraph(content=[
                        InlineContent(text="The following diagram shows the process:")
                    ]),
                    Diagram(
                        diagram_type="sequence",
                        mermaid_code="""sequenceDiagram
    participant User
    participant System
    User->>System: Request
    System->>User: Response""",
                        caption="User-System interaction sequence"
                    )
                ]
            )
        ]
    )
    
    # Verify structure
    assert len(doc.content) == 3
    assert doc.content[0].title == "Mathematics"
    assert doc.content[0].blocks[1].type == "math_equation"
    assert doc.content[1].blocks[1].type == "table"
    assert doc.content[2].blocks[1].type == "diagram"


def test_pdf_export_with_visual_elements():
    """Test PDF export handles visual elements without errors."""
    doc = DocumentIR(
        title="PDF Visual Elements Test",
        metadata=DocumentMetadata(author="Test", language="en", document_type="general_report"),
        content=[
            Section(
                title="Test Section",
                level=1,
                blocks=[
                    MathEquation(
                        equation=r"a^2 + b^2 = c^2",
                        display_mode=True,
                        label="Pythagorean Theorem"
                    ),
                    Diagram(
                        diagram_type="flowchart",
                        mermaid_code="graph LR\n    A-->B",
                        caption="Simple flow"
                    )
                ]
            )
        ]
    )
    
    exporter = PDFExporter()
    result = exporter.export(doc)
    
    # Should produce valid PDF bytes
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result[:4] == b'%PDF'  # PDF magic number


def test_html_export_with_visual_elements():
    """Test HTML export includes MathJax and Mermaid."""
    doc = DocumentIR(
        title="HTML Visual Elements Test",
        metadata=DocumentMetadata(author="Test", language="en", document_type="general_report"),
        content=[
            Section(
                title="Test Section",
                level=1,
                blocks=[
                    MathEquation(
                        equation=r"\sum_{i=1}^{n} i = \frac{n(n+1)}{2}",
                        display_mode=True
                    ),
                    Diagram(
                        diagram_type="class",
                        mermaid_code="classDiagram\n    class Animal",
                        caption="Class diagram"
                    )
                ]
            )
        ]
    )
    
    exporter = HTMLExporter()
    result = exporter.export(doc)
    html = result.decode('utf-8')
    
    # Check for MathJax inclusion
    assert 'MathJax' in html or 'mathjax' in html.lower()
    assert 'tex-mml-chtml.js' in html or 'MathJax' in html
    
    # Check for Mermaid inclusion
    assert 'mermaid' in html.lower()
    assert 'mermaid.min.js' in html or 'mermaid.js' in html
    
    # Check for visual element content
    assert 'math-equation' in html
    assert 'diagram-container' in html
    assert r'\sum_{i=1}^{n}' in html
    assert 'classDiagram' in html


def test_docx_export_with_visual_elements():
    """Test DOCX export handles visual elements without errors."""
    doc = DocumentIR(
        title="DOCX Visual Elements Test",
        metadata=DocumentMetadata(author="Test", language="en", document_type="general_report"),
        content=[
            Section(
                title="Test Section",
                level=1,
                blocks=[
                    MathEquation(
                        equation=r"f(x) = x^2 + 2x + 1",
                        display_mode=True,
                        label="Sample Function"
                    ),
                    Table(
                        headers=["X", "Y"],
                        rows=[["1", "4"], ["2", "9"]]
                    ),
                    Diagram(
                        diagram_type="gantt",
                        mermaid_code="gantt\n    title Project\n    section Phase1\n    Task :a1, 2024-01-01, 30d",
                        caption="Project timeline"
                    )
                ]
            )
        ]
    )
    
    exporter = DOCXExporter()
    result = exporter.export(doc)
    
    # Should produce valid DOCX bytes
    assert isinstance(result, bytes)
    assert len(result) > 0
    # DOCX files are ZIP archives
    assert result[:2] == b'PK'  # ZIP magic number


def test_multiple_equations_in_document():
    """Test document with multiple math equations."""
    doc = DocumentIR(
        title="Mathematics Reference",
        metadata=DocumentMetadata(author="Test", language="en", document_type="general_report"),
        content=[
            Section(
                title="Famous Equations",
                level=1,
                blocks=[
                    MathEquation(
                        equation=r"E = mc^2",
                        display_mode=True,
                        label="Einstein's Mass-Energy Equivalence"
                    ),
                    MathEquation(
                        equation=r"F = ma",
                        display_mode=True,
                        label="Newton's Second Law"
                    ),
                    MathEquation(
                        equation=r"\nabla \cdot \mathbf{E} = \frac{\rho}{\epsilon_0}",
                        display_mode=True,
                        label="Gauss's Law"
                    )
                ]
            )
        ]
    )
    
    # Test all exporters can handle multiple equations
    pdf_result = PDFExporter().export(doc)
    html_result = HTMLExporter().export(doc)
    docx_result = DOCXExporter().export(doc)
    
    assert len(pdf_result) > 0
    assert len(html_result) > 0
    assert len(docx_result) > 0
    
    # Verify HTML contains all equations
    html = html_result.decode('utf-8')
    assert 'E = mc^2' in html
    assert 'F = ma' in html
    assert 'Gauss' in html


def test_mixed_content_export():
    """Test document with mixed text, tables, equations, and diagrams."""
    doc = DocumentIR(
        title="Comprehensive Document",
        metadata=DocumentMetadata(author="Test", language="en", document_type="general_report"),
        content=[
            Section(
                title="Introduction",
                level=1,
                blocks=[
                    Paragraph(content=[InlineContent(text="This document contains various content types.")])
                ]
            ),
            Section(
                title="Data Analysis",
                level=1,
                blocks=[
                    Paragraph(content=[InlineContent(text="Statistical results:")]),
                    Table(
                        headers=["Metric", "Value", "Unit"],
                        rows=[
                            ["Mean", "42.5", "kg"],
                            ["Std Dev", "3.2", "kg"]
                        ]
                    ),
                    MathEquation(
                        equation=r"\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i",
                        display_mode=True,
                        label="Sample Mean"
                    )
                ]
            ),
            Section(
                title="Workflow",
                level=1,
                blocks=[
                    Diagram(
                        diagram_type="flowchart",
                        mermaid_code="""graph TD
    A[Collect Data] --> B[Analyze]
    B --> C[Report]""",
                        caption="Data processing workflow"
                    )
                ]
            )
        ]
    )
    
    # All exporters should handle mixed content
    for exporter in [PDFExporter(), HTMLExporter(), DOCXExporter()]:
        result = exporter.export(doc)
        assert isinstance(result, bytes)
        assert len(result) > 100  # Should be substantial content
