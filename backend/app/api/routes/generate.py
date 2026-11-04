"""Generation endpoints."""
from fastapi import APIRouter, HTTPException

from app.models.generation import (
    DocumentRequirements,
    OutlineResponse,
    ContentGenerationRequest,
    SectionGenerationRequest,
)
from app.models.document_ir import DocumentIR, Section
from app.providers.factory import get_provider

router = APIRouter()


@router.post("/generate/outline", response_model=OutlineResponse)
async def generate_outline(requirements: DocumentRequirements):
    """Generate document outline from requirements."""
    try:
        provider = get_provider()
        outline = await provider.generate_outline(requirements)
        return outline
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate outline: {str(e)}")


@router.post("/generate/content", response_model=DocumentIR)
async def generate_content(request: ContentGenerationRequest):
    """Generate full document content from approved outline."""
    try:
        provider = get_provider()
        # Wrap the outline list in OutlineResponse for the provider
        outline_response = OutlineResponse(outline=request.outline)
        document = await provider.generate_content(outline_response, request.requirements)
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")


@router.post("/generate/section", response_model=Section)
async def generate_section(request: SectionGenerationRequest):
    """Generate or transform a single section."""
    try:
        provider = get_provider()
        section = await provider.generate_section(
            request.section_title,
            request.context,
            request.instruction,
            request.requirements,
        )
        return section
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate section: {str(e)}")
