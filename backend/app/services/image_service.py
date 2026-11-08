"""Image upload and storage service."""
import os
import uuid
import base64
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


class ImageService:
    """Service for handling document image uploads and storage."""
    
    def __init__(self, upload_dir: str = "uploads/images"):
        """
        Initialize image service.
        
        Args:
            upload_dir: Directory to store uploaded images
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Allowed image formats
        self.allowed_formats = {"PNG", "JPEG", "JPG", "GIF", "WEBP", "BMP"}
        
        # Maximum file size (10MB)
        self.max_file_size = 10 * 1024 * 1024
    
    def save_image(
        self,
        image_data: bytes,
        filename: Optional[str] = None,
        optimize: bool = True,
        max_width: Optional[int] = 2000,
        max_height: Optional[int] = 2000
    ) -> Tuple[str, dict]:
        """
        Save an uploaded image.
        
        Args:
            image_data: Raw image bytes
            filename: Original filename (optional)
            optimize: Whether to optimize the image
            max_width: Maximum width for resizing
            max_height: Maximum height for resizing
            
        Returns:
            Tuple of (file_path, metadata)
            
        Raises:
            ValueError: If image is invalid or too large
        """
        # Check file size
        if len(image_data) > self.max_file_size:
            raise ValueError(f"Image size exceeds maximum of {self.max_file_size / 1024 / 1024}MB")
        
        # Load and validate image
        try:
            image = Image.open(io.BytesIO(image_data))
            image.verify()  # Verify it's a valid image
            
            # Reopen after verify (verify closes the file)
            image = Image.open(io.BytesIO(image_data))
            
        except Exception as e:
            logger.error(f"Invalid image data: {e}")
            raise ValueError("Invalid image file")
        
        # Check format
        if image.format not in self.allowed_formats:
            raise ValueError(f"Unsupported format: {image.format}. Allowed: {', '.join(self.allowed_formats)}")
        
        # Resize if needed
        original_size = image.size
        if max_width or max_height:
            image = self._resize_image(image, max_width, max_height)
        
        # Convert RGBA to RGB if saving as JPEG
        if image.format == "JPEG" and image.mode == "RGBA":
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = rgb_image
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = image.format.lower()
        if extension == "jpeg":
            extension = "jpg"
        saved_filename = f"{file_id}.{extension}"
        file_path = self.upload_dir / saved_filename
        
        # Save image
        save_kwargs = {"format": image.format}
        if optimize:
            save_kwargs["optimize"] = True
            if image.format == "JPEG":
                save_kwargs["quality"] = 85
        
        image.save(file_path, **save_kwargs)
        
        # Get final file size
        file_size = file_path.stat().st_size
        
        metadata = {
            "id": file_id,
            "filename": filename or saved_filename,
            "format": image.format,
            "width": image.size[0],
            "height": image.size[1],
            "original_width": original_size[0],
            "original_height": original_size[1],
            "file_size": file_size,
            "optimized": optimize,
            "path": str(file_path.relative_to(self.upload_dir.parent))
        }
        
        logger.info(f"Saved image {file_id} ({image.format}, {image.size[0]}x{image.size[1]}, {file_size} bytes)")
        
        return str(file_path.relative_to(self.upload_dir.parent)), metadata
    
    def save_base64_image(
        self,
        base64_data: str,
        filename: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, dict]:
        """
        Save a base64-encoded image.
        
        Args:
            base64_data: Base64-encoded image string (with or without data URI prefix)
            filename: Original filename (optional)
            **kwargs: Additional arguments passed to save_image
            
        Returns:
            Tuple of (file_path, metadata)
        """
        # Remove data URI prefix if present
        if "," in base64_data:
            base64_data = base64_data.split(",", 1)[1]
        
        try:
            image_data = base64.b64decode(base64_data)
        except Exception as e:
            logger.error(f"Invalid base64 data: {e}")
            raise ValueError("Invalid base64 image data")
        
        return self.save_image(image_data, filename, **kwargs)
    
    def _resize_image(
        self,
        image: Image.Image,
        max_width: Optional[int],
        max_height: Optional[int]
    ) -> Image.Image:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            image: PIL Image
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Resized image
        """
        width, height = image.size
        
        # Calculate scaling factor
        scale = 1.0
        if max_width and width > max_width:
            scale = min(scale, max_width / width)
        if max_height and height > max_height:
            scale = min(scale, max_height / height)
        
        # Resize if needed
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        return image
    
    def get_image_path(self, file_id: str) -> Optional[Path]:
        """
        Get the full path to an image by ID.
        
        Args:
            file_id: Image file ID
            
        Returns:
            Path to image file or None if not found
        """
        # Search for file with this ID
        for ext in ["png", "jpg", "jpeg", "gif", "webp", "bmp"]:
            file_path = self.upload_dir / f"{file_id}.{ext}"
            if file_path.exists():
                return file_path
        return None
    
    def delete_image(self, file_id: str) -> bool:
        """
        Delete an image by ID.
        
        Args:
            file_id: Image file ID
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self.get_image_path(file_id)
        if file_path and file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted image {file_id}")
            return True
        return False
