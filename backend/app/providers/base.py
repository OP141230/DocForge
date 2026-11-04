"""Abstract AI provider interface."""
from abc import ABC, abstractmethod
from typing import Dict

from app.models.document_ir import DocumentIR, Section
from app.models.generation import DocumentRequirements, OutlineResponse


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_outline(self, requirements: DocumentRequirements) -> OutlineResponse:
        """Generate document outline from requirements.
        
        Args:
            requirements: Document requirements
            
        Returns:
            OutlineResponse with list of outline items
        """
        pass
    
    @abstractmethod
    async def generate_content(self, outline: OutlineResponse, requirements: DocumentRequirements) -> DocumentIR:
        """Generate full document content from approved outline.
        
        Args:
            outline: Approved outline structure
            requirements: Original document requirements
            
        Returns:
            Complete DocumentIR with generated content
        """
        pass
    
    @abstractmethod
    async def generate_section(
        self,
        section_title: str,
        context: Dict,
        instruction: str,
        requirements: DocumentRequirements = None,
    ) -> Section:
        """Regenerate or transform a single section.
        
        Args:
            section_title: Title of section to generate
            context: Surrounding document context
            instruction: Transformation instruction (expand, shorten, change_tone:casual, etc.)
            requirements: Optional document requirements
            
        Returns:
            Section with generated content
        """
        pass
