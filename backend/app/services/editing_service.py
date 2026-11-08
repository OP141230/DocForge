"""Controlled AI editing (Phase 6).

The invariant this module protects: **a user's document never changes without an
explicit accept**, and every accepted change is recoverable.

Two-step protocol
-----------------
1. :meth:`EditingService.propose` calls the provider and stores an
   :class:`EditProposal`. The document is untouched. The proposal records the
   fingerprint of the document it was derived from.
2. :meth:`EditingService.apply` re-checks that fingerprint (optimistic
   concurrency), snapshots the pre-edit document as a version, applies the
   change, snapshots the result, and resets affected verification findings to
   *Not Checked*. If the user edited the document in another tab in between, the
   fingerprint no longer matches and the call is refused with a conflict instead
   of clobbering their work.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.database import Database
from app.models.document_ir import DocumentIR
from app.models.review import (
    OPERATION_LABELS,
    DocumentVersionNote,
    EditOperation,
    EditProposal,
    ProposalStatus,
    ProposeEditRequest,
    VersionOrigin,
)
from app.providers.base import AIProvider
from app.providers.factory import get_provider
from app.repositories.citation_repository import CitationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.review_repository import EditProposalRepository, VersionNoteRepository
from app.services.document_text import (
    DocumentTextIndex,
    block_text,
    replace_block_text,
    replace_section_text,
)

MAX_PROPOSAL_CHARS = 40000

# Each operation maps to an instruction the model can act on. Keeping them in
# one table (rather than a method per operation) means adding an operation is a
# data change, not a code path - and the API can validate against the enum.
OPERATION_INSTRUCTIONS: Dict[EditOperation, str] = {
    EditOperation.IMPROVE_CLARITY: "Rewrite for clarity. Remove ambiguity and simplify tangled phrasing without losing meaning.",
    EditOperation.FIX_GRAMMAR: "Correct grammar, spelling and punctuation. Change nothing else.",
    EditOperation.MAKE_CONCISE: "Make this more concise. Cut filler and redundancy while keeping every substantive point.",
    EditOperation.EXPAND_EXPLANATION: "Expand the explanation with more detail. Do not invent facts, figures or sources.",
    EditOperation.SIMPLIFY: "Simplify the language for a general reader. Keep technical accuracy.",
    EditOperation.IMPROVE_TRANSITIONS: "Improve the transitions so ideas connect smoothly.",
    EditOperation.IMPROVE_PROFESSIONALISM: "Rewrite in a polished, professional register.",
    EditOperation.TONE_FORMAL: "Rewrite in a formal tone.",
    EditOperation.TONE_ACADEMIC: "Rewrite in an academic tone, suitable for scholarly writing.",
    EditOperation.TONE_PROFESSIONAL: "Rewrite in a professional business tone.",
    EditOperation.TONE_CONVERSATIONAL: "Rewrite in a clear, conversational tone while staying accurate.",
    EditOperation.TONE_TECHNICAL: "Rewrite in a precise technical tone for a specialist reader.",
    EditOperation.TONE_PERSUASIVE: "Rewrite persuasively without overstating the evidence.",
    EditOperation.REWRITE_PARAGRAPH: "Rewrite this paragraph so it reads more clearly, preserving all facts and citations.",
    EditOperation.IMPROVE_INTRODUCTION: "Strengthen this introduction: state the purpose and scope, then lead into the content.",
    EditOperation.IMPROVE_CONCLUSION: "Strengthen this conclusion: summarise the key points without introducing new claims.",
    EditOperation.REORGANIZE_SECTION: "Reorganize the material into a clearer logical order.",
    EditOperation.TO_BULLETS: "Convert this prose into concise bullet points, one idea per bullet.",
    EditOperation.FROM_BULLETS: "Convert these bullet points into flowing paragraphs.",
    EditOperation.ADD_EXAMPLES: "Add one or two concrete illustrative examples. Do not invent statistics, studies or sources.",
    EditOperation.SUMMARIZE: "Summarize this content, keeping the most important points.",
    EditOperation.EXPAND_SECTION: "Expand this section with more depth. Do not invent facts or sources.",
    EditOperation.STANDARDIZE_TERMINOLOGY: "Standardize terminology so the same concept always uses the same term.",
    EditOperation.NORMALIZE_TONE: "Make the tone consistent throughout.",
    EditOperation.REDUCE_REPETITION: "Remove repetition and redundancy while keeping all distinct information.",
    EditOperation.ALIGN_OUTLINE: "Revise this content so it matches the approved outline and section purpose.",
    EditOperation.ALIGN_BRIEF: "Revise this content so it better satisfies the document brief requirements.",
}

CITATION_MARKER = re.compile(r"\[(?:E|S|C|P)\d+\]|\([A-Z][^()]{2,80}\d{4}[a-z]?\)")


class EditConflict(Exception):
    """Raised when the document changed since the proposal was created."""


class EditingService:
    def __init__(self, db: Database, *, provider: Optional[AIProvider] = None):
        self.db = db
        self.provider = provider or get_provider()
        self.documents = DocumentRepository(db)
        self.proposals = EditProposalRepository(db)
        self.notes = VersionNoteRepository(db)
        self.citations = CitationRepository(db)

    # ------------------------------------------------------------------
    # Propose
    # ------------------------------------------------------------------
    async def propose(
        self, document_id: str, user_id: str, request: ProposeEditRequest
    ) -> EditProposal:
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        index = DocumentTextIndex(document)
        original, target_section, target_block = self._resolve_target(
            document, index, request
        )
        if not original.strip():
            raise ValueError("The selected content is empty")

        instruction = OPERATION_INSTRUCTIONS[request.operation]
        if request.instruction:
            instruction = f"{instruction}\nAdditional instruction: {request.instruction}"

        payload = {
            "text": original,
            "instruction": instruction,
            "operation": request.operation.value,
            "document_title": document.title,
            "document_type": document.metadata.document_type,
            "audience": document.metadata.audience,
            "tone": document.metadata.tone,
        }

        try:
            proposed = await self.provider.transform_text(payload)
        except Exception as exc:
            raise ValueError(f"The AI provider failed: {type(exc).__name__}") from exc

        if not proposed or not proposed.strip():
            raise ValueError(
                "The AI provider returned no rewritten text. "
                "Check that AI_PROVIDER is configured for editing."
            )
        proposed = proposed.strip()[:MAX_PROPOSAL_CHARS]
        if proposed == original:
            raise ValueError("The AI provider produced no change")

        impact = await self._impact(document_id, user_id, target_section, original, proposed)

        proposal = EditProposal(
            user_id=user_id,
            document_id=document_id,
            operation=request.operation,
            target_type=request.target_type,
            section_id=target_section,
            block_id=target_block,
            original_text=original,
            proposed_text=proposed,
            status=ProposalStatus.PROPOSED,
            base_fingerprint=index.fingerprint,
            provider=type(self.provider).__name__,
            notes=request.instruction,
            impact=impact,
        )
        return await self.proposals.create(proposal)

    async def reject(self, proposal_id: str, user_id: str) -> Optional[EditProposal]:
        """Rejecting never touches the document - that is the point."""
        return await self.proposals.set_status(proposal_id, user_id, ProposalStatus.REJECTED)

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------
    async def apply(
        self,
        proposal_id: str,
        user_id: str,
        *,
        expected_fingerprint: Optional[str] = None,
    ) -> tuple[DocumentIR, EditProposal]:
        proposal = await self.proposals.get(proposal_id, user_id)
        if proposal is None:
            raise ValueError("Edit proposal not found")
        if proposal.status != ProposalStatus.PROPOSED:
            raise ValueError(f"This proposal was already {proposal.status.value}")

        document = await self.documents.get_by_id(proposal.document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        index = DocumentTextIndex(document)
        current_fingerprint = index.fingerprint
        expected = expected_fingerprint or proposal.base_fingerprint
        if expected and expected != current_fingerprint:
            raise EditConflict(
                "The document changed after this suggestion was created. "
                "Re-run the edit so it applies to the current text."
            )

        updated = self._apply_to_document(document, proposal)

        affected_verifications = await self._verification_ids_for(
            proposal.document_id, user_id, proposal.section_id
        )

        await self._apply_transactionally(
            document=document,
            updated=updated,
            proposal=proposal,
            user_id=user_id,
            affected_verifications=affected_verifications,
        )

        refreshed = await self.proposals.get(proposal_id, user_id)
        return updated, refreshed or proposal

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _resolve_target(
        self, document: DocumentIR, index: DocumentTextIndex, request: ProposeEditRequest
    ) -> tuple[str, Optional[str], Optional[str]]:
        if request.target_type == "block":
            if not request.block_id:
                raise ValueError("block_id is required for a block edit")
            unit = index.unit_for_block(request.block_id)
            if unit is None:
                raise ValueError("Block not found in this document")
            return unit.text, unit.section_id, unit.block_id

        if request.target_type == "document":
            # Deliberately unsupported: a whole-document rewrite cannot be
            # reviewed meaningfully in a diff, and one bad generation would
            # replace an entire document. Section-level edits keep the change
            # scoped and recoverable.
            raise ValueError(
                "Whole-document rewrites are not supported. Select a section and edit it."
            )

        # default: section
        if not request.section_id:
            raise ValueError("section_id is required for a section edit")
        section = next((item for item in document.content if item.id == request.section_id), None)
        if section is None:
            raise ValueError("Section not found in this document")
        text = index.section_text(section.id)
        return text, section.id, None

    def _apply_to_document(self, document: DocumentIR, proposal: EditProposal) -> DocumentIR:
        text = proposal.proposed_text
        if proposal.target_type == "block" and proposal.block_id:
            return replace_block_text(document, proposal.block_id, text)
        if not proposal.section_id:
            raise ValueError("Proposal has no target section")
        return replace_section_text(document, proposal.section_id, text)

    async def _impact(
        self,
        document_id: str,
        user_id: str,
        section_id: Optional[str],
        original: str,
        proposed: str,
    ) -> Dict[str, Any]:
        """Record which citation/verification records may need re-checking."""
        markers_before = set(CITATION_MARKER.findall(original))
        markers_after = set(CITATION_MARKER.findall(proposed))

        records = await self.citations.list_for_document(document_id, user_id)
        relevant = [
            record
            for record in records
            if section_id is None or record.section_id in (None, section_id)
        ]
        removed = sorted(markers_before - markers_after)
        added = sorted(markers_after - markers_before)

        return {
            "citations_in_scope": [record.id for record in relevant],
            "markers_removed": removed,
            "markers_added": added,
            "citation_review_required": bool(relevant) or bool(removed) or bool(added),
            "verification_recheck_required": bool(relevant),
            "notes": (
                "Citations and claim verifications in this section are marked for re-checking "
                "because the text that carried them changed."
                if relevant
                else "No citations were attached to this content."
            ),
        }

    async def _verification_ids_for(
        self, document_id: str, user_id: str, section_id: Optional[str]
    ) -> List[str]:
        async with self.db.connection.cursor() as cursor:
            if section_id:
                await cursor.execute(
                    "SELECT id FROM claim_verifications WHERE document_id = ? AND user_id = ? "
                    "AND section_id = ?",
                    (document_id, user_id, section_id),
                )
            else:
                await cursor.execute(
                    "SELECT id FROM claim_verifications WHERE document_id = ? AND user_id = ?",
                    (document_id, user_id),
                )
            rows = await cursor.fetchall()
        return [row["id"] for row in rows]

    async def _apply_transactionally(
        self,
        *,
        document: DocumentIR,
        updated: DocumentIR,
        proposal: EditProposal,
        user_id: str,
        affected_verifications: List[str],
    ) -> None:
        """Write versions, the document, and recheck flags in one transaction.

        Repositories commit on every call, which is convenient for simple CRUD
        but wrong here: a half-applied edit (document updated, version missing)
        would be unrecoverable. This block drives the connection directly so a
        single commit covers every write, and any failure rolls back cleanly.
        """
        conn = self.db.connection
        now = datetime.utcnow().isoformat()
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(
                    "SELECT COALESCE(MAX(version_number), 0) FROM document_versions WHERE document_id = ?",
                    (document.id,),
                )
                version_number = (await cursor.fetchone())[0]

                # 1. Snapshot the pre-edit state, so "undo" always has a target.
                version_number += 1
                await cursor.execute(
                    "INSERT INTO document_versions (id, document_id, version_number, content, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        str(uuid4()),
                        document.id,
                        version_number,
                        document.model_dump_json(),
                        now,
                    ),
                )
                await cursor.execute(
                    "INSERT OR REPLACE INTO document_version_notes "
                    "(document_id, version_number, user_id, origin, operation, summary, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        document.id,
                        version_number,
                        user_id,
                        VersionOrigin.AI_ACCEPTED.value,
                        f"before:{proposal.operation.value}",
                        f"State before: {OPERATION_LABELS[proposal.operation]}",
                        now,
                    ),
                )

                # 2. Apply the accepted change.
                await cursor.execute(
                    "UPDATE documents SET title = ?, content = ?, metadata = ?, updated_at = ? "
                    "WHERE id = ? AND user_id = ?",
                    (
                        updated.title,
                        json.dumps([section.model_dump() for section in updated.content]),
                        json.dumps(updated.metadata.model_dump()),
                        now,
                        document.id,
                        user_id,
                    ),
                )

                # 3. Snapshot the new state.
                version_number += 1
                await cursor.execute(
                    "INSERT INTO document_versions (id, document_id, version_number, content, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        str(uuid4()),
                        document.id,
                        version_number,
                        updated.model_dump_json(),
                        now,
                    ),
                )
                await cursor.execute(
                    "INSERT OR REPLACE INTO document_version_notes "
                    "(document_id, version_number, user_id, origin, operation, summary, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        document.id,
                        version_number,
                        user_id,
                        VersionOrigin.AI_ACCEPTED.value,
                        proposal.operation.value,
                        OPERATION_LABELS[proposal.operation],
                        now,
                    ),
                )

                # 4. Old verification results no longer describe this text.
                for verification_id in affected_verifications:
                    await cursor.execute(
                        "UPDATE claim_verifications SET status = 'not_checked', "
                        "verification_method = 'stale_after_ai_edit', "
                        "manual_review = 1, checked_at = NULL, "
                        "explanation = ? WHERE id = ? AND user_id = ?",
                        (
                            "Re-check required: the text of this claim was changed by an AI-assisted "
                            "edit, so the previous verification no longer applies.",
                            verification_id,
                            user_id,
                        ),
                    )

                # 5. Mark the proposal accepted.
                await cursor.execute(
                    "UPDATE edit_proposals SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                    (ProposalStatus.ACCEPTED.value, now, proposal.id, user_id),
                )

                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
