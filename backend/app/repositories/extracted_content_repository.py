"""Repository for extracted content operations."""
from datetime import datetime
from typing import Optional
import json

from app.core.database import Database
from app.models.knowledge import ExtractedContent


class ExtractedContentRepository:
    """Repository for extracted content database operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, content: ExtractedContent) -> ExtractedContent:
        """Create a new extracted content record."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO extracted_content (
                    id, file_id, user_id, raw_text, page_count, word_count,
                    extraction_metadata, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content.id,
                    content.file_id,
                    content.user_id,
                    content.raw_text,
                    content.page_count,
                    content.word_count,
                    json.dumps(content.extraction_metadata),
                    content.created_at.isoformat()
                )
            )
            await self.db.connection.commit()
        
        return content
    
    async def get_by_id(self, content_id: str, user_id: str) -> Optional[ExtractedContent]:
        """
        Get extracted content by ID (user-scoped).
        
        Args:
            content_id: Content ID
            user_id: User ID (for authorization)
            
        Returns:
            ExtractedContent if found and owned by user, None otherwise
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM extracted_content
                WHERE id = ? AND user_id = ?
                """,
                (content_id, user_id)
            )
            row = await cursor.fetchone()
        
        if row:
            return ExtractedContent(
                id=row['id'],
                file_id=row['file_id'],
                user_id=row['user_id'],
                raw_text=row['raw_text'],
                page_count=row['page_count'],
                word_count=row['word_count'],
                extraction_metadata=json.loads(row['extraction_metadata']) if row['extraction_metadata'] else {},
                created_at=datetime.fromisoformat(row['created_at'])
            )
        return None
    
    async def get_by_file_id(self, file_id: str, user_id: str) -> Optional[ExtractedContent]:
        """
        Get extracted content by file ID (user-scoped).
        
        Args:
            file_id: File ID
            user_id: User ID (for authorization)
            
        Returns:
            ExtractedContent if found and owned by user, None otherwise
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM extracted_content
                WHERE file_id = ? AND user_id = ?
                """,
                (file_id, user_id)
            )
            row = await cursor.fetchone()
        
        if row:
            return ExtractedContent(
                id=row['id'],
                file_id=row['file_id'],
                user_id=row['user_id'],
                raw_text=row['raw_text'],
                page_count=row['page_count'],
                word_count=row['word_count'],
                extraction_metadata=json.loads(row['extraction_metadata']) if row['extraction_metadata'] else {},
                created_at=datetime.fromisoformat(row['created_at'])
            )
        return None
    
    async def update(self, content: ExtractedContent) -> bool:
        """
        Update extracted content.
        
        Args:
            content: Updated content object
            
        Returns:
            True if updated, False if not found
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE extracted_content
                SET raw_text = ?, page_count = ?, word_count = ?, extraction_metadata = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    content.raw_text,
                    content.page_count,
                    content.word_count,
                    json.dumps(content.extraction_metadata),
                    content.id,
                    content.user_id
                )
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    async def delete(self, content_id: str, user_id: str) -> bool:
        """
        Delete extracted content (user-scoped).
        
        Args:
            content_id: Content ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found or not owned by user
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM extracted_content WHERE id = ? AND user_id = ?",
                (content_id, user_id)
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
