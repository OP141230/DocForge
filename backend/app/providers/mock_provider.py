"""Mock AI provider for testing and development."""
import hashlib
import json
from typing import Dict, List, Optional

from app.models.document_ir import (
    DocumentIR,
    DocumentMetadata,
    Section,
    Paragraph,
    Heading,
    ListBlock,
    InlineContent,
)
from app.models.generation import DocumentRequirements, OutlineResponse, OutlineItem
from .base import AIProvider


class MockProvider(AIProvider):
    """Deterministic mock provider that requires no API key."""
    
    def _get_seed(self, data: dict) -> int:
        """Generate deterministic seed from input data."""
        data_str = json.dumps(data, sort_keys=True)
        hash_hex = hashlib.md5(data_str.encode()).hexdigest()
        return int(hash_hex[:8], 16)
    
    async def generate_outline(self, requirements: DocumentRequirements) -> OutlineResponse:
        """Generate a deterministic outline based on document type and topic."""
        seed = self._get_seed(requirements.model_dump())
        num_sections = 3 + (seed % 3)  # 3-5 sections
        
        # Base sections by document type
        type_templates = {
            "general_report": ["Introduction", "Background", "Analysis", "Findings", "Conclusion"],
            "academic_report": ["Abstract", "Introduction", "Literature Review", "Methodology", "Results", "Discussion", "Conclusion"],
            "project_report": ["Executive Summary", "Project Overview", "Objectives", "Implementation", "Results", "Recommendations"],
            "technical_documentation": ["Overview", "Getting Started", "Core Concepts", "API Reference", "Examples", "Troubleshooting"],
            "business_report": ["Executive Summary", "Market Analysis", "Financial Overview", "Strategic Recommendations", "Conclusion"],
            "article": ["Introduction", "Main Content", "Key Points", "Conclusion"],
            "resume": ["Summary", "Experience", "Education", "Skills"],
        }
        
        template = type_templates.get(requirements.document_type, type_templates["general_report"])
        sections = template[:num_sections]
        
        outline = [OutlineItem(level=1, title=title) for title in sections]
        
        # Add some subsections for variety
        if num_sections > 3:
            outline.insert(2, OutlineItem(level=2, title="Key Considerations"))
        
        return OutlineResponse(outline=outline)
    
    async def generate_content(self, outline: OutlineResponse, requirements: DocumentRequirements) -> DocumentIR:
        """Generate document content from outline."""
        sections = []
        
        for item in outline.outline:
            # Generate 2-3 paragraphs per section
            seed = self._get_seed({"title": item.title, "topic": requirements.topic})
            num_paragraphs = 2 + (seed % 2)
            
            blocks = []
            for i in range(num_paragraphs):
                para_seed = seed + i
                text = self._generate_paragraph_text(item.title, requirements.topic, para_seed)
                blocks.append(
                    Paragraph(
                        content=[InlineContent(text=text)]
                    )
                )
            
            # Add a list to some sections
            if seed % 3 == 0:
                items = [
                    [InlineContent(text=f"Key point about {item.title.lower()}")],
                    [InlineContent(text=f"Important consideration for {requirements.topic}")],
                    [InlineContent(text="Additional relevant information")],
                ]
                blocks.append(ListBlock(ordered=False, items=items))
            
            sections.append(
                Section(
                    level=item.level,
                    title=item.title,
                    blocks=blocks,
                )
            )
        
        metadata = DocumentMetadata(
            document_type=requirements.document_type,
            audience=requirements.audience,
            tone=requirements.tone,
            language=requirements.language,
        )
        
        return DocumentIR(
            title=requirements.title,
            content=sections,
            metadata=metadata,
        )
    
    async def generate_section(
        self,
        section_title: str,
        context: Dict,
        instruction: str,
        requirements: DocumentRequirements = None,
    ) -> Section:
        """Generate a single section with transformation applied."""
        seed = self._get_seed({"title": section_title, "instruction": instruction})
        
        # Adjust paragraph count based on instruction
        if "expand" in instruction.lower():
            num_paragraphs = 4
        elif "shorten" in instruction.lower():
            num_paragraphs = 1
        else:
            num_paragraphs = 2
        
        blocks = []
        for i in range(num_paragraphs):
            text = self._generate_paragraph_text(
                section_title,
                context.get("document_title", ""),
                seed + i,
            )
            blocks.append(Paragraph(content=[InlineContent(text=text)]))
        
        return Section(
            level=context.get("level", 1),
            title=section_title,
            blocks=blocks,
        )
    
    async def generate_content_with_sources(
        self,
        outline: OutlineResponse,
        requirements: DocumentRequirements,
        sources: List[Dict],
        evidence: Optional[List[Dict]] = None,
        citation_style: Optional[str] = None,
    ) -> DocumentIR:
        """Deterministic grounded generation for tests and offline development.

        The mock cannot reason about content, so it does something deliberately
        boring and honest: it reuses the normal template text and appends a
        marker that points at real evidence rows. That exercises the citation
        pipeline (marker -> source record -> in-text citation) without a network
        call and without inventing an external source.
        """
        document = await self.generate_content(outline, requirements)

        if not document.metadata.custom_fields:
            document.metadata.custom_fields = {}
        document.metadata.custom_fields["source_count"] = len(sources or [])
        document.metadata.custom_fields["sources_used"] = [
            source.get("original_filename", "uploaded document") for source in (sources or [])
        ]
        document.metadata.custom_fields["generation_provider"] = "mock"

        if evidence and document.content:
            markers = []
            for index, item in enumerate(evidence, 1):
                marker = item.get("marker") or f"E{index}"
                markers.append(marker)

            reference_note = " ".join(f"[{marker}]" for marker in markers[:3])
            target = document.content[0]
            target.blocks.append(
                Paragraph(
                    content=[
                        InlineContent(
                            text=(
                                "Reference passages were retrieved for this section "
                                f"{reference_note}."
                            )
                        )
                    ]
                )
            )
            document.metadata.custom_fields["evidence_markers_offered"] = markers

        return document

    def _generate_paragraph_text(self, section: str, topic: str, seed: int) -> str:
        """Generate deterministic paragraph text."""
        templates = [
            f"This section discusses {section.lower()} in the context of {topic}. "
            f"The analysis reveals several important aspects that merit careful consideration. "
            f"Understanding these elements is crucial for a comprehensive view of the subject matter.",
            
            f"When examining {section.lower()}, it becomes clear that {topic} plays a significant role. "
            f"Research and practical experience have demonstrated the importance of this relationship. "
            f"Further investigation continues to yield valuable insights.",
            
            f"The implications of {section.lower()} for {topic} are multifaceted. "
            f"Key stakeholders must consider various factors when addressing these issues. "
            f"Strategic planning and careful implementation are essential for success.",
            
            f"In relation to {topic}, {section.lower()} presents both opportunities and challenges. "
            f"Effective approaches require a balance of theoretical understanding and practical application. "
            f"Continuous evaluation helps ensure optimal outcomes.",
        ]
        
        return templates[seed % len(templates)]
