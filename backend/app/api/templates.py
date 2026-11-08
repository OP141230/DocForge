"""Template API routes for document templates."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.models.template import DocumentTemplate, TemplateCategory
from app.services.template_service import TemplateService
from app.core.auth import get_current_user
from app.models.auth import User

router = APIRouter()


@router.get("/", response_model=List[DocumentTemplate])
async def list_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List all available document templates.
    
    Args:
        category: Optional category filter
        current_user: Authenticated user
        
    Returns:
        List of templates
    """
    if category:
        return TemplateService.get_templates_by_category(category)
    return TemplateService.get_system_templates()


@router.get("/categories", response_model=List[str])
async def list_categories(current_user: User = Depends(get_current_user)):
    """
    List all template categories.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        List of category names
    """
    templates = TemplateService.get_system_templates()
    categories = list(set(t.category for t in templates))
    return sorted(categories)


@router.get("/{template_id}", response_model=DocumentTemplate)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific template by ID.
    
    Args:
        template_id: Template identifier
        current_user: Authenticated user
        
    Returns:
        Template details
        
    Raises:
        HTTPException: If template not found
    """
    template = TemplateService.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return template
