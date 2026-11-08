"""Message repository - data access layer."""
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4
import json

from app.models.auth import Message, MessageAttachment
from app.core.database import Database


class MessageRepository:
    """Repository for message CRUD operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(
        self, 
        conversation_id: str, 
        role: str, 
        content: str, 
        sequence_number: int,
        attachments: List[MessageAttachment] = None
    ) -> Message:
        """Create a new message with optional attachments."""
        if attachments is None:
            attachments = []
            
        message = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            attachments=attachments,
            sequence_number=sequence_number,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_deleted=False,
        )
        
        # Serialize attachments to JSON
        attachments_json = json.dumps([att.dict() for att in attachments])
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, attachments, sequence_number, created_at, updated_at, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.conversation_id,
                    message.role,
                    message.content,
                    attachments_json,
                    message.sequence_number,
                    message.created_at.isoformat(),
                    message.updated_at.isoformat(),
                    0,  # SQLite uses 0/1 for boolean
                ),
            )
            await self.db.connection.commit()
        
        return message
    
    async def list_by_conversation(self, conversation_id: str, limit: int = 100, offset: int = 0) -> Tuple[List[Message], int]:
        """List messages for a conversation with pagination, excluding deleted messages."""
        async with self.db.connection.cursor() as cursor:
            # Get total count of non-deleted messages
            await cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE conversation_id = ? AND is_deleted = 0",
                (conversation_id,),
            )
            total = (await cursor.fetchone())[0]
            
            # Get messages ordered by sequence_number ASC
            await cursor.execute(
                """
                SELECT * FROM messages 
                WHERE conversation_id = ? AND is_deleted = 0 
                ORDER BY sequence_number ASC 
                LIMIT ? OFFSET ?
                """,
                (conversation_id, limit, offset),
            )
            rows = await cursor.fetchall()
            
            messages = [self._row_to_message(row) for row in rows]
            return messages, total
    
    async def get_latest_sequence(self, conversation_id: str) -> int:
        """Get the latest sequence number for a conversation."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT COALESCE(MAX(sequence_number), 0) FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def delete_by_conversation(self, conversation_id: str) -> bool:
        """Delete all messages for a conversation (hard delete)."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    def _row_to_message(self, row) -> Message:
        """Convert database row to Message model."""
        # Parse attachments from JSON
        attachments_json = row["attachments"] if "attachments" in row.keys() else "[]"
        attachments_data = json.loads(attachments_json) if attachments_json else []
        attachments = [MessageAttachment(**att) for att in attachments_data]
        
        return Message(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            attachments=attachments,
            sequence_number=row["sequence_number"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            is_deleted=bool(row["is_deleted"]),
        )
