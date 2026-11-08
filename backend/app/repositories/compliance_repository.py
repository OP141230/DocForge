"""Repository for DocumentBrief compliance snapshots.

Results are stored as one JSON document per check rather than one row per
requirement. A compliance run is an immutable observation ("the document looked
like this at time T"), so rows-per-requirement would add joins without adding
query power. The latest snapshot is what the UI shows.
"""
import json
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.core.database import Database
from app.models.review import (
    ComplianceReport,
    ComplianceResult,
    ComplianceStatus,
)


class ComplianceRepository:
    def __init__(self, db: Database):
        self.db = db

    async def save(self, report: ComplianceReport, user_id: str) -> str:
        check_id = str(uuid4())
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO compliance_checks "
                "(id, user_id, document_id, brief_id, overall, results, document_fingerprint, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    check_id,
                    user_id,
                    report.document_id,
                    report.brief_id,
                    report.overall.value,
                    json.dumps([result.model_dump(mode="json") for result in report.results]),
                    report.document_fingerprint,
                    report.generated_at.isoformat(),
                ),
            )
            await self.db.connection.commit()
        return check_id

    async def latest(self, document_id: str, user_id: str) -> Optional[ComplianceReport]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM compliance_checks WHERE document_id = ? AND user_id = ? "
                "ORDER BY created_at DESC LIMIT 1",
                (document_id, user_id),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return ComplianceReport(
            document_id=row["document_id"],
            brief_id=row["brief_id"],
            overall=ComplianceStatus(row["overall"]),
            results=[ComplianceResult(**item) for item in json.loads(row["results"] or "[]")],
            document_fingerprint=row["document_fingerprint"],
            generated_at=datetime.fromisoformat(row["created_at"]),
        )
