"""Abstract AI provider interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

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

    # ------------------------------------------------------------------
    # Optional Phase 4/5 capabilities
    # ------------------------------------------------------------------
    # These are concrete (not abstract) on purpose: Phase 1's providers must keep
    # working unchanged, so a provider that cannot use sources simply falls back
    # to plain generation.

    async def generate_content_with_sources(
        self,
        outline: OutlineResponse,
        requirements: DocumentRequirements,
        sources: List[Dict],
        evidence: Optional[List[Dict]] = None,
        citation_style: Optional[str] = None,
    ) -> DocumentIR:
        """Generate content using retrieved source material.

        ``sources`` are Phase 4 knowledge-base chunks; ``evidence`` are Phase 5
        evidence passages, each with a ``marker`` such as ``E1``. Providers that
        do not implement grounding should ignore both and warn the caller via
        metadata rather than inventing citations.
        """
        document = await self.generate_content(outline, requirements)
        if not document.metadata.custom_fields:
            document.metadata.custom_fields = {}
        document.metadata.custom_fields["generation_note"] = (
            "This provider does not support source-grounded generation; no citations were produced."
        )
        return document

    async def assess_claim(
        self,
        claim: str,
        passages: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Judge whether ``passages`` support or contradict ``claim``.

        Returns ``None`` when the provider cannot assess claims. The verification
        service then reports *Insufficient Evidence* rather than assuming
        support - an LLM's silence is not evidence either way.
        """
        return None

    # ------------------------------------------------------------------
    # Optional Phase 6 capabilities
    # ------------------------------------------------------------------
    # Same pattern as above: concrete defaults so a provider written for
    # Phase 1 keeps working. "Returns None" means "this provider cannot do it",
    # which the reviewer turns into a clearly-labelled limitation instead of
    # pretending the check ran.

    async def review_document(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return structured review findings for a document slice.

        ``payload`` keys (all untrusted *data*, never instructions):

        * ``text`` - the flattened text to review
        * ``categories`` - category ids the caller wants checked
        * ``requirements`` - brief metadata (document type, audience, tone)
        * ``evidence`` - optional list of ``{marker, title, url, text}``
        * ``section_titles`` - ordering hints for structural review

        The return value must look like ``{"findings": [RawFinding, ...]}``.
        Callers validate every field and reject anything they cannot locate in
        the real document.
        """
        return None

    async def transform_text(self, payload: Dict[str, Any]) -> Optional[str]:
        """Rewrite ``payload['text']`` according to ``payload['instruction']``.

        Must return the rewritten text only - no JSON envelope, no commentary.
        Returning ``None`` means the operation is unsupported.
        """
        return None

    async def assess_compliance(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Judge qualitative brief requirements (tone, audience, coverage).

        Returns ``{"results": [{"requirement", "status", "explanation",
        "suggested_action"}]}`` where ``status`` is one of the ComplianceStatus
        values. Deterministic checks (word count, required sections) are done by
        the service, not the model.
        """
        return None
