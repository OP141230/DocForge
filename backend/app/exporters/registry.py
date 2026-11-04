"""Exporter registry."""
from typing import Dict, Optional, List

from .base import Exporter


class ExporterRegistry:
    """Singleton registry for document exporters."""
    
    _instance = None
    _exporters: Dict[str, Exporter] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, exporter: Exporter) -> None:
        """Register an exporter."""
        self._exporters[exporter.format_name] = exporter
    
    def get_exporter(self, format_name: str) -> Optional[Exporter]:
        """Get an exporter by format name."""
        return self._exporters.get(format_name)
    
    def list_formats(self) -> List[str]:
        """List all registered format names."""
        return list(self._exporters.keys())
    
    def get_capabilities(self, format_name: str) -> Optional[Dict[str, bool]]:
        """Get capabilities of a specific format."""
        exporter = self.get_exporter(format_name)
        return exporter.supports_formatting if exporter else None
    
    def clear(self) -> None:
        """Clear all registered exporters (for testing)."""
        self._exporters.clear()
