"""Repository for knowledge file operations."""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.core.database import Database
from app.models.knowledge import KnowledgeFile


class KnowledgeFileRepository:
    """Repository for knowledge file database operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, file: KnowledgeFile) -> KnowledgeFile:
        """Create a new knowledge file record."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO knowledge_files (
                    id, user_id, conversation_id, original_filename, stored_filename,
                    file_extension, mime_type, file_size_bytes, content_hash, storage_path,
                    upload_status, extraction_status, extraction_error, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file.id, file.user_id, file.conversation_id, file.original_filename,
                    file.stored_filename, file.file_extension, file.mime_type,
                    file.file_size_bytes, file.content_hash, file.storage_path,
                    file.upload_status, file.extraction_status, file.extraction_error,
                    file.created_at.isoformat(), file.updated_at.isoformat()
                )
            )
            await self.db.connection.commit()
        
        return file
    
    async def get_by_id(self, file_id: str, user_id: str) -> Optional[KnowledgeFile]:
        """
        Get file by ID (user-scoped).
        
        Args:
            file_id: File ID
            user_id: User ID (for authorization)
            
        Returns:
            KnowledgeFile if found and owned by user, None otherwise
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM knowledge_files
                WHERE id = ? AND user_id = ?
                """,
                (file_id, user_id)
            )
            row = await cursor.fetchone()
        
        if row:
            return KnowledgeFile(
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
        return None
    
    async def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        conversation_id: Optional[str] = None,
        file_extension: Optional[str] = None
    ) -> tuple[List[KnowledgeFile], int]:
        """
        List files for a user with pagination and filters.
        
        Args:
            user_id: User ID
            limit: Maximum number of files to return
            offset: Number of files to skip
            conversation_id: Optional filter by conversation
            file_extension: Optional filter by file extension
            
        Returns:
            Tuple of (list of files, total count)
        """
        # Build query with optional filters
        query = "SELECT * FROM knowledge_files WHERE user_id = ?"
        params = [user_id]
        
        if conversation_id:
            query += " AND conversation_id = ?"
            params.append(conversation_id)
        
        if file_extension:
            query += " AND file_extension = ?"
            params.append(file_extension)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Get files
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(query, params)
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
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM knowledge_files WHERE user_id = ?"
        count_params = [user_id]
        
        if conversation_id:
            count_query += " AND conversation_id = ?"
            count_params.append(conversation_id)
        
        if file_extension:
            count_query += " AND file_extension = ?"
            count_params.append(file_extension)
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(count_query, count_params)
            row = await cursor.fetchone()
            total = row['total'] if row else 0
        
        return files, total
    
    async def update_status(
        self,
        file_id: str,
        user_id: str,
        upload_status: Optional[str] = None,
        extraction_status: Optional[str] = None,
        extraction_error: Optional[str] = None
    ) -> bool:
        """
        Update file processing status.
        
        Args:
            file_id: File ID
            user_id: User ID (for authorization)
            upload_status: New upload status
            extraction_status: New extraction status
            extraction_error: Error message if extraction failed
            
        Returns:
            True if updated, False if file not found or not owned by user
        """
        updates = []
        params = []
        
        if upload_status is not None:
            updates.append("upload_status = ?")
            params.append(upload_status)
        
        if extraction_status is not None:
            updates.append("extraction_status = ?")
            params.append(extraction_status)
        
        if extraction_error is not None:
            updates.append("extraction_error = ?")
            params.append(extraction_error)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        # Add WHERE clause params
        params.extend([file_id, user_id])
        
        query = f"UPDATE knowledge_files SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(query, params)
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    async def delete(self, file_id: str, user_id: str) -> bool:
        """
        Delete a file (user-scoped).
        
        Args:
            file_id: File ID
            user_id: User ID (for authorization)
            
        Returns:
            True if deleted, False if not found or not owned by user
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM knowledge_files WHERE id = ? AND user_id = ?",
                (file_id, user_id)
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    async def get_by_hash(self, content_hash: str, user_id: str) -> Optional[KnowledgeFile]:
        """
        Find existing file by content hash (for deduplication).
        
        Args:
            content_hash: SHA-256 hash of file content
            user_id: User ID
            
        Returns:
            Existing file if found, None otherwise
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM knowledge_files
                WHERE content_hash = ? AND user_id = ?
                LIMIT 1
                """,
                (content_hash, user_id)
            )
            row = await cursor.fetchone()
        
        if row:
            return KnowledgeFile(
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
        return None
