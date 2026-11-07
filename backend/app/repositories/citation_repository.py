"""Repository for document citations.

A citation row is the join between a document, a real source record and the
place the claim appears. Deleting a citation never deletes its source (the spec
requires "remove a citation without accidentally deleting its source").
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import Database
from app.models.research import CitationRecord, CitationStyle

CITATION_COLUMNS = (
    "id, user_id, document_id, source_id, research_session_id, evidence_id, "
    "section_id, section_title, marker, locator, style, in_text, created_at"
)


class CitationRepository:
    """Data access for ``citations``."""

    def __init__(self, db: Database):
        self.db = db

    async def create(self, citation: CitationRecord) -> CitationRecord:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"INSERT INTO citations ({CITATION_COLUMNS}) VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    citation.id,
                    citation.user_id,
                    citation.document_id,
                    citation.source_id,
                    citation.research_session_id,
                    citation.evidence_id,
                    citation.section_id,
                    citation.section_title,
                    citation.marker,
                    citation.locator,
                    citation.style.value,
                    citation.in_text,
                    citation.created_at.isoformat(),
                ),
            )
            await self.db.connection.commit()
        return citation

    async def list_for_document(self, document_id: str, user_id: str) -> List[CitationRecord]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {CITATION_COLUMNS} FROM citations "
                "WHERE document_id = ? AND user_id = ? ORDER BY created_at ASC",
                (document_id, user_id),
            )
            rows = await cursor.fetchall()
        return [self._row_to_citation(row) for row in rows]

    async def get_by_id(self, citation_id: str, user_id: str) -> Optional[CitationRecord]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {CITATION_COLUMNS} FROM citations WHERE id = ? AND user_id = ?",
                (citation_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_citation(row) if row else None

    async def find_existing(
        self, document_id: str, user_id: str, evidence_id: Optional[str], source_id: str,
        section_id: Optional[str],
    ) -> Optional[CitationRecord]:
        """Avoid duplicate rows when the same evidence is cited twice."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {CITATION_COLUMNS} FROM citations WHERE document_id = ? AND user_id = ? "
                "AND source_id = ? AND IFNULL(evidence_id, '') = ? AND IFNULL(section_id, '') = ? "
                "LIMIT 1",
                (document_id, user_id, source_id, evidence_id or "", section_id or ""),
            )
            row = await cursor.fetchone()
        return self._row_to_citation(row) if row else None

    async def update_style(self, document_id: str, user_id: str, style: CitationStyle) -> int:
        """Re-render in-text markers when the user changes style.

        The reference list is derived on read, but in-text markers live inside the
        document text, so the caller re-renders them with
        :mod:`app.services.citation_service`.
        """
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE citations SET style = ? WHERE document_id = ? AND user_id = ?",
                (style.value, document_id, user_id),
            )
            await self.db.connection.commit()
            return cursor.rowcount

    async def update_style_and_text(
        self, citation_id: str, user_id: str, style: CitationStyle, in_text: str
    ) -> bool:
        """Persist a re-rendered in-text citation after a style change."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE citations SET style = ?, in_text = ? WHERE id = ? AND user_id = ?",
                (style.value, in_text, citation_id, user_id),
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0

    async def delete(self, citation_id: str, user_id: str) -> bool:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM citations WHERE id = ? AND user_id = ?",
                (citation_id, user_id),
            )
            await self.db.connection.commit()
            return cursor.rowcount > 0

    async def delete_for_document(self, document_id: str, user_id: str) -> int:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM citations WHERE document_id = ? AND user_id = ?",
                (document_id, user_id),
            )
            await self.db.connection.commit()
            return cursor.rowcount

    def _row_to_citation(self, row) -> CitationRecord:
        return CitationRecord(
            id=row["id"],
            user_id=row["user_id"],
            document_id=row["document_id"],
            source_id=row["source_id"],
            research_session_id=row["research_session_id"],
            evidence_id=row["evidence_id"],
            section_id=row["section_id"],
            section_title=row["section_title"],
            marker=row["marker"],
            locator=row["locator"],
            style=CitationStyle(row["style"]),
            in_text=row["in_text"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
