"""Database connection and initialization."""
import aiosqlite
import os
from pathlib import Path
from typing import Optional


class Database:
    """SQLite database manager."""
    
    def __init__(self, db_path: str = "./docforge.db"):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Establish database connection and initialize schema."""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._init_schema()
    
    async def disconnect(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def _init_schema(self):
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "db_schema.sql"
        if schema_path.exists():
            async with self._connection.cursor() as cursor:
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                await cursor.executescript(schema_sql)
                await self._connection.commit()
    
    @property
    def connection(self) -> aiosqlite.Connection:
        """Get database connection."""
        if not self._connection:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection


# Global database instance
_db: Optional[Database] = None


async def get_database() -> Database:
    """Get or create global database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.connect()
    return _db


async def close_database():
    """Close global database instance."""
    global _db
    if _db:
        await _db.disconnect()
        _db = None
