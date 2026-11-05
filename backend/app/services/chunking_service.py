"""Chunking service for splitting extracted content into searchable chunks."""
import re
from typing import List, Optional
from uuid import uuid4

from app.models.knowledge import ExtractedContent, ContentChunk


class ChunkingService:
    """Service for chunking extracted content with overlap."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize chunking service.
        
        Args:
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_content(self, extracted_content: ExtractedContent) -> List[ContentChunk]:
        """
        Split extracted content into chunks with overlap.
        
        Algorithm:
        - Split text into chunks of ~1000 characters
        - Overlap adjacent chunks by 200 characters
        - Preserve page/section metadata from extraction
        - Handle edge cases (content shorter than chunk size)
        
        Args:
            extracted_content: Extracted content to chunk
            
        Returns:
            List of content chunks
        """
        text = extracted_content.raw_text
        
        # Handle empty content
        if not text or not text.strip():
            return []
        
        # Handle content shorter than chunk size
        if len(text) <= self.chunk_size:
            return [
                ContentChunk(
                    id=str(uuid4()),
                    file_id=extracted_content.file_id,
                    user_id=extracted_content.user_id,
                    chunk_index=0,
                    chunk_text=text,
                    chunk_size=len(text),
                    page_number=self._extract_page_number(text, extracted_content),
                    section_title=self._extract_section_title(text),
                    metadata={
                        'total_chunks': 1,
                        'is_complete_document': True
                    }
                )
            ]
        
        # Split into overlapping chunks
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(text):
            # Determine end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                end = self._find_break_point(text, start, end)
            else:
                end = len(text)
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            # Skip empty chunks
            if not chunk_text:
                start = end
                continue
            
            # Create chunk
            chunk = ContentChunk(
                id=str(uuid4()),
                file_id=extracted_content.file_id,
                user_id=extracted_content.user_id,
                chunk_index=chunk_index,
                chunk_text=chunk_text,
                chunk_size=len(chunk_text),
                page_number=self._extract_page_number(chunk_text, extracted_content),
                section_title=self._extract_section_title(chunk_text),
                metadata={
                    'start_position': start,
                    'end_position': end,
                    'total_chunks': None  # Will be set after all chunks created
                }
            )
            
            chunks.append(chunk)
            chunk_index += 1
            
            # Move start position (with overlap)
            start = end - self.overlap
            
            # Ensure we make progress
            if start <= chunks[-1].metadata.get('start_position', 0):
                start = end
        
        # Update total_chunks metadata
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.metadata['total_chunks'] = total_chunks
        
        return chunks
    
    def _find_break_point(self, text: str, start: int, ideal_end: int) -> int:
        """
        Find a good break point near the ideal end position.
        
        Prioritizes breaking at:
        1. Sentence boundaries (. ! ?)
        2. Paragraph boundaries (\n\n)
        3. Line boundaries (\n)
        4. Word boundaries (space)
        5. Character boundary (fallback)
        
        Args:
            text: Full text
            start: Start position of chunk
            ideal_end: Ideal end position
            
        Returns:
            Actual end position
        """
        # Search window: look back up to 100 characters from ideal end
        search_start = max(start, ideal_end - 100)
        search_text = text[search_start:ideal_end + 1]
        
        # Try to find sentence boundary
        sentence_end = self._find_last_match(search_text, r'[.!?]\s+')
        if sentence_end is not None:
            return search_start + sentence_end
        
        # Try to find paragraph boundary
        para_end = search_text.rfind('\n\n')
        if para_end > 0:
            return search_start + para_end + 2
        
        # Try to find line boundary
        line_end = search_text.rfind('\n')
        if line_end > 0:
            return search_start + line_end + 1
        
        # Try to find word boundary
        space_end = search_text.rfind(' ')
        if space_end > 0:
            return search_start + space_end + 1
        
        # Fallback to ideal end
        return ideal_end
    
    def _find_last_match(self, text: str, pattern: str) -> Optional[int]:
        """
        Find the position after the last match of a regex pattern.
        
        Args:
            text: Text to search
            pattern: Regex pattern
            
        Returns:
            Position after last match, or None if no match
        """
        matches = list(re.finditer(pattern, text))
        if matches:
            last_match = matches[-1]
            return last_match.end()
        return None
    
    def _extract_page_number(
        self,
        chunk_text: str,
        extracted_content: ExtractedContent
    ) -> Optional[int]:
        """
        Extract page number from chunk text if available.
        
        Looks for patterns like [Page N] that extraction service adds.
        
        Args:
            chunk_text: Chunk text
            extracted_content: Original extracted content
            
        Returns:
            Page number if found, None otherwise
        """
        # Look for [Page N] markers
        match = re.search(r'\[Page (\d+)\]', chunk_text)
        if match:
            return int(match.group(1))
        
        return None
    
    def _extract_section_title(self, chunk_text: str) -> Optional[str]:
        """
        Extract section title from chunk text if available.
        
        Looks for markdown-style headers (## Title) at the beginning.
        
        Args:
            chunk_text: Chunk text
            
        Returns:
            Section title if found, None otherwise
        """
        lines = chunk_text.split('\n', 3)
        
        for line in lines[:3]:
            line = line.strip()
            
            # Check for markdown header
            if line.startswith('##'):
                title = line.lstrip('#').strip()
                if title:
                    return title[:200]  # Limit title length
        
        return None


# Global chunking service instance
_chunking_service: Optional[ChunkingService] = None


def get_chunking_service() -> ChunkingService:
    """Get or create global chunking service."""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
