"""Groq provider for document generation (FREE)."""
import json
from typing import Dict
from openai import AsyncOpenAI

from app.models.document_ir import DocumentIR, DocumentMetadata, Section
from app.models.generation import DocumentRequirements, OutlineResponse, OutlineItem
from app.core.config import get_settings
from .base import AIProvider


class GroqProvider(AIProvider):
    """Groq-based AI provider using Llama 3 models (FREE with rate limits)."""
    
    def __init__(self):
        settings = get_settings()
        # Groq uses OpenAI-compatible API
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = settings.GROQ_MODEL
        self.max_retries = settings.GROQ_MAX_RETRIES
    
    async def generate_outline(self, requirements: DocumentRequirements) -> OutlineResponse:
        """Generate document outline using Groq."""
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
                        {"role": "system", "content": "You are a professional document planner. Return only valid JSON array."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content.strip()
                
                # Parse the JSON response
                doc_data = json.loads(content)
                
                # Handle different response structures
                if isinstance(doc_data, list):
                    outline_items = [OutlineItem(**item) for item in doc_data]
                elif "outline" in doc_data:
                    outline_items = [OutlineItem(**item) for item in doc_data["outline"]]
                elif "items" in doc_data:
                    outline_items = [OutlineItem(**item) for item in doc_data["items"]]
                else:
                    # Assume the first array found
                    for value in doc_data.values():
                        if isinstance(value, list):
                            outline_items = [OutlineItem(**item) for item in value]
                            break
                    else:
                        raise ValueError("Could not find outline array in response")
                
                return OutlineResponse(outline=outline_items)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Failed to generate outline after {self.max_retries} attempts: {str(e)}")
                continue
    
    async def generate_content(self, outline: OutlineResponse, requirements: DocumentRequirements) -> DocumentIR:
        """Generate full document content using Groq."""
        outline_str = "\n".join([f"{'  ' * (item.level - 1)}{item.level}. {item.title}" for item in outline.outline])
        
        prompt = f"""Generate complete content for this document. Return valid JSON only.

Title: {requirements.title}
Topic: {requirements.topic}
Document Type: {requirements.document_type}

Outline:
{outline_str}

Generate well-structured content. Return JSON matching this structure:
{{
  "title": "{requirements.title}",
  "content": [
    {{
      "level": 1,
      "title": "Section Title",
      "blocks": [
        {{"type": "paragraph", "content": [{{"text": "Content text here"}}]}}
      ]
    }}
  ],
  "metadata": {{
    "document_type": "{requirements.document_type}",
    "audience": "{requirements.audience or 'general'}",
    "tone": "{requirements.tone or 'professional'}",
    "language": "{requirements.language or 'en'}"
  }}
}}

Write 2-3 paragraphs per section. Keep responses concise to avoid truncation."""

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional document writer. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content.strip()
                doc_data = json.loads(content)
                return DocumentIR(**doc_data)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Fallback: create minimal valid document
                    sections = []
                    for item in outline.outline:
                        sections.append(Section(
                            level=item.level,
                            title=item.title,
                            blocks=[{
                                "type": "paragraph",
                                "content": [{
                                    "text": f"Content for {item.title}: This section covers the key points and details related to {item.title.lower()}. [Generated content failed, showing placeholder]"
                                }]
                            }]
                        ))
                    
                    return DocumentIR(
                        title=requirements.title,
                        content=sections,
                        metadata=DocumentMetadata(
                            document_type=requirements.document_type,
                            audience=requirements.audience,
                            tone=requirements.tone,
                            language=requirements.language or "en"
                        )
                    )
                continue
    
    async def generate_section(
        self,
        section_title: str,
        context: Dict,
        instruction: str,
        requirements: DocumentRequirements = None,
    ) -> Section:
        """Generate or transform a single section using Groq."""
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
                    content = "```".join(content.split("```")[:-1])
                
                section_data = json.loads(content)
                return Section(**section_data)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Failed to generate section after {self.max_retries} attempts: {str(e)}")
                continue
