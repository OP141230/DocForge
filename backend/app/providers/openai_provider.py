"""OpenAI provider for document generation."""
import json
from typing import Dict
from openai import AsyncOpenAI

from app.models.document_ir import DocumentIR, DocumentMetadata, Section
from app.models.generation import DocumentRequirements, OutlineResponse, OutlineItem
from app.core.config import get_settings
from .base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI-based AI provider using GPT models."""
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_retries = settings.OPENAI_MAX_RETRIES
    
    async def generate_outline(self, requirements: DocumentRequirements) -> OutlineResponse:
        """Generate document outline using OpenAI."""
        prompt = f"""Generate a detailed outline for a {requirements.document_type} document.

Topic: {requirements.topic}
Title: {requirements.title}
Audience: {requirements.audience or 'general'}
Tone: {requirements.tone or 'professional'}
Length: {requirements.length}
{f'Additional instructions: {requirements.additional_instructions}' if requirements.additional_instructions else ''}

Return a JSON array of outline items, each with 'level' (1-6) and 'title'.
Example: [{{"level": 1, "title": "Introduction"}}, {{"level": 2, "title": "Background"}}]

Generate an appropriate outline with 4-7 main sections."""

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional document planner. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                )
                
                content = response.choices[0].message.content.strip()
                # Parse JSON response
                outline_data = json.loads(content)
                outline_items = [OutlineItem(**item) for item in outline_data]
                
                return OutlineResponse(outline=outline_items)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Failed to generate outline after {self.max_retries} attempts: {str(e)}")
                continue
    
    async def generate_content(self, outline: OutlineResponse, requirements: DocumentRequirements) -> DocumentIR:
        """Generate full document content using OpenAI."""
        outline_str = "\n".join([f"{'  ' * (item.level - 1)}{item.level}. {item.title}" for item in outline.outline])
        
        # FIX #2: Calculate target word count based on length
        length_to_words = {
            "short": 1000,      # ~2 pages
            "medium": 2500,     # ~5 pages
            "long": 5000,       # ~10 pages
            "10_pages": 5000,   # Explicit 10 pages
            "20_pages": 10000,  # Explicit 20 pages
        }
        target_words = length_to_words.get(requirements.length, 2500)
        
        # If length is a number with "pages", parse it
        if "page" in requirements.length.lower():
            try:
                num_pages = int(''.join(filter(str.isdigit, requirements.length)))
                target_words = num_pages * 500  # ~500 words per page
            except:
                pass
        
        prompt = f"""Generate complete content for this document:

Title: {requirements.title}
Topic: {requirements.topic}
Document Type: {requirements.document_type}
Audience: {requirements.audience or 'general'}
Tone: {requirements.tone or 'professional'}
Length: {requirements.length} (Target: approximately {target_words} words)

IMPORTANT: 
- Generate approximately {target_words} words of content
- Include {target_words // 100} to {target_words // 80} paragraphs
- Ensure comprehensive coverage of each section
- Do NOT just create outlines - write full, detailed paragraphs for each section

VISUAL ELEMENTS REQUIRED:
- Include TABLES for data, comparisons, or structured information
- Include MATH EQUATIONS using DEDICATED BLOCKS for formulas, calculations
- Include DIAGRAMS (Mermaid syntax) for processes, flows, relationships
- Use tables when presenting: statistics, comparisons, features, specifications
- Use diagrams when explaining: workflows, architectures, processes, relationships

Outline:
{outline_str}

Generate well-structured content with:
- Full paragraphs (not bullet points unless specifically needed)
- Detailed explanations and examples
- Proper transitions between sections
- Lists only where they add value
- **Tables for data presentation** (use "table" type blocks)
- **Math equations for formulas** (use "math_equation" type blocks - see examples below)
- **Diagrams for visual concepts** (use "diagram" type blocks with Mermaid)

CRITICAL RULE FOR MATHEMATICAL EXPRESSIONS:
❌ NEVER write LaTeX inside paragraph text like: {{"type": "paragraph", "content": [{{"text": "The equation \\(E=mc^2\\) shows..."}}]}}
✅ ALWAYS use separate math_equation blocks like: {{"type": "math_equation", "equation": "E = mc^2", "display_mode": true}}

BLOCK TYPES AVAILABLE:
{{
  "type": "paragraph",
  "content": [{{"text": "Full detailed paragraph without any LaTeX delimiters..."}}]
}},
{{
  "type": "table",
  "headers": ["Column 1", "Column 2", "Column 3"],
  "rows": [
    ["Data 1", "Data 2", "Data 3"],
    ["Data 4", "Data 5", "Data 6"]
  ],
  "caption": "Table caption"
}},
{{
  "type": "math_equation",
  "equation": "E = mc^2",
  "display_mode": true,
  "label": "Einstein's mass-energy equivalence"
}},
{{
  "type": "math_equation",
  "equation": "x = \\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}",
  "display_mode": true,
  "label": "Quadratic formula"
}},
{{
  "type": "math_equation",
  "equation": "\\sum_{{i=1}}^{{n}} x_i = x_1 + x_2 + \\cdots + x_n",
  "display_mode": true,
  "label": "Summation notation"
}},
{{
  "type": "math_equation",
  "equation": "Q(x,y,z) = 3x^{{2}} + 3y^{{2}} + 3z^{{2}} + 2xy + 2xz + 2yz",
  "display_mode": true,
  "label": "Quadratic form"
}},
{{
  "type": "diagram",
  "diagram_type": "flowchart",
  "mermaid_code": "flowchart TD\\n  A[Start] --> B[Process]\\n  B --> C[End]",
  "caption": "Process flow diagram"
}}

MATH EQUATION EXAMPLES - Use these patterns:
- Simple: {{"type": "math_equation", "equation": "F = ma", "display_mode": true}}
- Fractions: {{"type": "math_equation", "equation": "\\frac{{1}}{{2}}", "display_mode": true}}
- Subscripts/Superscripts: {{"type": "math_equation", "equation": "x^{{2}} + y_{{i}}", "display_mode": true}}
- Greek letters: {{"type": "math_equation", "equation": "\\alpha + \\beta = \\gamma", "display_mode": true}}
- Matrices: {{"type": "math_equation", "equation": "\\begin{{bmatrix}} 1 & 2 \\\\ 3 & 4 \\end{{bmatrix}}", "display_mode": true}}

Return the content as a valid DocumentIR JSON matching this schema:
{{
  "title": "string",
  "content": [
    {{
      "level": 1,
      "title": "Section Title",
      "blocks": [
        {{"type": "paragraph", "content": [{{"text": "Full detailed paragraph content here with multiple sentences..."}}]}},
        {{"type": "table", "headers": ["Col1", "Col2"], "rows": [["Data1", "Data2"]], "caption": "Table caption"}},
        {{"type": "math_equation", "equation": "x = \\frac{{-b \\pm \\sqrt{{b^2-4ac}}}}{{2a}}", "display_mode": true}},
        {{"type": "diagram", "diagram_type": "flowchart", "mermaid_code": "flowchart LR\\n  A-->B", "caption": "Diagram caption"}}
      ]
    }}
  ],
  "metadata": {{
    "document_type": "{requirements.document_type}",
    "audience": "{requirements.audience}",
    "tone": "{requirements.tone}",
    "language": "{requirements.language}"
  }}
}}

Remember: Generate {target_words} words of ACTUAL CONTENT with visual elements (tables, diagrams, equations) where relevant!"""

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional document writer. Generate comprehensive, detailed content. Return only valid JSON matching the DocumentIR schema."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=min(16000, target_words * 2),  # Ensure enough tokens for long documents
                )
                
                content = response.choices[0].message.content.strip()
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                doc_data = json.loads(content)
                return DocumentIR(**doc_data)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Failed to generate content after {self.max_retries} attempts: {str(e)}")
                continue
    
    async def generate_section(
        self,
        section_title: str,
        context: Dict,
        instruction: str,
        requirements: DocumentRequirements = None,
    ) -> Section:
        """Generate or transform a single section using OpenAI."""
        prompt = f"""Generate content for this document section:

Section Title: {section_title}
Document Context: {context.get('document_title', 'N/A')}
Instruction: {instruction}
Previous Section: {context.get('previous_section', 'N/A')}

Return a valid Section JSON matching this schema:
{{
  "level": {context.get('level', 1)},
  "title": "{section_title}",
  "blocks": [
    {{"type": "paragraph", "content": [{{"text": "Content here"}}]}}
  ]
}}

Generate well-written content following the instruction."""

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional document writer. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                )
                
                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                section_data = json.loads(content)
                return Section(**section_data)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Failed to generate section after {self.max_retries} attempts: {str(e)}")
                continue
