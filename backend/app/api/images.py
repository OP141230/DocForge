"""Image upload API routes."""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from app.services.image_service import ImageService
from app.core.auth import get_current_user
from app.models.auth import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
image_service = ImageService()


class Base64ImageUpload(BaseModel):
    """Base64-encoded image upload request."""
    image_data: str
    filename: Optional[str] = None
    optimize: bool = True
    max_width: Optional[int] = 2000
    max_height: Optional[int] = 2000


class ImageUploadResponse(BaseModel):
    """Image upload response."""
    success: bool
    image_id: str
    url: str
    width: int
    height: int
    file_size: int
    format: str


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image file.
    
    Args:
        file: Uploaded image file
        current_user: Authenticated user
        
    Returns:
        Upload result with image URL
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        # Read file data
        image_data = await file.read()
        
        # Save image
        file_path, metadata = image_service.save_image(
            image_data,
            filename=file.filename,
            optimize=True,
            max_width=2000,
            max_height=2000
        )
        
        # Construct URL
        image_url = f"/api/images/{metadata['id']}"
        
        return ImageUploadResponse(
            success=True,
            image_id=metadata["id"],
            url=image_url,
            width=metadata["width"],
            height=metadata["height"],
            file_size=metadata["file_size"],
            format=metadata["format"]
        )
        
    except ValueError as e:
        logger.error(f"Image upload validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Image upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload image")


@router.post("/upload-base64", response_model=ImageUploadResponse)
async def upload_base64_image(
    request: Base64ImageUpload,
    current_user: User = Depends(get_current_user)
):
    """
    Upload a base64-encoded image.
    
    Args:
        request: Base64 image upload request
        current_user: Authenticated user
        
    Returns:
        Upload result with image URL
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        # Save image
        file_path, metadata = image_service.save_base64_image(
            request.image_data,
            filename=request.filename,
            optimize=request.optimize,
            max_width=request.max_width,
            max_height=request.max_height
        )
        
        # Construct URL
        image_url = f"/api/images/{metadata['id']}"
        
        return ImageUploadResponse(
            success=True,
            image_id=metadata["id"],
            url=image_url,
            width=metadata["width"],
            height=metadata["height"],
            file_size=metadata["file_size"],
            format=metadata["format"]
        )
        
    except ValueError as e:
        logger.error(f"Base64 image upload validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Base64 image upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload image")


@router.get("/{image_id}")
async def get_image(
    image_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get an image by ID.
    
    Args:
        image_id: Image identifier
        current_user: Authenticated user
        
    Returns:
        Image file
        
    Raises:
        HTTPException: If image not found
    """
    file_path = image_service.get_image_path(image_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path)


@router.delete("/{image_id}")
async def delete_image(
    image_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an image by ID.
    
    Args:
        image_id: Image identifier
        current_user: Authenticated user
        
    Returns:
        Success status
        
    Raises:
        HTTPException: If image not found
    """
    success = image_service.delete_image(image_id)
    if not success:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return {"success": True, "message": "Image deleted successfully"}
