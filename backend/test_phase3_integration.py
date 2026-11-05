"""Comprehensive Phase 3 integration test."""
import asyncio
import aiosqlite
from datetime import datetime


# Test data for all 10 document types
DOCUMENT_TYPES_TEST_DATA = {
    "technical_guide": {
        "title": "API Integration Guide",
        "target_audience": "Backend developers",
        "estimated_length": "medium",
        "tone": "technical",
        "technical_level": "advanced",
        "include_code_examples": True,
        "platform_or_technology": "FastAPI Python"
    },
    "user_manual": {
        "title": "Product User Manual",
        "target_audience": "End users",
        "estimated_length": "long",
        "tone": "friendly",
        "product_name": "DocForge",
        "version": "1.0.0",
        "include_screenshots": True,
        "include_troubleshooting": True
    },
    "api_documentation": {
        "title": "REST API Documentation",
        "target_audience": "API consumers",
        "estimated_length": "long",
        "tone": "technical",
        "api_type": "REST",
        "include_authentication": True,
        "include_examples": True,
        "base_url": "https://api.docforge.com"
    },
    "proposal": {
        "title": "Project Proposal",
        "target_audience": "Stakeholders",
        "estimated_length": "medium",
        "tone": "persuasive",
        "proposal_type": "project",
        "include_timeline": True,
        "include_budget": True,
        "budget_range": "$50,000 - $100,000"
    },
    "report": {
        "title": "Quarterly Business Report",
        "target_audience": "Management",
        "estimated_length": "medium",
        "tone": "formal",
        "report_type": "business",
        "time_period": "Q1 2024",
        "include_charts": True,
        "include_executive_summary": True
    },
    "tutorial": {
        "title": "React Hooks Tutorial",
        "target_audience": "Junior developers",
        "estimated_length": "medium",
        "tone": "educational",
        "difficulty_level": "beginner",
        "include_exercises": True,
        "prerequisites": "Basic JavaScript knowledge"
    },
    "whitepaper": {
        "title": "Blockchain Whitepaper",
        "target_audience": "Technical experts",
        "estimated_length": "long",
        "tone": "academic",
        "include_research": True,
        "include_citations": True,
        "problem_statement": "Scalability in distributed systems"
    },
    "case_study": {
        "title": "Migration Case Study",
        "target_audience": "Enterprise clients",
        "estimated_length": "medium",
        "tone": "professional",
        "company_or_subject": "TechCorp Inc.",
        "challenge_faced": "Legacy system modernization",
        "solution_provided": "Cloud migration",
        "include_metrics": True
    },
    "policy_document": {
        "title": "Privacy Policy",
        "target_audience": "General public",
        "estimated_length": "long",
        "tone": "legal",
        "policy_type": "privacy",
        "jurisdiction": "United States",
        "effective_date": "2024-01-01",
        "include_definitions": True
    },
    "standard_document": {
        "title": "Standard Document",
        "target_audience": "General",
        "estimated_length": "medium",
        "tone": "professional"
    }
}


async def test_database_schema():
    """Test document_briefs table structure."""
    print("\n1. Testing Database Schema")
    print("-" * 50)
    
    conn = await aiosqlite.connect('docforge.db')
    conn.row_factory = aiosqlite.Row
    
    # Check table exists
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='document_briefs'"
    )
    result = await cursor.fetchone()
    
    if not result:
        print("✗ document_briefs table not found")
        await conn.close()
        return False
    
    print("✓ document_briefs table exists")
    
    # Check columns
    cursor = await conn.execute("PRAGMA table_info(document_briefs)")
    columns = await cursor.fetchall()
    column_names = [col['name'] for col in columns]
    
    required_columns = [
        'id', 'user_id', 'conversation_id', 'document_type',
        'title', 'topic', 'purpose', 'audience', 'language',
        'desired_length', 'tone', 'writing_style', 'document_specific_data',
        'required_sections', 'important_points', 'topics_to_avoid',
        'additional_instructions', 'citation_style', 'outline',
        'outline_approved', 'outline_approved_at', 'document_id',
        'created_at', 'updated_at'
    ]
    
    missing_columns = [col for col in required_columns if col not in column_names]
    
    if missing_columns:
        print(f"✗ Missing columns: {missing_columns}")
        await conn.close()
        return False
    
    print(f"✓ All {len(required_columns)} required columns present")
    
    # Check indexes
    cursor = await conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='document_briefs'"
    )
    indexes = await cursor.fetchall()
    print(f"✓ Found {len(indexes)} indexes")
    
    await conn.close()
    return True


async def test_imports():
    """Test all module imports."""
    print("\n2. Testing Module Imports")
    print("-" * 50)
    
    try:
        from app.models.document_brief import (
            DocumentBrief, CreateBriefRequest, UpdateBriefRequest,
            UpdateOutlineRequest, OutlineItem
        )
        print("✓ DocumentBrief models import")
        
        from app.repositories.document_brief_repository import DocumentBriefRepository
        print("✓ DocumentBriefRepository imports")
        
        from app.api.routes import document_briefs
        print("✓ document_briefs routes import")
        
        import main
        app = main.app
        print(f"✓ FastAPI app loaded with {len(app.routes)} routes")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_repository_operations():
    """Test DocumentBriefRepository CRUD operations."""
    print("\n3. Testing Repository Operations")
    print("-" * 50)
    
    try:
        from app.core.database import get_database
        from app.repositories.document_brief_repository import DocumentBriefRepository
        
        # Initialize database
        db = await get_database()
        repo = DocumentBriefRepository(db)
        
        # Create a test brief
        brief_data = {
            "document_type": "technical_guide",
            "title": "Test Integration Guide",
            "topic": "API Integration",
            "audience": "Developers",
            "desired_length": "medium",
            "tone": "technical",
            "document_specific_data": {
                "technical_level": "intermediate",
                "include_code_examples": True
            }
        }
        
        brief = await repo.create(brief_data, user_id="test_user_123")
        print(f"✓ Created brief: {brief.id}")
        
        # Read brief
        retrieved = await repo.get_by_id(brief.id, user_id="test_user_123")
        if retrieved:
            print(f"✓ Retrieved brief: {retrieved.title}")
        else:
            print("✗ Failed to retrieve brief")
            return False
        
        # Update brief
        updates = {"title": "Updated Test Guide"}
        updated = await repo.update(brief.id, "test_user_123", updates)
        if updated and updated.title == "Updated Test Guide":
            print(f"✓ Updated brief title")
        else:
            print("✗ Failed to update brief")
            return False
        
        # List briefs
        briefs, total = await repo.list_by_user("test_user_123", limit=10, offset=0)
        print(f"✓ Listed {total} briefs for user")
        
        # Test user isolation
        other_user_brief = await repo.get_by_id(brief.id, user_id="other_user_456")
        if other_user_brief is None:
            print("✓ User isolation working (cannot access other user's brief)")
        else:
            print("✗ User isolation failed")
            return False
        
        # Cleanup
        await repo.delete(brief.id, user_id="test_outline_user")
        
        return True
        
    except Exception as e:
        print(f"✗ Repository test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_all_document_types():
    """Test creating briefs for all 10 document types."""
    print("\n4. Testing All Document Types")
    print("-" * 50)
    
    try:
        from app.core.database import get_database
        from app.repositories.document_brief_repository import DocumentBriefRepository
        
        db = await get_database()
        repo = DocumentBriefRepository(db)
        
        created_briefs = []
        
        for doc_type, fields in DOCUMENT_TYPES_TEST_DATA.items():
            try:
                brief_data = {
                    "document_type": doc_type,
                    "title": fields.get("title", f"Test {doc_type}"),
                    "topic": fields.get("title", f"Test {doc_type}"),
                    "audience": fields.get("target_audience", "General"),
                    "desired_length": fields.get("estimated_length", "medium"),
                    "tone": fields.get("tone", "professional"),
                    "document_specific_data": {
                        k: v for k, v in fields.items() 
                        if k not in ["title", "target_audience", "estimated_length", "tone"]
                    }
                }
                
                brief = await repo.create(brief_data, user_id=f"test_type_user")
                created_briefs.append(brief.id)
                print(f"✓ Created {doc_type}: {brief.title}")
                
            except Exception as e:
                print(f"✗ Failed to create {doc_type}: {e}")
                return False
        
        print(f"\n✓ Successfully created all 10 document types")
        
        # Cleanup
        for brief_id in created_briefs:
            await repo.delete(brief_id, user_id="test_type_user")
        
        return True
        
    except Exception as e:
        print(f"✗ Document types test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_outline_workflow():
    """Test outline generation and approval workflow."""
    print("\n5. Testing Outline Workflow")
    print("-" * 50)
    
    try:
        from app.core.database import get_database
        from app.repositories.document_brief_repository import DocumentBriefRepository
        
        db = await get_database()
        repo = DocumentBriefRepository(db)
        
        # Create brief
        brief_data = {
            "document_type": "tutorial",
            "title": "Python Basics Tutorial",
            "topic": "Python Programming Basics",
            "audience": "Beginners",
            "desired_length": "medium",
            "tone": "educational",
            "document_specific_data": {
                "difficulty_level": "beginner",
                "include_exercises": True
            }
        }
        
        brief = await repo.create(brief_data, user_id="test_outline_user")
        print(f"✓ Created brief for outline test")
        
        # Update with outline
        outline_data = {
            "outline": [
                {"level": 1, "title": "Introduction"},
                {"level": 2, "title": "What is Python?"},
                {"level": 1, "title": "Basic Syntax"},
                {"level": 2, "title": "Variables and Data Types"},
            ]
        }
        
        updated = await repo.update(brief.id, "test_outline_user", outline_data)
        if updated and updated.outline:
            print(f"✓ Updated brief with outline ({len(updated.outline)} sections)")
        else:
            print("✗ Failed to update outline")
            return False
        
        # Approve outline
        approval_data = {
            "outline_approved": True,
            "outline_approved_at": datetime.utcnow().isoformat()
        }
        
        approved = await repo.update(brief.id, "test_outline_user", approval_data)
        if approved and approved.outline_approved:
            print(f"✓ Approved outline at {approved.outline_approved_at}")
        else:
            print("✗ Failed to approve outline")
            return False
        
        # Link to generated document
        link_data = {
            "document_id": "doc_123456"
        }
        
        linked = await repo.update(brief.id, "test_outline_user", link_data)
        if linked and linked.document_id:
            print(f"✓ Linked to generated document: {linked.document_id}")
        else:
            print("✗ Failed to link document")
            return False
        
        # Cleanup
        deleted = await repo.delete(brief.id, user_id="test_outline_user")
        if deleted:
            print(f"✓ Cleaned up test brief")
        
        return True
        
    except Exception as e:
        print(f"✗ Outline workflow test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests."""
    print("=" * 50)
    print("Phase 3 Comprehensive Integration Test")
    print("=" * 50)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Module Imports", test_imports),
        ("Repository Operations", test_repository_operations),
        ("All Document Types", test_all_document_types),
        ("Outline Workflow", test_outline_workflow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 50)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All integration tests passed!")
        print("\nPhase 3 is ready for production!")
    else:
        print("❌ Some tests failed. Please review errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
