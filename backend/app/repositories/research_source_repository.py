"""Repository for research sources.

Sources are the bridge between Phase 4 (knowledge-base files) and Phase 5
(external pages). De-duplication happens here so the same URL cannot inflate a
reference list twice, and knowledge-base sources reuse ``knowledge_file_id`` /
``chunk_id`` instead of copying file content into a second document store.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import sqlite3

from app.core.database import Database
from app.models.research import (
    ResearchSource,
    RetrievalStatus,
    SourceType,
)

SOURCE_COLUMNS = (
    "id, session_id, user_id, research_question_id, source_type, retrieval_status, "
    "title, url, canonical_url, publisher, author, published_date, accessed_at, "
    "content_text, excerpt, word_count, http_status, error, source_type_label, "
    "evaluation_notes, relevance_score, knowledge_file_id, chunk_id, page_number, "
    "section_title, selected, created_at"
)

UPDATABLE_FIELDS = {
    "retrieval_status",
    "title",
    "url",
    "canonical_url",
    "publisher",
    "author",
    "published_date",
    "accessed_at",
    "content_text",
    "excerpt",
    "word_count",
    "http_status",
    "error",
    "source_type_label",
    "evaluation_notes",
    "relevance_score",
    "page_number",
    "section_title",
    "selected",
}


class ResearchSourceRepository:
    """Data access for ``research_sources``."""

    def __init__(self, db: Database):
        self.db = db

    async def create(self, source: ResearchSource) -> ResearchSource:
        """Insert a source. Returns the existing row when it is a duplicate."""
        async with self.db.connection.cursor() as cursor:
            try:
                await cursor.execute(
                    f"INSERT INTO research_sources ({SOURCE_COLUMNS}) VALUES "
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        source.id,
                        source.session_id,
                        source.user_id,
                        source.research_question_id,
                        source.source_type.value,
                        source.retrieval_status.value,
                        source.title,
                        source.url,
                        source.canonical_url,
                        source.publisher,
                        source.author,
                        source.published_date,
                        source.accessed_at.isoformat() if source.accessed_at else None,
                        source.content_text,
                        source.excerpt,
                        source.word_count,
                        source.http_status,
                        source.error,
                        source.source_type_label,
                        json.dumps(source.evaluation_notes),
                        source.relevance_score,
                        source.knowledge_file_id,
                        source.chunk_id,
                        source.page_number,
                        source.section_title,
                        1 if source.selected else 0,
                        source.created_at.isoformat(),
                    ),
                )
                await self.db.connection.commit()
            except sqlite3.IntegrityError:
                # UNIQUE(session_id, canonical_url) hit - reuse the stored row.
                existing = None
                if source.canonical_url:
                    existing = await self.find_by_canonical(
                        source.session_id, source.user_id, source.canonical_url
                    )
                if existing:
                    return existing
                raise
        return source

    async def get_by_id(self, source_id: str, user_id: str) -> Optional[ResearchSource]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {SOURCE_COLUMNS} FROM research_sources WHERE id = ? AND user_id = ?",
                (source_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_source(row) if row else None

    async def find_by_canonical(
        self, session_id: str, user_id: str, canonical_url: str
    ) -> Optional[ResearchSource]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {SOURCE_COLUMNS} FROM research_sources "
                "WHERE session_id = ? AND user_id = ? AND canonical_url = ? LIMIT 1",
                (session_id, user_id, canonical_url),
            )
            row = await cursor.fetchone()
        return self._row_to_source(row) if row else None

    async def find_knowledge_source(
        self, session_id: str, user_id: str, knowledge_file_id: str, chunk_id: str
    ) -> Optional[ResearchSource]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {SOURCE_COLUMNS} FROM research_sources "
                "WHERE session_id = ? AND user_id = ? AND knowledge_file_id = ? AND chunk_id = ? "
                "LIMIT 1",
                (session_id, user_id, knowledge_file_id, chunk_id),
            )
            row = await cursor.fetchone()
        return self._row_to_source(row) if row else None

    async def list_by_session(
        self,
        session_id: str,
        user_id: str,
        selected_only: bool = False,
        limit: int = 500,
    ) -> List[ResearchSource]:
        query = f"SELECT {SOURCE_COLUMNS} FROM research_sources WHERE session_id = ? AND user_id = ?"
        params: List[Any] = [session_id, user_id]
        if selected_only:
            query += " AND selected = 1"
        query += " ORDER BY created_at ASC, title ASC LIMIT ?"
        params.append(limit)

        async with self.db.connection.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
        return [self._row_to_source(row) for row in rows]

    async def count_by_status(self, session_id: str, user_id: str) -> Dict[str, int]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT retrieval_status, COUNT(*) AS count FROM research_sources "
                "WHERE session_id = ? AND user_id = ? GROUP BY retrieval_status",
                (session_id, user_id),
            )
            rows = await cursor.fetchall()
        counts = {status.value: 0 for status in RetrievalStatus}
        for row in rows:
            counts[row["retrieval_status"]] = row["count"]
        counts["total"] = sum(
            row["count"] for row in rows
        )
        return counts

    async def update(
        self, source_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[ResearchSource]:
        fields: List[str] = []
        values: List[Any] = []

        for key, value in updates.items():
            if key not in UPDATABLE_FIELDS:
                continue
            if key == "retrieval_status" and isinstance(value, RetrievalStatus):
                fields.append("retrieval_status = ?")
                values.append(value.value)
            elif key == "evaluation_notes":
                fields.append("evaluation_notes = ?")
                values.append(json.dumps(value or []))
            elif key == "accessed_at" and isinstance(value, datetime):
                fields.append("accessed_at = ?")
                values.append(value.isoformat())
            elif key == "selected":
                fields.append("selected = ?")
                values.append(1 if value else 0)
            else:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            return await self.get_by_id(source_id, user_id)

        values.extend([source_id, user_id])
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"UPDATE research_sources SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
                values,
            )
            await self.db.connection.commit()
            if cursor.rowcount == 0:
                return None
        return await self.get_by_id(source_id, user_id)

    async def delete(self, source_id: str, user_id: str) -> bool:
        """Delete a source and the evidence derived from it (one transaction)."""
        conn = self.db.connection
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "DELETE FROM claim_verification_evidence WHERE evidence_id IN "
                    "(SELECT id FROM research_evidence WHERE source_id = ? AND user_id = ?)",
                    (source_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM research_evidence WHERE source_id = ? AND user_id = ?",
                    (source_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM citations WHERE source_id = ? AND user_id = ?",
                    (source_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM research_sources WHERE id = ? AND user_id = ?",
                    (source_id, user_id),
                )
                deleted = cursor.rowcount > 0
                await conn.commit()
                return deleted
            except Exception:
                await conn.rollback()
                raise

    def _row_to_source(self, row) -> ResearchSource:
        return ResearchSource(
            id=row["id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            research_question_id=row["research_question_id"],
            source_type=SourceType(row["source_type"]),
            retrieval_status=RetrievalStatus(row["retrieval_status"]),
            title=row["title"],
            url=row["url"],
            canonical_url=row["canonical_url"],
            publisher=row["publisher"],
            author=row["author"],
            published_date=row["published_date"],
            accessed_at=datetime.fromisoformat(row["accessed_at"]) if row["accessed_at"] else None,
            content_text=row["content_text"],
            excerpt=row["excerpt"],
            word_count=row["word_count"] or 0,
            http_status=row["http_status"],
            error=row["error"],
            source_type_label=row["source_type_label"] or "unknown",
            evaluation_notes=json.loads(row["evaluation_notes"] or "[]"),
            relevance_score=row["relevance_score"],
            knowledge_file_id=row["knowledge_file_id"],
            chunk_id=row["chunk_id"],
            page_number=row["page_number"],
            section_title=row["section_title"],
            selected=bool(row["selected"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
