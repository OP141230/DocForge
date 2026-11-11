"""
Comprehensive security audit tests for Phase 8.
Tests authorization, authentication, data isolation, and input validation.
"""
import pytest
import uuid
from app.core.database import get_database
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_multi_user_document_isolation(api_client_factory, use_test_database):
    """Test that users cannot access each other's documents."""
    # Create two test users
    db = await get_database()
    user_repo = UserRepository(db)
    
    unique_suffix = str(uuid.uuid4())[:8]
    user1 = await user_repo.create("User One", f"user1_{unique_suffix}@test.com", hash_password("Password123"))
    user2 = await user_repo.create("User Two", f"user2_{unique_suffix}@test.com", hash_password("Password456"))
    
    # Create clients authenticated as each user
    client1 = api_client_factory(user1)
    client2 = api_client_factory(user2)
    
    # User1 creates a document
    doc_repo = DocumentRepository(db)
    from app.models.document_ir import DocumentIR, DocumentMetadata, Section
    
    doc1 = DocumentIR(
        title="User 1's Document",
        metadata=DocumentMetadata(document_type="general_report"),
        content=[Section(title="Section", level=2, blocks=[])]
    )
    created_doc = await doc_repo.create(doc1, user_id=user1.id)
    doc1_id = created_doc.id
    
    # User2 tries to access User1's document - should get 404
    response = await client2.get(f"/api/documents/{doc1_id}")
    assert response.status_code == 404, "User should not be able to access another user's document"
    
    # User2 tries to update User1's document - should get 404
    response = await client2.put(
        f"/api/documents/{doc1_id}",
        json=doc1.model_dump(mode='json')
    )
    assert response.status_code == 404, "User should not be able to update another user's document"
    
    # User2 tries to delete User1's document - should get 404
    response = await client2.delete(f"/api/documents/{doc1_id}")
    assert response.status_code == 404, "User should not be able to delete another user's document"
    
    # User1 CAN access their own document
    response = await client1.get(f"/api/documents/{doc1_id}")
    assert response.status_code == 200, "User should be able to access their own document"


@pytest.mark.asyncio
async def test_conversation_isolation(api_client_factory, use_test_database):
    """Test that users cannot access each other's conversations."""
    db = await get_database()
    user_repo = UserRepository(db)
    
    unique_suffix = str(uuid.uuid4())[:8]
    user1 = await user_repo.create("User One", f"conv1_{unique_suffix}@test.com", hash_password("Password123"))
    user2 = await user_repo.create("User Two", f"conv2_{unique_suffix}@test.com", hash_password("Password456"))
    
    client1 = api_client_factory(user1)
    client2 = api_client_factory(user2)
    
    # User1 creates a conversation
    response = await client1.post(
        "/api/conversations",
        json={"title": "User 1's Conversation"}
    )
    assert response.status_code == 201
    conv_id = response.json()["id"]
    
    # User2 tries to access it - should fail
    response = await client2.get(f"/api/conversations/{conv_id}")
    assert response.status_code == 404, "User cannot access another user's conversation"
    
    # User1 CAN access their own conversation
    response = await client1.get(f"/api/conversations/{conv_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_knowledge_file_isolation(api_client_factory, use_test_database):
    """Test that users cannot access each other's uploaded files."""
    import io
    
    db = await get_database()
    user_repo = UserRepository(db)
    
    unique_suffix = str(uuid.uuid4())[:8]
    user1 = await user_repo.create("User One", f"file1_{unique_suffix}@test.com", hash_password("Password123"))
    user2 = await user_repo.create("User Two", f"file2_{unique_suffix}@test.com", hash_password("Password456"))
    
    client1 = api_client_factory(user1)
    client2 = api_client_factory(user2)
    
    # User1 uploads a file
    files = {"file": ("test.txt", io.BytesIO(b"Secret content from User 1"), "text/plain")}
    response = await client1.post("/api/knowledge/files", files=files)
    assert response.status_code == 200
    file_id = response.json()["file_id"]
    
    # User2 tries to access User1's file - should fail
    response = await client2.get(f"/api/knowledge/files/{file_id}")
    assert response.status_code == 404, "User cannot access another user's file"
    
    # User1 CAN access their own file
    response = await client1.get(f"/api/knowledge/files/{file_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_access_blocked(use_test_database):
    """Test that unauthenticated requests are blocked."""
    from main import app
    from httpx import ASGITransport, AsyncClient
    
    # Create client WITHOUT authentication override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Try to access protected endpoints without authentication
        endpoints = [
            ("/api/documents", "get"),
            ("/api/conversations", "get"),
            ("/api/auth/me", "get"),
            ("/api/knowledge/files", "get"),
            ("/api/templates/", "get"),
            ("/api/research/sessions", "get"),
        ]
        
        for endpoint, method in endpoints:
            if method == "get":
                response = await client.get(endpoint)
            else:
                response = await client.post(endpoint, json={})
            
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"


@pytest.mark.asyncio
async def test_weak_password_rejected(api_client):
    """Test that weak passwords are rejected."""
    weak_passwords = [
        "short",           # Too short
        "12345678",        # Only numbers
        "abcdefgh",        # Only letters
        "a1",              # Too short even with both
    ]
    
    for weak_pwd in weak_passwords:
        unique_suffix = str(uuid.uuid4())[:8]
        response = await api_client.post("/api/auth/register", json={
            "full_name": "Test User",
            "email": f"test_{weak_pwd}_{unique_suffix}@test.com",
            "password": weak_pwd,
            "confirm_password": weak_pwd
        })
        # FastAPI validation returns 422 for pydantic errors
        assert response.status_code in [400, 422], f"Weak password '{weak_pwd}' should be rejected"


@pytest.mark.asyncio
async def test_session_isolation(api_client_factory, use_test_database):
    """Test that sessions are properly isolated."""
    db = await get_database()
    user_repo = UserRepository(db)
    
    unique_suffix = str(uuid.uuid4())[:8]
    user1 = await user_repo.create("Session User 1", f"session1_{unique_suffix}@test.com", hash_password("Password123"))
    user2 = await user_repo.create("Session User 2", f"session2_{unique_suffix}@test.com", hash_password("Password456"))
    
    client1 = api_client_factory(user1)
    client2 = api_client_factory(user2)
    
    # Check that each client returns the correct user
    r1 = await client1.get("/api/auth/me")
    assert r1.status_code == 200
    assert r1.json()["email"] == f"session1_{unique_suffix}@test.com"
    
    r2 = await client2.get("/api/auth/me")
    assert r2.status_code == 200
    assert r2.json()["email"] == f"session2_{unique_suffix}@test.com"


@pytest.mark.asyncio
async def test_email_enumeration_prevention(api_client):
    """Test that email enumeration is prevented."""
    unique_suffix = str(uuid.uuid4())[:8]
    
    # Register a user
    await api_client.post("/api/auth/register", json={
        "full_name": "Existing User",
        "email": f"exists_{unique_suffix}@test.com",
        "password": "Password123",
        "confirm_password": "Password123"
    })
    
    # Try to login with correct email but wrong password
    response1 = await api_client.post("/api/auth/login", json={
        "email": f"exists_{unique_suffix}@test.com",
        "password": "WrongPassword123"
    })
    
    # Try to login with non-existent email
    response2 = await api_client.post("/api/auth/login", json={
        "email": f"notexist_{unique_suffix}@test.com",
        "password": "Password123"
    })
    
    # Both should return the same generic error
    assert response1.status_code == 401
    assert response2.status_code == 401
    assert response1.json()["detail"] == response2.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_sql_injection_protection(api_client):
    """Test that SQL injection attempts are neutralized."""
    # Try SQL injection in search query
    malicious_queries = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1' UNION SELECT * FROM users--",
        "admin'--",
    ]
    
    for query in malicious_queries:
        response = await api_client.get(f"/api/knowledge/search?q={query}")
        # Should not crash - 200 (empty results) or 400 (validation) are acceptable
        assert response.status_code in [200, 400, 404], f"Query '{query}' should not cause server error"


@pytest.mark.asyncio
async def test_xss_in_document_title(api_client):
    """Test that XSS attempts in document titles are handled."""
    from app.models.document_ir import DocumentIR, DocumentMetadata, Section
    
    xss_title = "<script>alert('XSS')</script>"
    doc = DocumentIR(
        title=xss_title,
        metadata=DocumentMetadata(document_type="general_report"),
        content=[Section(title="Test", level=2, blocks=[])]
    )
    
    response = await api_client.post(
        "/api/documents",
        json=doc.model_dump(mode='json')
    )
    
    # Document should be created (backend doesn't sanitize, frontend should)
    assert response.status_code == 201
    doc_data = response.json()
    
    # Title should be stored as-is (responsibility of frontend to escape)
    assert doc_data["title"] == xss_title


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--timeout=60"])
