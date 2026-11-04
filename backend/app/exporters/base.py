"""Base exporter interface."""
from abc import ABC, abstractmethod
from typing import Dict

from app.models.document_ir import DocumentIR


class Exporter(ABC):
    """Abstract base class for document exporters."""
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Format identifier (e.g., 'docx', 'pdf', 'markdown')."""
        pass
    
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """MIME type for HTTP Content-Type header."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension including dot (e.g., '.docx', '.pdf')."""
        pass
    
    @property
    def supports_formatting(self) -> Dict[str, bool]:
        """Report which DocumentIR features this format supports."""
        return {
            "headings": True,
            "lists": True,
            "tables": True,
            "formatting": True,  # bold, italic, underline
            "links": True,
            "code_blocks": True,
            "quotes": True,
        }
    
    @abstractmethod
    def export(self, document: DocumentIR) -> bytes:
        """Convert DocumentIR to target format as bytes.
        
        Args:
            document: DocumentIR to export
            
        Returns:
            bytes: Exported document
        """
        pass
