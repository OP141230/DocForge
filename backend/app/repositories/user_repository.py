"""User repository - data access layer for users."""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.auth import User
from app.core.database import Database


class UserRepository:
    """Repository for user CRUD operations."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, full_name: str, email: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(
            id=str(uuid4()),
            full_name=full_name,
            email=email.lower(),  # Store emails in lowercase
            password_hash=password_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO users (id, full_name, email, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.full_name,
                    user.email,
                    user.password_hash,
                    user.created_at.isoformat(),
                    user.updated_at.isoformat(),
                ),
            )
            await self.db.connection.commit()
        
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM users WHERE id = ?",
                (user_id,),
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_user(row)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM users WHERE email = ?",
                (email.lower(),),
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_user(row)
    
    async def email_exists(self, email: str) -> bool:
        """Check if an email already exists."""
        user = await self.get_by_email(email)
        return user is not None
    
    async def update(self, user: User) -> User:
        """Update a user."""
        user.updated_at = datetime.utcnow()
        
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?, password_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    user.full_name,
                    user.email,
                    user.password_hash,
                    user.updated_at.isoformat(),
                    user.id,
                ),
            )
            await self.db.connection.commit()
        
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Delete a user."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            await self.db.connection.commit()
            return cursor.rowcount > 0
    
    def _row_to_user(self, row) -> User:
        """Convert database row to User model."""
        return User(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
