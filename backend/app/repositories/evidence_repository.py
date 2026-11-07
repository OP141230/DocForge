"""Repository for the evidence layer.

Evidence is data, not prompt text: each row keeps the source it came from, the
question it answers, the passage itself, and whether the user kept it. That is
what makes traceability (and honest verification) possible.
"""
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
import sqlite3

from app.core.database import Database
from app.models.research import EvidenceRecord, EvidenceType

EVIDENCE_COLUMNS = (
    "id, session_id, source_id, user_id, research_question_id, claim_or_finding, "
    "passage, passage_hash, evidence_type, url, knowledge_file_id, page_number, "
    "section_title, retrieved_at, user_selected, notes"
)



def passage_hash(passage: str) -> str:
    """Normalize a passage before hashing so whitespace variants dedupe."""
    normalized = " ".join(passage.split()).strip().lower()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:24]


class EvidenceRepository:
    """Data access for ``research_evidence``."""

    def __init__(self, db: Database):
        self.db = db

    async def create(self, evidence: EvidenceRecord) -> Optional[EvidenceRecord]:
        """Insert evidence, returning ``None`` when the passage already exists."""
        async with self.db.connection.cursor() as cursor:
            try:
                await cursor.execute(
                    f"INSERT INTO research_evidence ({EVIDENCE_COLUMNS}) VALUES "
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        evidence.id,
                        evidence.session_id,
                        evidence.source_id,
                        evidence.user_id,
                        evidence.research_question_id,
                        evidence.claim_or_finding,
                        evidence.passage,
                        passage_hash(evidence.passage),
                        evidence.evidence_type.value,
                        evidence.url,
                        evidence.knowledge_file_id,
                        evidence.page_number,
                        evidence.section_title,
                        evidence.retrieved_at.isoformat(),
                        1 if evidence.user_selected else 0,
                        evidence.notes,
                    ),
                )
                await self.db.connection.commit()
            except sqlite3.IntegrityError:
                # Duplicate passage for this source - keep the original row.
                await self.db.connection.rollback()
                return None
        return evidence

    async def get_by_id(self, evidence_id: str, user_id: str) -> Optional[EvidenceRecord]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {EVIDENCE_COLUMNS} FROM research_evidence WHERE id = ? AND user_id = ?",
                (evidence_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_evidence(row) if row else None

    async def list_by_session(
        self,
        session_id: str,
        user_id: str,
        selected_only: bool = False,
        limit: int = 1000,
    ) -> List[EvidenceRecord]:
        query = f"SELECT {EVIDENCE_COLUMNS} FROM research_evidence WHERE session_id = ? AND user_id = ?"
        params: List[Any] = [session_id, user_id]
        if selected_only:
            query += " AND user_selected = 1"
        query += " ORDER BY retrieved_at ASC LIMIT ?"
        params.append(limit)

        async with self.db.connection.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
        return [self._row_to_evidence(row) for row in rows]

    async def list_by_source(self, source_id: str, user_id: str) -> List[EvidenceRecord]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {EVIDENCE_COLUMNS} FROM research_evidence "
                "WHERE source_id = ? AND user_id = ? ORDER BY retrieved_at ASC",
                (source_id, user_id),
            )
            rows = await cursor.fetchall()
        return [self._row_to_evidence(row) for row in rows]

    async def count_for_session(self, session_id: str, user_id: str) -> int:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM research_evidence WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )
            row = await cursor.fetchone()
        return row[0] if row else 0

    async def update(
        self, evidence_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[EvidenceRecord]:
        fields: List[str] = []
        values: List[Any] = []

        for key, value in updates.items():
            if key == "user_selected":
                fields.append("user_selected = ?")
                values.append(1 if value else 0)
            elif key == "evidence_type" and isinstance(value, EvidenceType):
                fields.append("evidence_type = ?")
                values.append(value.value)
            elif key == "notes":
                fields.append("notes = ?")
                values.append(value)

        if not fields:
            return await self.get_by_id(evidence_id, user_id)

        values.extend([evidence_id, user_id])
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"UPDATE research_evidence SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
                values,
            )
            await self.db.connection.commit()
            if cursor.rowcount == 0:
                return None
        return await self.get_by_id(evidence_id, user_id)

    async def delete(self, evidence_id: str, user_id: str) -> bool:
        conn = self.db.connection
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "DELETE FROM claim_verification_evidence WHERE evidence_id = ?", (evidence_id,)
                )
                await cursor.execute(
                    "DELETE FROM research_evidence WHERE id = ? AND user_id = ?",
                    (evidence_id, user_id),
                )
                deleted = cursor.rowcount > 0
                await conn.commit()
                return deleted
            except Exception:
                await conn.rollback()
                raise

    async def selected_by_ids(
        self, evidence_ids: List[str], user_id: str
    ) -> List[EvidenceRecord]:
        """Fetch specific evidence rows, enforcing ownership."""
        if not evidence_ids:
            return []
        placeholders = ",".join("?" for _ in evidence_ids)
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {EVIDENCE_COLUMNS} FROM research_evidence "
                f"WHERE id IN ({placeholders}) AND user_id = ?",
                [*evidence_ids, user_id],
            )
            rows = await cursor.fetchall()
        return [self._row_to_evidence(row) for row in rows]

    def _row_to_evidence(self, row) -> EvidenceRecord:
        return EvidenceRecord(
            id=row["id"],
            session_id=row["session_id"],
            source_id=row["source_id"],
            user_id=row["user_id"],
            research_question_id=row["research_question_id"],
            claim_or_finding=row["claim_or_finding"],
            passage=row["passage"],
            evidence_type=EvidenceType(row["evidence_type"]),
            url=row["url"],
            knowledge_file_id=row["knowledge_file_id"],
            page_number=row["page_number"],
            section_title=row["section_title"],
            retrieved_at=datetime.fromisoformat(row["retrieved_at"]),
            user_selected=bool(row["user_selected"]),
            notes=row["notes"],
        )
