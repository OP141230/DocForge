"""Repositories for Phase 6 review sessions, findings, proposals and notes.

Every query is scoped by ``user_id`` so a forged id from the client cannot reach
another user's data. The API layer additionally verifies document ownership
before creating anything, giving defence in depth.
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import Database
from app.models.review import (
    EditProposal,
    EditOperation,
    FindingSource,
    FindingStatus,
    ProposalStatus,
    ReviewCategory,
    ReviewFinding,
    ReviewMode,
    ReviewScope,
    ReviewSession,
    ReviewStatus,
    Severity,
    VersionOrigin,
    DocumentVersionNote,
)


def _iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _parse(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


SESSION_COLUMNS = (
    "id, user_id, document_id, brief_id, mode, categories, scope, section_id, status, "
    "document_fingerprint, provider, provider_message, error, progress_message, "
    "findings_total, created_at, updated_at, completed_at"
)

FINDING_COLUMNS = (
    "id, user_id, review_id, document_id, category, severity, source, title, explanation, "
    "section_id, section_title, block_id, original_text, start_offset, end_offset, "
    "suggested_text, status, evidence_ids, citation_ids, document_fingerprint, "
    "created_at, updated_at"
)

PROPOSAL_COLUMNS = (
    "id, user_id, document_id, review_id, finding_id, operation, target_type, section_id, "
    "block_id, original_text, proposed_text, status, base_fingerprint, provider, notes, "
    "impact, created_at, updated_at"
)


class ReviewRepository:
    """Data access for review sessions and their findings."""

    def __init__(self, db: Database):
        self.db = db

    # -- sessions ---------------------------------------------------------
    async def create_session(self, session: ReviewSession) -> ReviewSession:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"INSERT INTO review_sessions ({SESSION_COLUMNS}) VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session.id,
                    session.user_id,
                    session.document_id,
                    session.brief_id,
                    session.mode.value,
                    json.dumps([category.value for category in session.categories]),
                    session.scope.value,
                    session.section_id,
                    session.status.value,
                    session.document_fingerprint,
                    session.provider,
                    session.provider_message,
                    session.error,
                    session.progress_message,
                    session.findings_total,
                    _iso(session.created_at),
                    _iso(session.updated_at),
                    _iso(session.completed_at),
                ),
            )
            await self.db.connection.commit()
        return session

    async def update_session(self, session: ReviewSession) -> ReviewSession:
        session.updated_at = datetime.utcnow()
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE review_sessions SET status = ?, provider = ?, provider_message = ?, "
                "error = ?, progress_message = ?, findings_total = ?, updated_at = ?, "
                "completed_at = ? WHERE id = ? AND user_id = ?",
                (
                    session.status.value,
                    session.provider,
                    session.provider_message,
                    session.error,
                    session.progress_message,
                    session.findings_total,
                    _iso(session.updated_at),
                    _iso(session.completed_at),
                    session.id,
                    session.user_id,
                ),
            )
            await self.db.connection.commit()
        return session

    async def get_session(self, review_id: str, user_id: str) -> Optional[ReviewSession]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {SESSION_COLUMNS} FROM review_sessions WHERE id = ? AND user_id = ?",
                (review_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_session(row) if row else None

    async def list_sessions(
        self, document_id: str, user_id: str, limit: int = 20
    ) -> List[ReviewSession]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {SESSION_COLUMNS} FROM review_sessions "
                "WHERE document_id = ? AND user_id = ? ORDER BY created_at DESC LIMIT ?",
                (document_id, user_id, limit),
            )
            rows = await cursor.fetchall()
        return [self._row_to_session(row) for row in rows]

    async def latest_session(self, document_id: str, user_id: str) -> Optional[ReviewSession]:
        sessions = await self.list_sessions(document_id, user_id, limit=1)
        return sessions[0] if sessions else None

    # -- findings ---------------------------------------------------------
    async def add_findings(self, findings: List[ReviewFinding]) -> int:
        if not findings:
            return 0
        async with self.db.connection.cursor() as cursor:
            for finding in findings:
                await cursor.execute(
                    f"INSERT INTO review_findings ({FINDING_COLUMNS}) VALUES "
                    "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        finding.id,
                        finding.user_id,
                        finding.review_id,
                        finding.document_id,
                        finding.category.value,
                        finding.severity.value,
                        finding.source.value,
                        finding.title,
                        finding.explanation,
                        finding.section_id,
                        finding.section_title,
                        finding.block_id,
                        finding.original_text,
                        finding.start_offset,
                        finding.end_offset,
                        finding.suggested_text,
                        finding.status.value,
                        json.dumps(finding.evidence_ids),
                        json.dumps(finding.citation_ids),
                        finding.document_fingerprint,
                        _iso(finding.created_at),
                        _iso(finding.updated_at),
                    ),
                )
            await self.db.connection.commit()
        return len(findings)

    async def list_findings(
        self,
        review_id: str,
        user_id: str,
        *,
        category: Optional[ReviewCategory] = None,
        severity: Optional[Severity] = None,
        status: Optional[FindingStatus] = None,
    ) -> List[ReviewFinding]:
        query = f"SELECT {FINDING_COLUMNS} FROM review_findings WHERE review_id = ? AND user_id = ?"
        params: List[Any] = [review_id, user_id]
        if category:
            query += " AND category = ?"
            params.append(category.value)
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at ASC, rowid ASC"

        async with self.db.connection.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
        return [self._row_to_finding(row) for row in rows]

    async def get_finding(self, finding_id: str, user_id: str) -> Optional[ReviewFinding]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {FINDING_COLUMNS} FROM review_findings WHERE id = ? AND user_id = ?",
                (finding_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_finding(row) if row else None

    async def update_finding_status(
        self, finding_id: str, user_id: str, status: FindingStatus
    ) -> Optional[ReviewFinding]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE review_findings SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (status.value, _iso(datetime.utcnow()), finding_id, user_id),
            )
            await self.db.connection.commit()
            if cursor.rowcount == 0:
                return None
        return await self.get_finding(finding_id, user_id)

    async def delete_for_document(self, document_id: str, user_id: str) -> int:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM review_findings WHERE document_id = ? AND user_id = ?",
                (document_id, user_id),
            )
            deleted = cursor.rowcount
            await cursor.execute(
                "DELETE FROM review_sessions WHERE document_id = ? AND user_id = ?",
                (document_id, user_id),
            )
            await self.db.connection.commit()
        return deleted

    # -- mappers ----------------------------------------------------------
    def _row_to_session(self, row) -> ReviewSession:
        return ReviewSession(
            id=row["id"],
            user_id=row["user_id"],
            document_id=row["document_id"],
            brief_id=row["brief_id"],
            mode=ReviewMode(row["mode"]),
            categories=[ReviewCategory(value) for value in json.loads(row["categories"] or "[]")],
            scope=ReviewScope(row["scope"]),
            section_id=row["section_id"],
            status=ReviewStatus(row["status"]),
            document_fingerprint=row["document_fingerprint"],
            provider=row["provider"],
            provider_message=row["provider_message"],
            error=row["error"],
            progress_message=row["progress_message"],
            findings_total=row["findings_total"],
            created_at=_parse(row["created_at"]),
            updated_at=_parse(row["updated_at"]),
            completed_at=_parse(row["completed_at"]),
        )

    def _row_to_finding(self, row) -> ReviewFinding:
        return ReviewFinding(
            id=row["id"],
            user_id=row["user_id"],
            review_id=row["review_id"],
            document_id=row["document_id"],
            category=ReviewCategory(row["category"]),
            severity=Severity(row["severity"]),
            source=FindingSource(row["source"]),
            title=row["title"],
            explanation=row["explanation"],
            section_id=row["section_id"],
            section_title=row["section_title"],
            block_id=row["block_id"],
            original_text=row["original_text"],
            start_offset=row["start_offset"],
            end_offset=row["end_offset"],
            suggested_text=row["suggested_text"],
            status=FindingStatus(row["status"]),
            evidence_ids=json.loads(row["evidence_ids"] or "[]"),
            citation_ids=json.loads(row["citation_ids"] or "[]"),
            document_fingerprint=row["document_fingerprint"],
            created_at=_parse(row["created_at"]),
            updated_at=_parse(row["updated_at"]),
        )


class EditProposalRepository:
    """Data access for AI edit proposals."""

    def __init__(self, db: Database):
        self.db = db

    async def create(self, proposal: EditProposal) -> EditProposal:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"INSERT INTO edit_proposals ({PROPOSAL_COLUMNS}) VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    proposal.id,
                    proposal.user_id,
                    proposal.document_id,
                    proposal.review_id,
                    proposal.finding_id,
                    proposal.operation.value,
                    proposal.target_type,
                    proposal.section_id,
                    proposal.block_id,
                    proposal.original_text,
                    proposal.proposed_text,
                    proposal.status.value,
                    proposal.base_fingerprint,
                    proposal.provider,
                    proposal.notes,
                    json.dumps(proposal.impact),
                    _iso(proposal.created_at),
                    _iso(proposal.updated_at),
                ),
            )
            await self.db.connection.commit()
        return proposal

    async def get(self, proposal_id: str, user_id: str) -> Optional[EditProposal]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                f"SELECT {PROPOSAL_COLUMNS} FROM edit_proposals WHERE id = ? AND user_id = ?",
                (proposal_id, user_id),
            )
            row = await cursor.fetchone()
        return self._row_to_proposal(row) if row else None

    async def list_for_document(
        self, document_id: str, user_id: str, status: Optional[ProposalStatus] = None
    ) -> List[EditProposal]:
        query = f"SELECT {PROPOSAL_COLUMNS} FROM edit_proposals WHERE document_id = ? AND user_id = ?"
        params: List[Any] = [document_id, user_id]
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC"
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()
        return [self._row_to_proposal(row) for row in rows]

    async def set_status(
        self, proposal_id: str, user_id: str, status: ProposalStatus
    ) -> Optional[EditProposal]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "UPDATE edit_proposals SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (status.value, _iso(datetime.utcnow()), proposal_id, user_id),
            )
            await self.db.connection.commit()
            if cursor.rowcount == 0:
                return None
        return await self.get(proposal_id, user_id)

    def _row_to_proposal(self, row) -> EditProposal:
        return EditProposal(
            id=row["id"],
            user_id=row["user_id"],
            document_id=row["document_id"],
            review_id=row["review_id"],
            finding_id=row["finding_id"],
            operation=EditOperation(row["operation"]),
            target_type=row["target_type"],
            section_id=row["section_id"],
            block_id=row["block_id"],
            original_text=row["original_text"],
            proposed_text=row["proposed_text"],
            status=ProposalStatus(row["status"]),
            base_fingerprint=row["base_fingerprint"],
            provider=row["provider"],
            notes=row["notes"],
            impact=json.loads(row["impact"] or "{}"),
            created_at=_parse(row["created_at"]),
            updated_at=_parse(row["updated_at"]),
        )


class VersionNoteRepository:
    """Provenance for ``document_versions`` rows."""

    def __init__(self, db: Database):
        self.db = db

    async def record(self, note: DocumentVersionNote) -> DocumentVersionNote:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "INSERT OR REPLACE INTO document_version_notes "
                "(document_id, version_number, user_id, origin, operation, summary, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    note.document_id,
                    note.version_number,
                    note.user_id,
                    note.origin.value,
                    note.operation,
                    note.summary,
                    _iso(note.created_at),
                ),
            )
            await self.db.connection.commit()
        return note

    async def for_document(
        self, document_id: str, user_id: str
    ) -> Dict[int, DocumentVersionNote]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT document_id, version_number, user_id, origin, operation, summary, created_at "
                "FROM document_version_notes WHERE document_id = ? AND user_id = ?",
                (document_id, user_id),
            )
            rows = await cursor.fetchall()
        return {
            row["version_number"]: DocumentVersionNote(
                document_id=row["document_id"],
                version_number=row["version_number"],
                user_id=row["user_id"],
                origin=VersionOrigin(row["origin"]),
                operation=row["operation"],
                summary=row["summary"],
                created_at=_parse(row["created_at"]),
            )
            for row in rows
        }
