"""
OCR Service - Extract text from images using Tesseract OCR.

This service is 100% free and runs locally with no API costs.
"""
import base64
import io
import re
from typing import Optional
from PIL import Image
import pytesseract

# Set Tesseract path for Windows (default installation location)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class OCRService:
    """Service for extracting text from images using Tesseract OCR."""
    
    @staticmethod
    def extract_text_from_data_url(data_url: str) -> Optional[str]:
        """
        Extract text from a base64-encoded data URL.
        
        Args:
            data_url: Base64-encoded image data URL (e.g., "data:image/png;base64,...")
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Parse data URL to get base64 data
            if not data_url.startswith('data:image'):
                return None
            
            # Extract base64 part after comma
            base64_data = data_url.split(',', 1)[1] if ',' in data_url else data_url
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_data)
            
            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary (Tesseract works best with RGB)
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            # Clean up extracted text
            text = OCRService._clean_ocr_text(text)
            
            return text if text.strip() else None
            
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return None
    
    @staticmethod
    def _clean_ocr_text(text: str) -> str:
        """
        Clean up OCR-extracted text.
        
        - Remove excessive whitespace
        - Fix common OCR errors
        - Preserve structure (line breaks, bullets)
        """
        if not text:
            return ""
        
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> Optional[str]:
        """
        Extract text from an image file path.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Clean up
            text = OCRService._clean_ocr_text(text)
            
            return text if text.strip() else None
            
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return None
    
    @staticmethod
    def is_tesseract_available() -> bool:
        """
        Check if Tesseract is installed and available.
        
        Returns:
            True if Tesseract is available, False otherwise
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
