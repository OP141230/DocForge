"""Session repository - data access layer for sessions."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.auth import Session
from app.core.database import Database


class SessionRepository:
    """Repository for session management."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, user_id: str, session_token: str, expires_at: datetime) -> Session:
        """Create a new session."""
        session = Session(
            id=str(uuid4()),
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO sessions (id, user_id, session_token, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.user_id,
                    session.session_token,
                    session.expires_at.isoformat(),
                    session.created_at.isoformat(),
                ),
            )
            await self.db.connection.commit()
        
        return session
    
    async def get_by_token(self, session_token: str) -> Optional[Session]:
        """Retrieve a session by token."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM sessions WHERE session_token = ?",
                (session_token,),
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_session(row)
    
    async def delete_by_token(self, session_token: str) -> bool:
        """Delete a session by token."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM sessions WHERE session_token = ?",
                (session_token,),
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete all sessions for a user."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM sessions WHERE user_id = ?",
                (user_id,),
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    async def cleanup_expired(self) -> int:
        """Delete expired sessions."""
        now = datetime.utcnow().isoformat()
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM sessions WHERE expires_at < ?",
                (now,),
            )
            await self.db.connection.commit()
            return cursor.rowcount
    
    def is_expired(self, session: Session) -> bool:
        """Check if a session is expired."""
        return datetime.utcnow() > session.expires_at
    
    def _row_to_session(self, row) -> Session:
        """Convert database row to Session model."""
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            session_token=row["session_token"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
