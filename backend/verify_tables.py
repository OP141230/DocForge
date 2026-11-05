"""Verify Phase 4 database tables."""
import asyncio
import aiosqlite


async def verify_tables():
    """Check that all Phase 4 tables exist."""
    async with aiosqlite.connect('docforge.db') as db:
        cursor = await db.cursor()
        
        # Get all tables
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = await cursor.fetchall()
        
        print("Database tables:")
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        # Check for Phase 4 tables specifically
        required_tables = [
            'knowledge_files',
            'extracted_content',
            'content_chunks',
            'content_chunks_fts',
            'brief_file_attachments'
        ]
        
        table_names = [t[0] for t in tables]
        print("\nPhase 4 table verification:")
        all_present = True
        for table in required_tables:
            if table in table_names:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (MISSING)")
                all_present = False
        
        if all_present:
            print("\n✅ All Phase 4 tables present")
        else:
            print("\n❌ Some Phase 4 tables missing")
        
        return all_present


if __name__ == "__main__":
    asyncio.run(verify_tables())
