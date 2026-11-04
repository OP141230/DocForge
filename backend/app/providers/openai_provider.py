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
        
        prompt = f"""Generate complete content for this document:

Title: {requirements.title}
Topic: {requirements.topic}
Document Type: {requirements.document_type}
Audience: {requirements.audience or 'general'}
Tone: {requirements.tone or 'professional'}
Length: {requirements.length}

Outline:
{outline_str}

Generate well-structured content with paragraphs, lists, and appropriate formatting.
Return the content as a valid DocumentIR JSON matching this schema:
{{
  "title": "string",
  "content": [
    {{
      "level": 1,
      "title": "Section Title",
      "blocks": [
        {{"type": "paragraph", "content": [{{"text": "Content here"}}]}},
        {{"type": "list", "ordered": false, "items": [[{{"text": "Item"}}]]}}
      ]
    }}
  ],
  "metadata": {{
    "document_type": "{requirements.document_type}",
    "audience": "{requirements.audience}",
    "tone": "{requirements.tone}",
    "language": "{requirements.language}"
  }}
}}"""

        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional document writer. Return only valid JSON matching the DocumentIR schema."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
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
