"""Deterministic document text index.

Everything in Phase 6 that points at "a place in the document" goes through
this module, so there is exactly one interpretation of what a text location
means.

Why not global character offsets?
---------------------------------
A single running offset over the whole document is fragile: inserting one word
in section 1 shifts every offset in section 5, and a model that hallucinated
``start=4213`` would silently point at unrelated text. Instead each unit of
text carries **stable anchors** (``section_id`` + ``block_id`` from the
DocumentIR, which are UUIDs persisted with the document) plus **block-local**
offsets. Staleness is then detected with a content fingerprint rather than by
trusting numbers.

Why normalize whitespace when locating a quote?
-----------------------------------------------
Models wrap and re-indent text. Comparing ``"the  audit\npolicy"`` against
``"The audit policy"`` should succeed, so :meth:`DocumentTextIndex.locate`
compares whitespace-collapsed, case-folded text while returning offsets into
the *original* characters. If a quote cannot be located, we reject it - an
unlocatable suggestion is not applied.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from app.models.document_ir import (
    BlockType,
    DocumentIR,
    InlineContent,
    ListBlock,
    Paragraph,
    Section,
)

_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Collapse whitespace and case-fold, for comparison only."""
    return _WHITESPACE.sub(" ", (text or "")).strip().lower()


def inline_text(parts: Iterable[InlineContent]) -> str:
    return "".join(part.text for part in parts)


def block_text(block: BlockType) -> str:
    """Extract the plain text of one block, in reading order."""
    if isinstance(block, (Paragraph,)) or getattr(block, "type", "") in (
        "paragraph",
        "heading",
        "quote",
    ):
        return inline_text(block.content)
    if isinstance(block, ListBlock) or getattr(block, "type", "") == "list":
        return "\n".join(inline_text(item) for item in block.items)
    if getattr(block, "type", "") == "code_block":
        return block.code
    if getattr(block, "type", "") == "table":
        rows = []
        if block.headers:
            rows.append(" | ".join(block.headers))
        rows.extend(" | ".join(row) for row in block.rows)
        return "\n".join(rows)
    return ""


@dataclass
class TextUnit:
    """One addressable run of text: a single block."""

    section_id: str
    section_title: str
    section_level: int
    block_id: str
    block_type: str
    text: str

    @property
    def is_prose(self) -> bool:
        return self.block_type in ("paragraph", "quote")


@dataclass
class Located:
    """Result of locating a quote in the document."""

    unit: TextUnit
    start: int
    end: int

    @property
    def text(self) -> str:
        return self.unit.text[self.start : self.end]


class DocumentTextIndex:
    """Read-only addressing view over a :class:`DocumentIR`."""

    def __init__(self, document: DocumentIR):
        self.document = document
        self.units: List[TextUnit] = []
        for section in document.content:
            for block in section.blocks:
                text = block_text(block)
                if not text.strip():
                    continue
                self.units.append(
                    TextUnit(
                        section_id=section.id,
                        section_title=section.title,
                        section_level=section.level,
                        block_id=block.id,
                        block_type=getattr(block, "type", type(block).__name__),
                        text=text,
                    )
                )

    # -- basic aggregates -------------------------------------------------
    @property
    def full_text(self) -> str:
        return "\n\n".join(unit.text for unit in self.units)

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())

    @property
    def fingerprint(self) -> str:
        """Stable hash of the document *content* (ids included).

        Renaming the title changes the fingerprint (and correctly stales old
        findings). Reordering unrelated fields in memory does not, because the
        JSON is canonicalised.
        """
        payload = {
            "title": self.document.title,
            "sections": [
                {
                    "id": section.id,
                    "level": section.level,
                    "title": section.title,
                    "blocks": [
                        {
                            "id": block.id,
                            "type": getattr(block, "type", ""),
                            "text": block_text(block),
                        }
                        for block in section.blocks
                    ],
                }
                for section in self.document.content
            ],
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # -- lookups ----------------------------------------------------------
    def unit_for_block(self, block_id: str) -> Optional[TextUnit]:
        return next((unit for unit in self.units if unit.block_id == block_id), None)

    def units_for_section(self, section_id: str) -> List[TextUnit]:
        return [unit for unit in self.units if unit.section_id == section_id]

    def section_text(self, section_id: str) -> str:
        return "\n\n".join(unit.text for unit in self.units_for_section(section_id))

    def locate(self, quote: str, *, hint_block_id: Optional[str] = None) -> Optional[Located]:
        """Find ``quote`` in the document, returning original-character offsets.

        Order: exact match inside the hinted block, then any block, then a
        whitespace/case-insensitive match. Returns ``None`` when the quote does
        not exist - callers must treat that as "reject this suggestion".
        """
        quote = (quote or "").strip()
        if not quote:
            return None

        candidates = self.units
        if hint_block_id:
            hinted = self.unit_for_block(hint_block_id)
            if hinted is not None:
                candidates = [hinted] + [unit for unit in self.units if unit is not hinted]

        for unit in candidates:
            position = unit.text.find(quote)
            if position >= 0:
                return Located(unit=unit, start=position, end=position + len(quote))

        target = normalize(quote)
        if not target:
            return None
        for unit in candidates:
            located = self._locate_normalized(unit, target)
            if located:
                return located
        return None

    @staticmethod
    def _locate_normalized(unit: TextUnit, target: str) -> Optional[Located]:
        """Map a whitespace-insensitive match back onto original offsets."""
        text = unit.text
        # Build normalized text plus an index from normalized char -> original.
        buffer: List[str] = []
        mapping: List[int] = []
        previous_space = False
        for index, char in enumerate(text):
            if char.isspace():
                if previous_space or not buffer:
                    continue
                buffer.append(" ")
                mapping.append(index)
                previous_space = True
                continue
            previous_space = False
            buffer.append(char.lower())
            mapping.append(index)

        normalized = "".join(buffer).strip()
        position = normalized.find(target)
        if position < 0:
            return None
        first = mapping[position]
        last_normalized = position + len(target) - 1
        last = mapping[min(last_normalized, len(mapping) - 1)]
        # Extend to the end of the matched word so we do not cut mid-character.
        end = last + 1
        while end < len(text) and not text[end].isspace():
            end += 1
        return Located(unit=unit, start=first, end=end)


# ---------------------------------------------------------------------------
# Mutation helpers (used by the editing service)
# ---------------------------------------------------------------------------

def replace_block_text(document: DocumentIR, block_id: str, new_text: str) -> DocumentIR:
    """Return a copy of ``document`` with one block's text replaced.

    The block keeps its id and type, so citations/anchors elsewhere stay valid.
    Inline formatting inside the block is intentionally flattened: an AI rewrite
    cannot be trusted to preserve per-word emphasis, and inventing it would be
    worse than losing it. The previous version is preserved by the version
    history, so nothing is unrecoverable.
    """
    data = document.model_dump()
    replaced = False
    for section in data["content"]:
        for block in section["blocks"]:
            if block.get("id") != block_id:
                continue
            if block.get("type") in ("paragraph", "heading", "quote"):
                block["content"] = [{"text": new_text}]
            elif block.get("type") == "list":
                block["items"] = [[{"text": line.strip()}] for line in new_text.splitlines() if line.strip()]
            elif block.get("type") == "code_block":
                block["code"] = new_text
            else:
                raise ValueError(f"Block type {block.get('type')!r} cannot be replaced by text")
            replaced = True
            break
        if replaced:
            break
    if not replaced:
        raise ValueError(f"Block {block_id} not found")
    return DocumentIR(**data)


def replace_section_text(document: DocumentIR, section_id: str, new_text: str) -> DocumentIR:
    """Replace all prose in a section with one paragraph of ``new_text``.

    Non-prose blocks (tables, code) are preserved in place, because destroying
    structured content during a "rewrite this section" request would be data
    loss. The rewritten prose is inserted where the first prose block was.
    """
    data = document.model_dump()
    for section in data["content"]:
        if section.get("id") != section_id:
            continue
        kept = [block for block in section["blocks"] if block.get("type") in ("table", "code_block")]
        new_block = {
            "id": None,
            "type": "paragraph",
            "content": [{"text": new_text}],
        }
        prose_block_id = next(
            (
                block["id"]
                for block in section["blocks"]
                if block.get("type") in ("paragraph", "heading", "quote", "list")
            ),
            None,
        )
        if prose_block_id is None:
            from uuid import uuid4

            prose_block_id = str(uuid4())
        new_block["id"] = prose_block_id
        section["blocks"] = [new_block, *kept] if kept else [new_block]
        return DocumentIR(**data)
    raise ValueError(f"Section {section_id} not found")


def document_outline(document: DocumentIR) -> List[Tuple[int, str]]:
    """(level, title) pairs for structural comparison against a brief."""
    return [(section.level, section.title) for section in document.content]
