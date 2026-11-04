"""Pytest configuration and fixtures."""
import pytest
import asyncio
from httpx import AsyncClient

from app.core.database import Database
from app.repositories.document_repository import DocumentRepository


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create a test database."""
    db = Database(":memory:")
    await db.connect()
    yield db
    await db.disconnect()


@pytest.fixture
async def document_repo(test_db):
    """Create a document repository with test database."""
    return DocumentRepository(test_db)


@pytest.fixture
async def async_client():
    """Create an async HTTP client for API testing."""
    from main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
