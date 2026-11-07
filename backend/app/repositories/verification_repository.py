"""Repository for claim verification findings.

``UNIQUE(document_id, claim_id)`` means re-checking a claim updates its finding
instead of piling up duplicates, which keeps the verification workspace
readable and makes "recheck" idempotent.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import Database
from app.models.research import (
    ClaimVerification,
    VerificationStatus,
    VerificationSummary,
)

VERIFICATION_COLUMNS = (
    "id, user_id, document_id, research_session_id, claim_id, claim_text, "
    "section_id, section_title, status, explanation, verification_method, "
    "time_sensitive, manual_review, checked_at"
)

UPDATABLE_FIELDS = {"manual_review", "status", "explanation", "checked_at", "research_session_id"}


class VerificationRepository:
    """Data access for ``claim_verifications`` and its evidence links."""

    def __init__(self, db: Database):
        self.db = db

    async def upsert(self, finding: ClaimVerification) -> ClaimVerification:
        """Insert or update one finding, then replace its evidence links."""
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"INSERT INTO claim_verifications ({VERIFICATION_COLUMNS}) VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(document_id, claim_id) DO UPDATE SET "
                "research_session_id = excluded.research_session_id, "
                "claim_text = excluded.claim_text, "
                "section_id = excluded.section_id, "
                "section_title = excluded.section_title, "
                "status = excluded.status, "
                "explanation = excluded.explanation, "
                "verification_method = excluded.verification_method, "
                "time_sensitive = excluded.time_sensitive, "
                "checked_at = excluded.checked_at",
                (
                    finding.id,
                    finding.user_id,
                    finding.document_id,
                    finding.research_session_id,
                    finding.claim_id,
                    finding.claim_text,
                    finding.section_id,
                    finding.section_title,
                    finding.status.value,
                    finding.explanation,
                    finding.verification_method,
                    1 if finding.time_sensitive else 0,
                    1 if finding.manual_review else 0,
                    finding.checked_at.isoformat() if finding.checked_at else None,
                ),
            )
            await cursor.execute(
                "SELECT id FROM claim_verifications WHERE document_id = ? AND claim_id = ?",
                (finding.document_id, finding.claim_id),
            )
            row = await cursor.fetchone()
            verification_id = row["id"] if row else finding.id

            await cursor.execute(
                "DELETE FROM claim_verification_evidence WHERE verification_id = ?",
                (verification_id,),
            )
            for evidence_id in finding.supporting_evidence_ids:
                await cursor.execute(
                    "INSERT OR IGNORE INTO claim_verification_evidence "
                    "(verification_id, evidence_id, relation) VALUES (?, ?, 'supporting')",
                    (verification_id, evidence_id),
                )
            for evidence_id in finding.contradicting_evidence_ids:
                await cursor.execute(
                    "INSERT OR IGNORE INTO claim_verification_evidence "
                    "(verification_id, evidence_id, relation) VALUES (?, ?, 'contradicting')",
                    (verification_id, evidence_id),
                )
            await self.db.connection.commit()

        finding.id = verification_id
        return finding

    async def list_for_document(
        self,
        document_id: str,
        user_id: str,
        status: Optional[VerificationStatus] = None,
    ) -> List[ClaimVerification]:
        query = (
            f"SELECT {VERIFICATION_COLUMNS} FROM claim_verifications "
            "WHERE document_id = ? AND user_id = ?"
        )
        params: List[Any] = [document_id, user_id]
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY rowid ASC"

        async with self.db.connection.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
            findings = [self._row_to_finding(row) for row in rows]

            for finding in findings:
                await cursor.execute(
                    "SELECT evidence_id, relation FROM claim_verification_evidence "
                    "WHERE verification_id = ?",
                    (finding.id,),
                )
                links = await cursor.fetchall()
                finding.supporting_evidence_ids = [
                    link["evidence_id"] for link in links if link["relation"] == "supporting"
                ]
                finding.contradicting_evidence_ids = [
                    link["evidence_id"] for link in links if link["relation"] == "contradicting"
                ]
        return findings

    async def get_by_id(self, verification_id: str, user_id: str) -> Optional[ClaimVerification]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {VERIFICATION_COLUMNS} FROM claim_verifications "
                "WHERE id = ? AND user_id = ?",
                (verification_id, user_id),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            finding = self._row_to_finding(row)
            await cursor.execute(
                "SELECT evidence_id, relation FROM claim_verification_evidence WHERE verification_id = ?",
                (finding.id,),
            )
            links = await cursor.fetchall()
        finding.supporting_evidence_ids = [
            link["evidence_id"] for link in links if link["relation"] == "supporting"
        ]
        finding.contradicting_evidence_ids = [
            link["evidence_id"] for link in links if link["relation"] == "contradicting"
        ]
        return finding

    async def update(
        self, verification_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[ClaimVerification]:
        fields: List[str] = []
        values: List[Any] = []

        for key, value in updates.items():
            if key not in UPDATABLE_FIELDS:
                continue
            if key == "manual_review":
                fields.append("manual_review = ?")
                values.append(1 if value else 0)
            elif key == "status" and isinstance(value, VerificationStatus):
                fields.append("status = ?")
                values.append(value.value)
            elif key == "checked_at" and isinstance(value, datetime):
                fields.append("checked_at = ?")
                values.append(value.isoformat())
            else:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            return await self.get_by_id(verification_id, user_id)

        values.extend([verification_id, user_id])
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"UPDATE claim_verifications SET {', '.join(fields)} "
                "WHERE id = ? AND user_id = ?",
                values,
            )
            await self.db.connection.commit()
            if cursor.rowcount == 0:
                return None
        return await self.get_by_id(verification_id, user_id)

    async def summary(self, document_id: str, user_id: str) -> VerificationSummary:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT status, COUNT(*) AS count, SUM(time_sensitive) AS sensitive "
                "FROM claim_verifications WHERE document_id = ? AND user_id = ? "
                "GROUP BY status",
                (document_id, user_id),
            )
            rows = await cursor.fetchall()

        counts: Dict[str, int] = {status.value: 0 for status in VerificationStatus}
        time_sensitive = 0
        for row in rows:
            counts[row["status"]] = row["count"]
            time_sensitive += row["sensitive"] or 0

        return VerificationSummary(
            supported=counts.get(VerificationStatus.SUPPORTED.value, 0),
            contradicted=counts.get(VerificationStatus.CONTRADICTED.value, 0),
            insufficient_evidence=counts.get(VerificationStatus.INSUFFICIENT_EVIDENCE.value, 0),
            not_checked=counts.get(VerificationStatus.NOT_CHECKED.value, 0),
            total=sum(counts.values()),
            time_sensitive=time_sensitive,
        )

    async def delete_for_document(self, document_id: str, user_id: str) -> int:
        conn = self.db.connection
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "DELETE FROM claim_verification_evidence WHERE verification_id IN "
                    "(SELECT id FROM claim_verifications WHERE document_id = ? AND user_id = ?)",
                    (document_id, user_id),
                )
                await cursor.execute(
                    "DELETE FROM claim_verifications WHERE document_id = ? AND user_id = ?",
                    (document_id, user_id),
                )
                deleted = cursor.rowcount
                await conn.commit()
                return deleted
            except Exception:
                await conn.rollback()
                raise

    def _row_to_finding(self, row) -> ClaimVerification:
        return ClaimVerification(
            id=row["id"],
            user_id=row["user_id"],
            document_id=row["document_id"],
            research_session_id=row["research_session_id"],
            claim_id=row["claim_id"],
            claim_text=row["claim_text"],
            section_id=row["section_id"],
            section_title=row["section_title"],
            status=VerificationStatus(row["status"]),
            explanation=row["explanation"],
            verification_method=row["verification_method"],
            time_sensitive=bool(row["time_sensitive"]),
            manual_review=bool(row["manual_review"]),
            checked_at=datetime.fromisoformat(row["checked_at"]) if row["checked_at"] else None,
        )
