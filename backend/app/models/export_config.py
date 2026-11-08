"""Export configuration models."""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ExportConfig(BaseModel):
    """Configuration for document export."""
    
    format: str  # pdf, docx, markdown, html, text
    include_metadata: bool = True
    include_table_of_contents: bool = False
    apply_template: bool = True
    custom_options: Dict[str, Any] = {}


class ExportHistoryEntry(BaseModel):
    """Record of a document export."""
    
    id: str
    document_id: str
    format: str
    timestamp: datetime
    file_size: int
    success: bool
    error_message: Optional[str] = None
    config: Optional[ExportConfig] = None
