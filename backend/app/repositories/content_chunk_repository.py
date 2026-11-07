"""Repository for content chunk operations with FTS5 search."""
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import re

from app.core.database import Database
from app.models.knowledge import ContentChunk


def _to_fts_query(query: str, max_tokens: int = 24) -> Optional[str]:
    """Convert free text into a safe FTS5 MATCH expression."""
    tokens = re.findall(r"[A-Za-z0-9_]+", query or "")
    unique: List[str] = []
    seen = set()
    for token in tokens:
        if len(token) < 2:
            continue
        lowered = token.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(token)
    if not unique:
        return None
    return " OR ".join(f'"{token}"' for token in unique[:max_tokens])


class ContentChunkRepository:
    """Repository for content chunk database operations with FTS5 integration."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, chunk: ContentChunk) -> ContentChunk:
        """
        Create a new content chunk record.
        
        Note: The FTS5 table is automatically populated via trigger.
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO content_chunks (
                    id, file_id, user_id, chunk_index, chunk_text, chunk_size,
                    page_number, section_title, metadata, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.id,
                    chunk.file_id,
                    chunk.user_id,
                    chunk.chunk_index,
                    chunk.chunk_text,
                    chunk.chunk_size,
                    chunk.page_number,
                    chunk.section_title,
                    json.dumps(chunk.metadata),
                    chunk.created_at.isoformat()
                )
            )
            await self.db.connection.commit()
        
        return chunk
    
    async def get_by_content_id(self, content_id: str, user_id: str) -> List[ContentChunk]:
        """
        Get all chunks for an extracted content (user-scoped).
        
        Note: This queries by file_id since chunks reference files directly.
        
        Args:
            content_id: Extracted content ID (treated as file_id)
            user_id: User ID (for authorization)
            
        Returns:
            List of content chunks
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM content_chunks
                WHERE file_id = ? AND user_id = ?
                ORDER BY chunk_index
                """,
                (content_id, user_id)
            )
            rows = await cursor.fetchall()
        
        return [
            ContentChunk(
                id=row['id'],
                file_id=row['file_id'],
                user_id=row['user_id'],
                chunk_index=row['chunk_index'],
                chunk_text=row['chunk_text'],
                chunk_size=row['chunk_size'],
                page_number=row['page_number'],
                section_title=row['section_title'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                created_at=datetime.fromisoformat(row['created_at'])
            )
            for row in rows
        ]
    
    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        file_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Full-text search on content chunks using FTS5 with BM25 ranking.
        
        Args:
            query: Search query
            user_id: User ID (for authorization)
            limit: Maximum number of results
            file_ids: Optional allow-list of knowledge file IDs. Used by Phase 5
                so a research session only reads the files the user chose
                instead of every file in their knowledge base.
            
        Returns:
            List of dictionaries with chunk data and relevance scores
        """
        # FTS5 MATCH treats raw text as a query language: punctuation such as
        # "?", "'" or "-" raises "fts5: syntax error". Research questions and
        # user search boxes routinely contain those characters, so the query is
        # reduced to quoted alphanumeric tokens joined with OR (BM25 still ranks
        # the best matches first).
        fts_query = _to_fts_query(query)
        if not fts_query:
            return []

        parameters: List[Any] = [fts_query, user_id]
        file_filter = ""
        if file_ids:
            placeholders = ",".join("?" for _ in file_ids)
            file_filter = f" AND c.file_id IN ({placeholders})"
            parameters.extend(file_ids)
        parameters.append(limit)

        async with self.db.connection.cursor() as cursor:
            # Use FTS5 MATCH for full-text search with BM25 ranking
            # Join with main table to get metadata and enforce user scope
            await cursor.execute(
                f"""
                SELECT 
                    c.id,
                    c.file_id,
                    c.user_id,
                    c.chunk_index,
                    c.chunk_text,
                    c.chunk_size,
                    c.page_number,
                    c.section_title,
                    c.metadata,
                    c.created_at,
                    fts.rank as relevance_score
                FROM content_chunks_fts fts
                INNER JOIN content_chunks c ON fts.rowid = c.rowid
                WHERE fts.chunk_text MATCH ? AND c.user_id = ?{file_filter}
                ORDER BY fts.rank
                LIMIT ?
                """,
                parameters
            )
            rows = await cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'file_id': row['file_id'],
                'user_id': row['user_id'],
                'chunk_index': row['chunk_index'],
                'chunk_text': row['chunk_text'],
                'chunk_size': row['chunk_size'],
                'page_number': row['page_number'],
                'section_title': row['section_title'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                'created_at': row['created_at'],
                'relevance_score': abs(row['relevance_score'])  # FTS5 rank is negative, convert to positive
            })
        
        return results
    
    async def delete_by_content_id(self, content_id: str, user_id: str) -> bool:
        """
        Delete all chunks for an extracted content (user-scoped).
        
        Note: This deletes by file_id since chunks reference files directly.
        FTS5 entries are automatically deleted via trigger.
        
        Args:
            content_id: Extracted content ID (treated as file_id)
            user_id: User ID (for authorization)
            
        Returns:
            True if any chunks were deleted
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM content_chunks WHERE file_id = ? AND user_id = ?",
                (content_id, user_id)
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
