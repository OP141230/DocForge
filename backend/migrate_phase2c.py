"""Phase 2C Migration - Add user_id and conversation_id to documents table."""
import sys
import asyncio
import aiosqlite
from pathlib import Path


async def migrate_phase2c():
    """Add user_id and conversation_id columns to documents table."""
    db_path = Path(__file__).parent / "app" / "data" / "docforge.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("ℹ️  No migration needed - database will be created with correct schema")
        return
    
    print(f"🔄 Migrating database at {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # Check if columns already exist
        async with db.execute("PRAGMA table_info(documents)") as cursor:
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            has_user_id = "user_id" in column_names
            has_conversation_id = "conversation_id" in column_names
            
            if has_user_id and has_conversation_id:
                print("✅ Columns already exist - no migration needed")
                return
        
        print("📝 Adding user_id and conversation_id columns...")
        
        try:
            # Add user_id column if missing
            if not has_user_id:
                await db.execute("ALTER TABLE documents ADD COLUMN user_id TEXT")
                print("   ✓ Added user_id column")
            
            # Add conversation_id column if missing
            if not has_conversation_id:
                await db.execute("ALTER TABLE documents ADD COLUMN conversation_id TEXT")
                print("   ✓ Added conversation_id column")
            
            await db.commit()
            
            # Create index on user_id if it doesn't exist
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_user_id 
                ON documents(user_id, updated_at DESC)
            """)
            await db.commit()
            print("   ✓ Created index on user_id")
            
            print("✅ Migration completed successfully!")
            print("")
            print("⚠️  IMPORTANT:")
            print("   - Existing documents will have NULL user_id")
            print("   - You may want to delete test documents or assign them to a user")
            print("   - New documents will require authentication and will be assigned to users")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            await db.rollback()
            sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("DocForge Phase 2C Migration")
    print("Adding user_id and conversation_id to documents table")
    print("=" * 60)
    print()
    
    asyncio.run(migrate_phase2c())
