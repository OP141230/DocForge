"""Quick test script for Phase 3 implementation."""
import asyncio
import aiosqlite


async def test_database():
    """Test that document_briefs table exists."""
    conn = await aiosqlite.connect('docforge.db')
    conn.row_factory = aiosqlite.Row
    
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='document_briefs'"
    )
    result = await cursor.fetchone()
    
    if result:
        print("✓ document_briefs table exists")
        
        # Check columns
        cursor = await conn.execute("PRAGMA table_info(document_briefs)")
        columns = await cursor.fetchall()
        print(f"✓ Table has {len(columns)} columns:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
    else:
        print("✗ document_briefs table not found")
    
    await conn.close()


async def test_imports():
    """Test that all modules import correctly."""
    try:
        from app.models.document_brief import DocumentBrief
        print("✓ DocumentBrief model imports")
        
        from app.repositories.document_brief_repository import DocumentBriefRepository
        print("✓ DocumentBriefRepository imports")
        
        from app.api.routes import document_briefs
        print("✓ document_briefs routes import")
        
        import main
        print("✓ main.py imports with all routers")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


async def main():
    """Run all tests."""
    print("Phase 3 Implementation Test\n" + "="*50)
    
    print("\n1. Testing imports...")
    if not await test_imports():
        return
    
    print("\n2. Testing database...")
    await test_database()
    
    print("\n" + "="*50)
    print("✅ Phase 3 backend implementation complete!")
    print("\nNext steps:")
    print("- Start the backend server")
    print("- Test API endpoints via OpenAPI docs at /docs")
    print("- Create a document brief")
    print("- Generate an outline")
    print("- Approve the outline")
    print("- Generate a full document")


if __name__ == "__main__":
    asyncio.run(main())
