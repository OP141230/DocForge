"""Conversation repository - data access layer."""
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from app.models.auth import Conversation
from app.core.database import Database


class ConversationRepository:
    """Repository for conversation CRUD operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, user_id: str, title: str = "New Conversation") -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            id=str(uuid4()),
            user_id=user_id,
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO conversations (id, user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conversation.id,
                    conversation.user_id,
                    conversation.title,
                    conversation.created_at.isoformat(),
                    conversation.updated_at.isoformat(),
                ),
            )
            await self.db.connection.commit()
        
        return conversation
    
    async def get_by_id(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get a conversation by ID, filtered by user_id for ownership verification."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_conversation(row)
    
    async def list_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> Tuple[List[Conversation], int]:
        """List conversations for a user with pagination."""
        async with self.db.connection.cursor() as cursor:
            # Get total count
            await cursor.execute(
                "SELECT COUNT(*) FROM conversations WHERE user_id = ?",
                (user_id,),
            )
            total = (await cursor.fetchone())[0]
            
            # Get conversations ordered by updated_at DESC
            await cursor.execute(
                """
                SELECT * FROM conversations 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset),
            )
            rows = await cursor.fetchall()
            
            conversations = [self._row_to_conversation(row) for row in rows]
            return conversations, total
    
    async def update_title(self, conversation_id: str, title: str, user_id: str) -> Optional[Conversation]:
        """Update conversation title, filtered by user_id for ownership verification."""
        updated_at = datetime.utcnow()
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE conversations 
                SET title = ?, updated_at = ? 
                WHERE id = ? AND user_id = ?
                """,
                (title, updated_at.isoformat(), conversation_id, user_id),
            )
            await self.db.connection.commit()
            
            if cursor.rowcount == 0:
                return None
            
            # Return updated conversation
            return await self.get_by_id(conversation_id, user_id)
    
    async def delete(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation, filtered by user_id for ownership verification."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    def _row_to_conversation(self, row) -> Conversation:
        """Convert database row to Conversation model."""
        return Conversation(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
