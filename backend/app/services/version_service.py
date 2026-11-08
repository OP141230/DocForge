"""Document version history for Phase 6.

``document_versions`` already stored snapshots (Phase 1) but had no provenance
and no comparison. This service adds:

* **Provenance** from ``document_version_notes`` (manual / ai_accepted / restore).
* **Comparison** using a line diff over the flattened text, so the UI does not
  have to understand block structure to show what changed.
* **Safe restore**: the current state is snapshotted *before* restoring, so the
  restore action is itself undoable and no version is ever lost.
"""
from __future__ import annotations

import difflib
import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from app.core.database import Database
from app.models.document_ir import DocumentIR
from app.models.review import (
    VersionComparison,
    VersionEntry,
    VersionOrigin,
)
from app.repositories.document_repository import DocumentRepository
from app.repositories.review_repository import VersionNoteRepository
from app.services.document_text import DocumentTextIndex

MAX_DIFF_LINES = 400


class VersionService:
    def __init__(self, db: Database):
        self.db = db
        self.documents = DocumentRepository(db)
        self.notes = VersionNoteRepository(db)

    async def list_versions(self, document_id: str, user_id: str) -> List[VersionEntry]:
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        notes = await self.notes.for_document(document_id, user_id)
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT version_number, created_at, content FROM document_versions "
                "WHERE document_id = ? ORDER BY version_number DESC",
                (document_id,),
            )
            rows = await cursor.fetchall()

        entries: List[VersionEntry] = []
        for row in rows:
            note = notes.get(row["version_number"])
            try:
                payload = json.loads(row["content"])
                words = DocumentTextIndex(DocumentIR(**payload)).word_count
            except Exception:
                words = 0
            entries.append(
                VersionEntry(
                    version_number=row["version_number"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    origin=note.origin if note else VersionOrigin.MANUAL,
                    operation=note.operation if note else None,
                    summary=note.summary if note else None,
                    word_count=words,
                )
            )
        return entries

    async def compare(
        self, document_id: str, user_id: str, from_version: int, to_version: int
    ) -> VersionComparison:
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        left = await self._load_version(document_id, from_version)
        right = await self._load_version(document_id, to_version)
        if left is None or right is None:
            raise ValueError("Version not found")

        left_index = DocumentTextIndex(left)
        right_index = DocumentTextIndex(right)

        diff = list(
            difflib.unified_diff(
                left_index.full_text.splitlines(),
                right_index.full_text.splitlines(),
                fromfile=f"v{from_version}",
                tofile=f"v{to_version}",
                lineterm="",
                n=1,
            )
        )[:MAX_DIFF_LINES]

        left_sections = {section.title: section.id for section in left.content}
        right_sections = {section.title: section.id for section in right.content}
        changed = [
            title
            for title in list(dict.fromkeys(list(left_sections) + list(right_sections)))
            if title not in left_sections
            or title not in right_sections
            or left_sections.get(title) != right_sections.get(title)
            or self._section_text(left, title) != self._section_text(right, title)
        ]

        return VersionComparison(
            document_id=document_id,
            from_version=from_version,
            to_version=to_version,
            from_title=left.title,
            to_title=right.title,
            from_word_count=left_index.word_count,
            to_word_count=right_index.word_count,
            diff=diff,
            changed_sections=changed[:50],
        )

    async def restore(
        self, document_id: str, user_id: str, version_number: int
    ) -> DocumentIR:
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        target = await self._load_version(document_id, version_number)
        if target is None:
            raise ValueError("Version not found")

        conn = self.db.connection
        now = datetime.utcnow().isoformat()
        restored = target.model_copy(deep=True)
        restored.id = document.id
        restored.updated_at = datetime.utcnow()

        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "SELECT COALESCE(MAX(version_number), 0) FROM document_versions WHERE document_id = ?",
                    (document_id,),
                )
                next_version = (await cursor.fetchone())[0] + 1

                # Snapshot the current state first: restoring is reversible.
                await cursor.execute(
                    "INSERT INTO document_versions (id, document_id, version_number, content, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (str(uuid4()), document_id, next_version, document.model_dump_json(), now),
                )
                await cursor.execute(
                    "INSERT OR REPLACE INTO document_version_notes "
                    "(document_id, version_number, user_id, origin, operation, summary, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        document_id,
                        next_version,
                        user_id,
                        VersionOrigin.RESTORE.value,
                        f"before_restore_v{version_number}",
                        f"State before restoring version {version_number}",
                        now,
                    ),
                )

                await cursor.execute(
                    "UPDATE documents SET title = ?, content = ?, metadata = ?, updated_at = ? "
                    "WHERE id = ? AND user_id = ?",
                    (
                        restored.title,
                        json.dumps([section.model_dump() for section in restored.content]),
                        json.dumps(restored.metadata.model_dump()),
                        now,
                        document_id,
                        user_id,
                    ),
                )
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise

        return restored

    async def _load_version(
        self, document_id: str, version_number: int
    ) -> Optional[DocumentIR]:
        async with self.db.connection.cursor() as cursor:
            await cursor.execute(
                "SELECT content FROM document_versions WHERE document_id = ? AND version_number = ?",
                (document_id, version_number),
            )
            row = await cursor.fetchone()
        if not row:
            return None
        return DocumentIR(**json.loads(row["content"]))

    @staticmethod
    def _section_text(document: DocumentIR, title: str) -> str:
        section = next((item for item in document.content if item.title == title), None)
        if section is None:
            return ""
        return DocumentTextIndex(
            DocumentIR(
                title=document.title,
                content=[section],
                metadata=document.metadata,
            )
        ).full_text
