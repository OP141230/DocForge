"""Quick fix for PDF math rendering - replace Unicode symbols with ASCII equivalents."""

# This script patches the LaTeX converter to use ASCII fallbacks instead of Unicode
# symbols that ReportLab's standard fonts can't render

import sys
sys.path.insert(0, '.')

from app.exporters.pdf_exporter import parse_inline_latex, latex_to_unicode

# Test cases
test_cases = [
    (r"Q(x,y,z)=x^{2}+y^{2}+z^{2}", "Q(x,y,z)=x^2+y^2+z^2"),
    (r"\lambda_{1}", "lambda_1"),
    (r"x^T A x", "x^T A x"),
    (r"\sum_{i=1}^{n}", "SUM_(i=1)^n"),
]

print("Testing current LaTeX converter:")
print("=" * 60)

for latex, expected in test_cases:
    result = parse_inline_latex(latex)
    print(f"Input:  {latex}")
    print(f"Output: {result}")
    print(f"Has ■?: {'■' in result or '□' in result}")
    print()

print("\nDirect latex_to_unicode tests:")
print("=" * 60)

for latex, _ in test_cases:
    result = latex_to_unicode(latex)
    print(f"Input:  {latex}")
    print(f"Output: {result}")
    # Check for common Unicode characters that ReportLab can't render
    problem_chars = ['²', '³', '₁', '₂', 'λ', 'α', 'Σ', '∑', '∫', '∂']
    has_unicode = any(c in result for c in problem_chars)
    print(f"Has problematic Unicode: {has_unicode}")
    print()
