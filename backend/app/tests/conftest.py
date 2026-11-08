"""Pytest configuration and fixtures (Phases 1-5).

Every fixture uses an in-memory SQLite database and no network access, so the
suite is fast, deterministic and safe to run offline.

Note: the previous version built ``AsyncClient(app=app)``, which httpx removed.
Tests now use ``httpx.ASGITransport`` explicitly.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_user
from app.core.database import Database, get_database
from app.models.auth import User
from app.models.document_ir import (
    DocumentIR,
    DocumentMetadata,
    InlineContent,
    Paragraph,
    Section,
)
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository


@pytest.fixture
async def test_db():
    """Fresh in-memory database with the full schema."""
    db = Database(":memory:")
    await db.connect()
    yield db
    await db.disconnect()


@pytest.fixture
async def db(test_db):
    """Alias used by Phase 5 tests."""
    return test_db


@pytest.fixture
async def user(test_db):
    return await UserRepository(test_db).create("Test User", "test@example.com", "hash")


@pytest.fixture
async def other_user(test_db):
    return await UserRepository(test_db).create("Other User", "other@example.com", "hash")


@pytest.fixture
async def document_repo(test_db):
    return DocumentRepository(test_db)


@pytest.fixture
async def conversation_repo(test_db):
    return ConversationRepository(test_db)


@pytest.fixture
async def message_repo(test_db):
    return MessageRepository(test_db)


@pytest.fixture
def document_factory():
    """Build a DocumentIR with one section per provided paragraph."""

    def _make(title: str = "Test document", paragraphs=None, section_title: str = "Findings"):
        paragraphs = paragraphs or [
            "The system processed 42 percent of records in the first quarter of 2023."
        ]
        return DocumentIR(
            title=title,
            content=[
                Section(
                    level=1,
                    title=section_title,
                    blocks=[
                        Paragraph(content=[InlineContent(text=text)]) for text in paragraphs
                    ],
                )
            ],
            metadata=DocumentMetadata(document_type="general_report"),
        )

    return _make


@pytest.fixture
def use_test_database(test_db, monkeypatch):
    """Point the global database accessor at the in-memory test database.

    The route modules call ``await get_database()`` directly rather than
    declaring ``Depends(get_database)``, so FastAPI's ``dependency_overrides``
    does not intercept them. Without this patch the routes would read and write
    the real ``./docforge.db`` file, which makes tests slow and lets one test's
    data leak into the next.

    ``monkeypatch`` restores the original value after every test, so no state
    escapes the fixture.
    """
    import app.core.database as database_module

    monkeypatch.setattr(database_module, "_db", test_db, raising=False)
    return test_db


@pytest.fixture
async def api_client(use_test_database, test_db, user):
    """ASGI client with authentication and database dependencies overridden."""
    from main import app

    async def _get_db():
        return test_db

    async def _get_user():
        return user

    app.dependency_overrides[get_database] = _get_db
    app.dependency_overrides[get_current_user] = _get_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def api_client_factory(use_test_database, test_db):
    """Build a client authenticated as a specific user (for isolation tests)."""
    from main import app

    clients = []

    def _factory(current_user: User):
        async def _get_db():
            return test_db

        async def _get_user():
            return current_user

        app.dependency_overrides[get_database] = _get_db
        app.dependency_overrides[get_current_user] = _get_user
        transport = ASGITransport(app=app)
        client = AsyncClient(transport=transport, base_url="http://test")
        clients.append(client)
        return client

    yield _factory

    for client in clients:
        await client.aclose()
    app.dependency_overrides.clear()
