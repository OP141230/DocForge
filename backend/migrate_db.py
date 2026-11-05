"""Database migration script for Phase 2."""
import asyncio
import aiosqlite
import os


async def migrate_database():
    """Migrate existing database to Phase 2 schema."""
    db_path = "./docforge.db"
    
    if not os.path.exists(db_path):
        print("No existing database found. New schema will be created automatically.")
        return
    
    print("Migrating database to Phase 2 schema...")
    
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        
        # Check if users table exists
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        users_exists = await cursor.fetchone()
        
        if users_exists:
            print("✓ Users table already exists")
        else:
            print("Creating users table...")
            await cursor.execute("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await cursor.execute("CREATE INDEX idx_users_email ON users(email)")
            print("✓ Users table created")
        
        # Check if sessions table exists
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        )
        sessions_exists = await cursor.fetchone()
        
        if sessions_exists:
            print("✓ Sessions table already exists")
        else:
            print("Creating sessions table...")
            await cursor.execute("""
                CREATE TABLE sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            await cursor.execute("CREATE INDEX idx_sessions_token ON sessions(session_token)")
            await cursor.execute("CREATE INDEX idx_sessions_user_id ON sessions(user_id)")
            print("✓ Sessions table created")
        
        # Check if conversations table exists
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
        )
        conversations_exists = await cursor.fetchone()
        
        if conversations_exists:
            print("✓ Conversations table already exists")
        else:
            print("Creating conversations table...")
            await cursor.execute("""
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            await cursor.execute("CREATE INDEX idx_conversations_user_id ON conversations(user_id, updated_at DESC)")
            print("✓ Conversations table created")
        
        # Check if messages table exists
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
        )
        messages_exists = await cursor.fetchone()
        
        if messages_exists:
            print("✓ Messages table already exists")
        else:
            print("Creating messages table...")
            await cursor.execute("""
                CREATE TABLE messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            await cursor.execute("CREATE INDEX idx_messages_conversation ON messages(conversation_id, sequence_number)")
            print("✓ Messages table created")
        
        # Check if documents table has user_id column
        await cursor.execute("PRAGMA table_info(documents)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'user_id' not in column_names:
            print("Adding user_id column to documents table...")
            await cursor.execute("ALTER TABLE documents ADD COLUMN user_id TEXT")
            await cursor.execute("ALTER TABLE documents ADD COLUMN conversation_id TEXT")
            await cursor.execute("CREATE INDEX idx_documents_user_id ON documents(user_id, updated_at DESC)")
            print("✓ Documents table updated")
        else:
            print("✓ Documents table already has user_id column")
        
        await db.commit()
    
    print("\n✅ Database migration complete!")
    print("\nNote: Existing documents will not have a user_id.")
    print("They will be inaccessible until assigned to a user,")
    print("or you can delete the database and start fresh.")


if __name__ == "__main__":
    asyncio.run(migrate_database())
