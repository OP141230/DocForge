"""Retrieval service for searching knowledge base using FTS5."""
from typing import List, Dict, Any, Optional
import logging

from app.core.database import Database
from app.repositories.content_chunk_repository import ContentChunkRepository
from app.repositories.knowledge_file_repository import KnowledgeFileRepository

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for searching and retrieving knowledge base content."""
    
    def __init__(self, db: Database):
        self.db = db
        self.chunk_repo = ContentChunkRepository(db)
        self.file_repo = KnowledgeFileRepository(db)
    
    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base using FTS5 full-text search with BM25 ranking.
        
        Args:
            query: Search query
            user_id: User ID (for authorization)
            limit: Maximum number of results (default 5)
            
        Returns:
            List of search results with chunk data and source metadata
        """
        if not query or not query.strip():
            return []
        
        try:
            # Search chunks
            chunk_results = await self.chunk_repo.search(query, user_id, limit)
            
            if not chunk_results:
                return []
            
            # Enrich with file metadata
            results = []
            
            for chunk_data in chunk_results:
                # Get file metadata
                file = await self.file_repo.get_by_id(chunk_data['file_id'], user_id)
                
                if not file:
                    logger.warning(f"File {chunk_data['file_id']} not found for chunk {chunk_data['id']}")
                    continue
                
                # Build result
                result = {
                    'chunk_id': chunk_data['id'],
                    'file_id': chunk_data['file_id'],
                    'original_filename': file.original_filename,
                    'file_extension': file.file_extension,
                    'chunk_text': chunk_data['chunk_text'],
                    'chunk_index': chunk_data['chunk_index'],
                    'page_number': chunk_data['page_number'],
                    'section_title': chunk_data['section_title'],
                    'relevance_score': chunk_data['relevance_score'],
                    'created_at': chunk_data['created_at']
                }
                
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise


def get_retrieval_service(db: Database) -> RetrievalService:
    """Create retrieval service instance."""
    return RetrievalService(db)
