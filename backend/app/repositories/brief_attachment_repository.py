"""Repository for brief-file attachment operations."""
from datetime import datetime
from typing import List
from uuid import uuid4

from app.core.database import Database
from app.models.knowledge import KnowledgeFile


class BriefAttachmentRepository:
    """Repository for managing brief-file attachments."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, brief_id: str, file_id: str, user_id: str) -> str:
        """
        Create a new brief-file attachment.
        
        Args:
            brief_id: Document brief ID
            file_id: Knowledge file ID
            user_id: User ID (for authorization)
            
        Returns:
            Attachment ID
        """
        attachment_id = str(uuid4())
        attached_at = datetime.utcnow().isoformat()
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO brief_file_attachments (id, brief_id, file_id, user_id, attached_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (attachment_id, brief_id, file_id, user_id, attached_at)
            )
            await self.db.connection.commit()
        
        return attachment_id
    
    async def get_by_brief_id(self, brief_id: str, user_id: str) -> List[KnowledgeFile]:
        """
        Get all files attached to a brief (user-scoped).
        
        Args:
            brief_id: Document brief ID
            user_id: User ID (for authorization)
            
        Returns:
            List of KnowledgeFile objects
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT kf.* FROM knowledge_files kf
                INNER JOIN brief_file_attachments bfa ON kf.id = bfa.file_id
                WHERE bfa.brief_id = ? AND bfa.user_id = ?
                ORDER BY bfa.attached_at DESC
                """,
                (brief_id, user_id)
            )
            rows = await cursor.fetchall()
        
        files = [
            KnowledgeFile(
                id=row['id'],
                user_id=row['user_id'],
                conversation_id=row['conversation_id'],
                original_filename=row['original_filename'],
                stored_filename=row['stored_filename'],
                file_extension=row['file_extension'],
                mime_type=row['mime_type'],
                file_size_bytes=row['file_size_bytes'],
                content_hash=row['content_hash'],
                storage_path=row['storage_path'],
                upload_status=row['upload_status'],
                extraction_status=row['extraction_status'],
                extraction_error=row['extraction_error'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
            for row in rows
        ]
        
        return files
    
    async def delete(self, brief_id: str, file_id: str, user_id: str) -> bool:
        """
        Remove a specific file attachment from a brief (user-scoped).
        
        Args:
            brief_id: Document brief ID
            file_id: Knowledge file ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found or unauthorized
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                DELETE FROM brief_file_attachments
                WHERE brief_id = ? AND file_id = ? AND user_id = ?
                """,
                (brief_id, file_id, user_id)
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    async def delete_by_brief_id(self, brief_id: str, user_id: str) -> int:
        """
        Remove all file attachments from a brief (user-scoped).
        
        Args:
            brief_id: Document brief ID
            user_id: User ID (for authorization)
            
        Returns:
            Number of attachments deleted
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                DELETE FROM brief_file_attachments
                WHERE brief_id = ? AND user_id = ?
                """,
                (brief_id, user_id)
            )
            await self.db.connection.commit()
            return cursor.rowcount
    
    async def exists(self, brief_id: str, file_id: str, user_id: str) -> bool:
        """
        Check if a specific attachment exists (user-scoped).
        
        Args:
            brief_id: Document brief ID
            file_id: Knowledge file ID
            user_id: User ID (for authorization)
            
        Returns:
            True if attachment exists, False otherwise
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT COUNT(*) as count FROM brief_file_attachments
                WHERE brief_id = ? AND file_id = ? AND user_id = ?
                """,
                (brief_id, file_id, user_id)
            )
            row = await cursor.fetchone()
            return row['count'] > 0 if row else False
