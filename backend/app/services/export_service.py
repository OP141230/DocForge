"""Export service for managing document exports."""
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import json

from app.models.document_ir import DocumentIR
from app.models.export_config import ExportConfig, ExportHistoryEntry
from app.exporters.factory import get_exporter


class ExportService:
    """Service for exporting documents with configuration and history tracking."""
    
    def __init__(self, history_dir: str = "data/export_history"):
        """
        Initialize export service.
        
        Args:
            history_dir: Directory to store export history
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_document(
        self,
        document: DocumentIR,
        config: ExportConfig
    ) -> tuple[bytes, ExportHistoryEntry]:
        """
        Export a document with given configuration.
        
        Args:
            document: Document to export
            config: Export configuration
            
        Returns:
            Tuple of (exported bytes, history entry)
            
        Raises:
            ValueError: If format is not supported
            Exception: If export fails
        """
        try:
            # Get exporter
            exporter = get_exporter(config.format)
            
            # Export document
            export_bytes = exporter.export(document)
            
            # Create history entry
            entry = ExportHistoryEntry(
                id=str(uuid.uuid4()),
                document_id=document.id,
                format=config.format,
                timestamp=datetime.utcnow(),
                file_size=len(export_bytes),
                success=True,
                config=config
            )
            
            # Save history
            await self._save_history_entry(entry)
            
            return export_bytes, entry
            
        except Exception as e:
            # Create failed history entry
            entry = ExportHistoryEntry(
                id=str(uuid.uuid4()),
                document_id=document.id,
                format=config.format,
                timestamp=datetime.utcnow(),
                file_size=0,
                success=False,
                error_message=str(e),
                config=config
            )
            
            await self._save_history_entry(entry)
            raise
    
    async def get_export_history(
        self,
        document_id: str,
        limit: int = 20
    ) -> List[ExportHistoryEntry]:
        """
        Get export history for a document.
        
        Args:
            document_id: Document ID
            limit: Maximum number of entries to return
            
        Returns:
            List of history entries, newest first
        """
        history_file = self.history_dir / f"{document_id}_history.json"
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
            
            entries = [ExportHistoryEntry(**entry) for entry in data]
            entries.sort(key=lambda x: x.timestamp, reverse=True)
            
            return entries[:limit]
            
        except Exception as e:
            return []
    
    async def _save_history_entry(self, entry: ExportHistoryEntry):
        """Save an export history entry."""
        history_file = self.history_dir / f"{entry.document_id}_history.json"
        
        # Load existing history
        if history_file.exists():
            with open(history_file, 'r') as f:
                data = json.load(f)
        else:
            data = []
        
        # Add new entry
        data.append(entry.model_dump(mode='json'))
        
        # Keep only last 100 entries per document
        if len(data) > 100:
            data = sorted(data, key=lambda x: x['timestamp'], reverse=True)[:100]
        
        # Save
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return ["pdf", "docx", "markdown", "html", "text"]
    
    def get_format_info(self, format_name: str) -> Optional[dict]:
        """
        Get information about an export format.
        
        Args:
            format_name: Format name
            
        Returns:
            Format information dict or None if not found
        """
        formats = {
            "pdf": {
                "name": "PDF",
                "description": "Portable Document Format - Best for printing and sharing",
                "mime_type": "application/pdf",
                "extension": ".pdf",
                "supports_formatting": True,
                "supports_images": True,
                "supports_page_layout": True
            },
            "docx": {
                "name": "Microsoft Word",
                "description": "Word document format - Editable in Microsoft Word and compatible editors",
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "extension": ".docx",
                "supports_formatting": True,
                "supports_images": True,
                "supports_page_layout": True
            },
            "html": {
                "name": "HTML",
                "description": "Web page format - View in any browser",
                "mime_type": "text/html",
                "extension": ".html",
                "supports_formatting": True,
                "supports_images": True,
                "supports_page_layout": False
            },
            "markdown": {
                "name": "Markdown",
                "description": "Plain text format with simple formatting - Great for GitHub and technical docs",
                "mime_type": "text/markdown",
                "extension": ".md",
                "supports_formatting": True,
                "supports_images": True,
                "supports_page_layout": False
            },
            "text": {
                "name": "Plain Text",
                "description": "Simple text format - No formatting, maximum compatibility",
                "mime_type": "text/plain",
                "extension": ".txt",
                "supports_formatting": False,
                "supports_images": False,
                "supports_page_layout": False
            }
        }
        
        return formats.get(format_name)
