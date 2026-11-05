"""Database migration script for Phase 3 - DocumentBrief system."""
import asyncio
import aiosqlite
import os


async def migrate_phase3():
    """Migrate database to Phase 3 schema."""
    # Support running from project root or backend directory
    if os.path.exists("./docforge.db"):
        db_path = "./docforge.db"
    elif os.path.exists("./backend/docforge.db"):
        db_path = "./backend/docforge.db"
    else:
        db_path = "./docforge.db"
    
    if not os.path.exists(db_path):
        print("No existing database found. Run the application first to create initial schema.")
        return
    
    print("Migrating database to Phase 3 schema...")
    
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.cursor()
        
        # Check if document_briefs table exists
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='document_briefs'"
        )
        table_exists = await cursor.fetchone()
        
        if table_exists:
            print("✓ document_briefs table already exists")
        else:
            print("Creating document_briefs table...")
            await cursor.execute("""
                CREATE TABLE document_briefs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    conversation_id TEXT,
                    document_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    purpose TEXT,
                    audience TEXT,
                    language TEXT DEFAULT 'en',
                    desired_length TEXT,
                    tone TEXT,
                    writing_style TEXT,
                    document_specific_data TEXT NOT NULL DEFAULT '{}',
                    required_sections TEXT NOT NULL DEFAULT '[]',
                    important_points TEXT NOT NULL DEFAULT '[]',
                    topics_to_avoid TEXT NOT NULL DEFAULT '[]',
                    additional_instructions TEXT,
                    citation_style TEXT,
                    outline TEXT,
                    outline_approved INTEGER DEFAULT 0,
                    outline_approved_at TEXT,
                    document_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
                )
            """)
            
            # Create indexes for performance
            await cursor.execute(
                "CREATE INDEX idx_document_briefs_user_id ON document_briefs(user_id, updated_at DESC)"
            )
            await cursor.execute(
                "CREATE INDEX idx_document_briefs_conversation ON document_briefs(conversation_id)"
            )
            await cursor.execute(
                "CREATE INDEX idx_document_briefs_document ON document_briefs(document_id)"
            )
            
            print("✓ document_briefs table created")
            print("✓ Indexes created")
        
        await db.commit()
    
    print("\n✅ Phase 3 database migration complete!")
    print("\nNew features:")
    print("- DocumentBrief system for managing document requirements")
    print("- Outline generation and approval workflow")
    print("- Link between briefs, conversations, and generated documents")


if __name__ == "__main__":
    asyncio.run(migrate_phase3())
