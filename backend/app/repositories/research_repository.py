"""Repository for research sessions and research questions.

Every method takes ``user_id`` and puts it in the ``WHERE`` clause. That is the
single most important security property of Phase 5: research sessions contain
extracted third-party content and evidence, so a missing user scope would leak
one user's research into another's workspace. The API layer passes the id from
the session cookie (:func:`app.core.auth.get_current_user`), never from a body.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.core.database import Database
from app.models.research import (
    CitationStyle,
    ResearchQuestion,
    ResearchSession,
    ResearchStatus,
)

SESSION_COLUMNS = (
    "id, user_id, brief_id, document_id, title, status, external_research, "
    "include_knowledge_base, citation_style, requested_urls, knowledge_file_ids, "
    "provider, provider_message, error, progress_message, created_at, updated_at, "
    "started_at, completed_at"
)

UPDATABLE_SESSION_FIELDS = {
    "title",
    "status",
    "external_research",
    "include_knowledge_base",
    "citation_style",
    "requested_urls",
    "knowledge_file_ids",
    "provider",
    "provider_message",
    "error",
    "progress_message",
    "document_id",
    "brief_id",
    "started_at",
    "completed_at",
}

JSON_FIELDS = {"requested_urls", "knowledge_file_ids"}
BOOL_FIELDS = {"external_research", "include_knowledge_base"}
DATETIME_FIELDS = {"started_at", "completed_at"}


class ResearchRepository:
    """Data access for ``research_sessions`` and ``research_questions``."""

    def __init__(self, db: Database):
        self.db = db

    # -- sessions ---------------------------------------------------------
    async def create_session(self, session: ResearchSession) -> ResearchSession:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"INSERT INTO research_sessions ({SESSION_COLUMNS}) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session.id,
                    session.user_id,
                    session.brief_id,
                    session.document_id,
                    session.title,
                    session.status.value,
                    1 if session.external_research else 0,
                    1 if session.include_knowledge_base else 0,
                    session.citation_style.value,
                    json.dumps(session.requested_urls),
                    json.dumps(session.knowledge_file_ids),
                    session.provider,
                    session.provider_message,
                    session.error,
                    session.progress_message,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    session.started_at.isoformat() if session.started_at else None,
                    session.completed_at.isoformat() if session.completed_at else None,
                ),
            )
            await self.db.connection.commit()
        return session

    async def get_session(self, session_id: str, user_id: str) -> Optional[ResearchSession]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {SESSION_COLUMNS} FROM research_sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_session(row) if row else None

    async def get_latest_for_document(
        self, document_id: str, user_id: str
    ) -> Optional[ResearchSession]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {SESSION_COLUMNS} FROM research_sessions "
                "WHERE document_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT 1",
                (document_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_session(row) if row else None

    async def get_latest_for_brief(
        self, brief_id: str, user_id: str
    ) -> Optional[ResearchSession]:
        """Most recent session for a brief (used when generating from a brief)."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {SESSION_COLUMNS} FROM research_sessions "
                "WHERE brief_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT 1",
                (brief_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_session(row) if row else None

    async def list_sessions(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[ResearchSession], int]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM research_sessions WHERE user_id = ?", (user_id,)
            )
            total = (await cursor.fetchone())[0]
            await cursor.execute(
                f"SELECT {SESSION_COLUMNS} FROM research_sessions "
                "WHERE user_id = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset),
            )
            rows = await cursor.fetchall()
        return [self._row_to_session(row) for row in rows], total

    async def update_session(
        self, session_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[ResearchSession]:
        fields: List[str] = []
        values: List[Any] = []

        for key, value in updates.items():
            if key not in UPDATABLE_SESSION_FIELDS:
                continue
            if key in JSON_FIELDS:
                fields.append(f"{key} = ?")
                values.append(json.dumps(value or []))
            elif key in BOOL_FIELDS:
                fields.append(f"{key} = ?")
                values.append(1 if value else 0)
            elif key in DATETIME_FIELDS:
                fields.append(f"{key} = ?")
                values.append(value.isoformat() if isinstance(value, datetime) else value)
            elif key == "status" and isinstance(value, ResearchStatus):
                fields.append("status = ?")
                values.append(value.value)
            elif key == "citation_style" and isinstance(value, CitationStyle):
                fields.append("citation_style = ?")
                values.append(value.value)
            else:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            return await self.get_session(session_id, user_id)

        fields.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.extend([session_id, user_id])

        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"UPDATE research_sessions SET {', '.join(fields)} "
                "WHERE id = ? AND user_id = ?",
                values,
            )
            await self.db.connection.commit()
            if cursor.rowcount == 0:
                return None
        return await self.get_session(session_id, user_id)

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a session and everything that hangs off it.

        Child rows are deleted explicitly: DocForge does not enable
        ``PRAGMA foreign_keys``, so SQLite will not cascade for us. Deletion is
        transactional so a partial delete cannot leave orphaned evidence.
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            return False

        conn = self.db.connection
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "DELETE FROM claim_verification_evidence WHERE verification_id IN "
                    "(SELECT id FROM claim_verifications WHERE research_session_id = ? AND user_id = ?)",
                    (session_id, user_id),
                )
                await cursor.execute(
                    "UPDATE claim_verifications SET research_session_id = NULL "
                    "WHERE research_session_id = ? AND user_id = ?",
                    (session_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM citations WHERE research_session_id = ? AND user_id = ?",
                    (session_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM research_evidence WHERE session_id = ? AND user_id = ?",
                    (session_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM research_sources WHERE session_id = ? AND user_id = ?",
                    (session_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM research_questions WHERE session_id = ? AND user_id = ?",
                    (session_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM research_sessions WHERE id = ? AND user_id = ?",
                    (session_id, user_id),
                )
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
        return True

    # -- questions --------------------------------------------------------
    async def replace_questions(
        self, session_id: str, user_id: str, questions: List[Dict[str, Any]]
    ) -> List[ResearchQuestion]:
        conn = self.db.connection
        created: List[ResearchQuestion] = []
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "DELETE FROM research_questions WHERE session_id = ? AND user_id = ?",
                    (session_id, user_id),
                )
                for index, item in enumerate(questions):
                    question = ResearchQuestion(
                        id=str(uuid4()),
                        session_id=session_id,
                        question=str(item["question"]).strip(),
                        rationale=(item.get("rationale") or None),
                        order_index=index,
                        created_at=datetime.utcnow(),
                    )
                    await cursor.execute(
                        "INSERT INTO research_questions "
                        "(id, session_id, user_id, question, rationale, order_index, created_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            question.id,
                            session_id,
                            user_id,
                            question.question,
                            question.rationale,
                            question.order_index,
                            question.created_at.isoformat(),
                        ),
                    )
                    created.append(question)
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
        return created

    async def list_questions(self, session_id: str, user_id: str) -> List[ResearchQuestion]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT id, session_id, question, rationale, order_index, created_at "
                "FROM research_questions WHERE session_id = ? AND user_id = ? "
                "ORDER BY order_index",
                (session_id, user_id),
            )
            rows = await cursor.fetchall()
        return [
            ResearchQuestion(
                id=row["id"],
                session_id=row["session_id"],
                question=row["question"],
                rationale=row["rationale"],
                order_index=row["order_index"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    # -- helpers ----------------------------------------------------------
    def _row_to_session(self, row) -> ResearchSession:
        return ResearchSession(
            id=row["id"],
            user_id=row["user_id"],
            brief_id=row["brief_id"],
            document_id=row["document_id"],
            title=row["title"],
            status=ResearchStatus(row["status"]),
            external_research=bool(row["external_research"]),
            include_knowledge_base=bool(row["include_knowledge_base"]),
            citation_style=CitationStyle(row["citation_style"]),
            requested_urls=json.loads(row["requested_urls"] or "[]"),
            knowledge_file_ids=json.loads(row["knowledge_file_ids"] or "[]"),
            provider=row["provider"],
            provider_message=row["provider_message"],
            error=row["error"],
            progress_message=row["progress_message"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )
