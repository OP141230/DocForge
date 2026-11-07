"""Citation integration: markers -> source-linked citations -> reference lists.

The generation prompt asks the model to write markers like ``[E1]``. Those
markers are *not* citations yet: they are converted only when they resolve to a
real evidence row and a real source record owned by the user.

This is the core anti-fabrication mechanism of Phase 5:

* a marker that does not resolve is **removed** and counted, so the model cannot
  invent a source;
* the in-text string is produced from our own source metadata rather than model
  output, so authors/dates/URLs cannot be hallucinated;
* integrity checks report orphan references, uncited sources, missing metadata,
  duplicated references and anchors that disappeared after editing.

Limitations (documented in docs/phase-5-research.md): a marker must not be split
across two inline runs, and changing style works by replacing the previously
rendered in-text string - a document hand-edited to remove that string will show
up in the integrity checks as an orphan instead of being silently rewritten.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Tuple

from app.core.database import Database
from app.models.document_ir import DocumentIR, ListBlock, Paragraph, Quote, Table
from app.models.research import (
    CitationIssue,
    CitationRecord,
    CitationStyle,
    EvidenceRecord,
    ReferenceEntry,
    ReferenceListResponse,
    ResearchSource,
)
from app.repositories.citation_repository import CitationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.repositories.research_source_repository import ResearchSourceRepository
from app.services.citations import (
    CitationSource,
    format_in_text,
    format_reference,
    normalize_style,
    source_sort_key,
)

MARKER_PATTERN = re.compile(r"\[E(\d{1,3})\]")


@dataclass
class MarkerResult:
    """Outcome of converting markers in one document."""

    citations_created: int = 0
    markers_replaced: int = 0
    markers_removed: int = 0
    style: CitationStyle = CitationStyle.APA


def citation_source_from_record(source: ResearchSource) -> CitationSource:
    """Adapt a stored source to the pure formatters in ``app.services.citations``."""
    authors: List[str] = []
    if source.author:
        for chunk in re.split(r";|\s+and\s+", source.author):
            cleaned = chunk.strip()
            if cleaned:
                authors.append(cleaned)

    return CitationSource(
        source_id=source.id,
        title=source.title,
        authors=authors[:20],
        publisher=source.publisher,
        published_date=source.published_date,
        url=source.url,
        accessed_at=source.accessed_at,
        source_type=source.source_type.value,
        site_name=source.publisher,
        page_number=source.page_number,
        section_title=source.section_title,
    )


class _TextNode:
    """Uniform read/write adapter over inline runs, list items and table cells."""

    def __init__(self, getter, setter):
        self._getter = getter
        self._setter = setter

    @property
    def text(self) -> str:
        return self._getter() or ""

    @text.setter
    def text(self, value: str) -> None:
        self._setter(value)


def _iter_text_nodes(document: DocumentIR) -> Iterator[Tuple[_TextNode, "object"]]:
    """Yield every editable text string together with its section."""
    for section in document.content:
        for block in section.blocks:
            if isinstance(block, Paragraph) or isinstance(block, Quote):
                for run in block.content:
                    yield _TextNode(lambda run=run: run.text, lambda value, run=run: setattr(run, "text", value)), section
            elif isinstance(block, ListBlock):
                for item in block.items:
                    for run in item:
                        yield _TextNode(lambda run=run: run.text, lambda value, run=run: setattr(run, "text", value)), section
            elif isinstance(block, Table):
                for row_index, row in enumerate(block.rows):
                    for column_index in range(len(row)):
                        def _getter(block=block, r=row_index, c=column_index):
                            return block.rows[r][c]

                        def _setter(value, block=block, r=row_index, c=column_index):
                            block.rows[r][c] = value

                        yield _TextNode(_getter, _setter), section


class CitationService:
    """Creates citations from evidence and renders reference lists."""

    def __init__(self, db: Database):
        self.db = db
        self.citations = CitationRepository(db)
        self.sources = ResearchSourceRepository(db)
        self.evidence = EvidenceRepository(db)
        self.documents = DocumentRepository(db)

    # -- creation ---------------------------------------------------------
    async def apply_evidence_markers(
        self,
        document: DocumentIR,
        document_id: str,
        user_id: str,
        evidence_items: List[Tuple[EvidenceRecord, ResearchSource]],
        style: CitationStyle | str = CitationStyle.APA,
    ) -> MarkerResult:
        """Rewrite ``[E1]`` markers into real, source-linked in-text citations."""
        normalized_style = normalize_style(style)
        result = MarkerResult(style=normalized_style)

        if not evidence_items:
            for node, _section in _iter_text_nodes(document):
                cleaned, _replaced, removed = _substitute(node.text, lambda _i: (None, None))
                if removed:
                    node.text = cleaned
                    result.markers_removed += removed
            return result

        source_number: Dict[str, int] = {}

        def number_for(source_id: str) -> int:
            if source_id not in source_number:
                source_number[source_id] = len(source_number) + 1
            return source_number[source_id]

        for node, section in _iter_text_nodes(document):
            pending: List[Tuple[int, EvidenceRecord, ResearchSource, str]] = []

            def resolver(index: int, _pending=pending) -> Optional[str]:
                if index < 1 or index > len(evidence_items):
                    return None
                evidence_record, source = evidence_items[index - 1]
                rendered = format_in_text(
                    citation_source_from_record(source),
                    normalized_style,
                    index=number_for(source.id),
                    locator=str(source.page_number) if source.page_number else None,
                )
                _pending.append((index, evidence_record, source, rendered))
                return rendered

            if MARKER_PATTERN.search(node.text) is None:
                continue

            new_text, replaced, removed = _substitute(node.text, lambda i: (resolver(i), None))
            node.text = new_text
            result.markers_replaced += replaced
            result.markers_removed += removed

            for index, evidence_record, source, rendered in pending:
                existing = await self.citations.find_existing(
                    document_id, user_id, evidence_record.id, source.id, section.id
                )
                if existing:
                    continue
                await self.citations.create(
                    CitationRecord(
                        user_id=user_id,
                        document_id=document_id,
                        source_id=source.id,
                        research_session_id=evidence_record.session_id,
                        evidence_id=evidence_record.id,
                        section_id=section.id,
                        section_title=section.title,
                        marker=f"E{index}",
                        locator=str(source.page_number) if source.page_number else None,
                        style=normalized_style,
                        in_text=rendered,
                    )
                )
                result.citations_created += 1

        return result

    # -- reference lists --------------------------------------------------
    async def reference_list(
        self,
        document_id: str,
        user_id: str,
        style: CitationStyle | str = CitationStyle.APA,
        document: Optional[DocumentIR] = None,
        session_id: Optional[str] = None,
    ) -> ReferenceListResponse:
        """Render the reference list and run citation-integrity checks."""
        normalized_style = normalize_style(style)
        citations = await self.citations.list_for_document(document_id, user_id)
        issues: List[CitationIssue] = []

        if document is None:
            document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        grouped: List[str] = []
        per_source: Dict[str, List[CitationRecord]] = {}
        for citation in citations:
            if citation.source_id not in per_source:
                per_source[citation.source_id] = []
                grouped.append(citation.source_id)
            per_source[citation.source_id].append(citation)

        sources: Dict[str, ResearchSource] = {}
        for source_id in grouped:
            source = await self.sources.get_by_id(source_id, user_id)
            if source is None:
                issues.append(
                    CitationIssue(
                        code="source_missing",
                        severity="error",
                        message=(
                            "A citation points at a source record that no longer exists. "
                            "The reference cannot be verified."
                        ),
                        source_id=source_id,
                    )
                )
                continue
            sources[source_id] = source

            # Traceability: every citation's evidence must belong to its source.
            for citation in per_source[source_id]:
                if not citation.evidence_id:
                    continue
                evidence_record = await self.evidence.get_by_id(citation.evidence_id, user_id)
                if evidence_record and evidence_record.source_id != citation.source_id:
                    issues.append(
                        CitationIssue(
                            code="citation_attached_to_wrong_source",
                            severity="error",
                            message=(
                                f"A citation for '{source.title[:60]}' was created from evidence "
                                "that belongs to a different source."
                            ),
                            citation_id=citation.id,
                            source_id=source_id,
                        )
                    )

            if not any([source.author, source.published_date, source.publisher]):
                issues.append(
                    CitationIssue(
                        code="missing_metadata",
                        severity="warning",
                        message=(
                            f"'{source.title[:60]}' has no author, date or publisher, so the "
                            "reference is rendered with explicit placeholders."
                        ),
                        source_id=source_id,
                    )
                )

            if source.url and not re.match(r"^https?://", source.url, re.IGNORECASE):
                issues.append(
                    CitationIssue(
                        code="invalid_url",
                        severity="warning",
                        message=f"'{source.title[:60]}' has a URL that is not http(s).",
                        source_id=source_id,
                    )
                )

        seen_titles: Dict[str, str] = {}
        for source_id, source in sources.items():
            key = f"{(source.title or '').strip().lower()}|{(source.publisher or '').strip().lower()}"
            if key in seen_titles:
                issues.append(
                    CitationIssue(
                        code="duplicate_reference",
                        severity="warning",
                        message=(
                            "Two source records produce the same reference: "
                            f"'{source.title[:60]}'."
                        ),
                        source_id=source_id,
                    )
                )
            else:
                seen_titles[key] = source_id

        section_ids = {section.id for section in document.content}
        for citation in citations:
            if citation.section_id and citation.section_id not in section_ids:
                issues.append(
                    CitationIssue(
                        code="citation_anchor_missing",
                        severity="warning",
                        message=(
                            "A citation belongs to a section that is no longer in the document. "
                            "The reference is kept, but its in-text marker may be gone."
                        ),
                        citation_id=citation.id,
                        source_id=citation.source_id,
                    )
                )

        leftover = MARKER_PATTERN.findall(document_text(document))
        if leftover:
            issues.append(
                CitationIssue(
                    code="broken_reference",
                    severity="error",
                    message=(
                        f"{len(leftover)} raw citation marker(s) do not resolve to a source and "
                        "appear as unformatted keys in the document."
                    ),
                )
            )

        if normalized_style == CitationStyle.IEEE:
            ordered_ids = [source_id for source_id in grouped if source_id in sources]
        else:
            ordered_ids = [
                source.id
                for source in sorted(
                    sources.values(),
                    key=lambda item: source_sort_key(citation_source_from_record(item)),
                )
            ]

        entries: List[ReferenceEntry] = []
        for index, source_id in enumerate(ordered_ids, 1):
            source = sources[source_id]
            entries.append(
                ReferenceEntry(
                    citation_id=per_source[source_id][0].id,
                    source_id=source_id,
                    index=index,
                    text=format_reference(
                        citation_source_from_record(source), normalized_style, index
                    ),
                )
            )

        uncited: List[str] = []
        if session_id:
            session_sources = await self.sources.list_by_session(
                session_id, user_id, selected_only=True
            )
            cited_ids = set(grouped)
            uncited = [source.id for source in session_sources if source.id not in cited_ids]
            for source in session_sources:
                if source.id in uncited and len(uncited) <= 10:
                    issues.append(
                        CitationIssue(
                            code="source_not_cited",
                            severity="warning",
                            message=(
                                f"'{source.title[:60]}' is selected in the research session but "
                                "never cited in the document."
                            ),
                            source_id=source.id,
                        )
                    )

        return ReferenceListResponse(
            document_id=document_id,
            style=normalized_style,
            entries=entries,
            issues=issues,
            uncited_source_ids=uncited,
        )

    async def restyle(
        self,
        document_id: str,
        user_id: str,
        style: CitationStyle | str,
    ) -> ReferenceListResponse:
        """Re-render in-text citations in a new style and persist the change."""
        normalized_style = normalize_style(style)
        document = await self.documents.get_by_id(document_id, user_id)
        if document is None:
            raise ValueError("Document not found")

        citations = await self.citations.list_for_document(document_id, user_id)
        if not citations:
            return await self.reference_list(
                document_id, user_id, normalized_style, document=document
            )

        source_order: Dict[str, int] = {}
        for citation in citations:
            if citation.source_id not in source_order:
                source_order[citation.source_id] = len(source_order) + 1

        replacements: Dict[str, str] = {}
        for citation in citations:
            source = await self.sources.get_by_id(citation.source_id, user_id)
            if source is None:
                continue
            rendered = format_in_text(
                citation_source_from_record(source),
                normalized_style,
                index=source_order[citation.source_id],
                locator=citation.locator,
            )
            if citation.in_text and citation.in_text != rendered:
                replacements[citation.in_text] = rendered
            await self.citations.update_style_and_text(
                citation.id, user_id, normalized_style, rendered
            )

        if replacements:
            for node, _section in _iter_text_nodes(document):
                text = node.text
                for old, new in replacements.items():
                    if old and old in text:
                        text = text.replace(old, new)
                node.text = text
            await self.documents.update(document)

        return await self.reference_list(
            document_id, user_id, normalized_style, document=document
        )


def _substitute(text: str, resolver) -> Tuple[str, int, int]:
    """Replace markers via ``resolver(index) -> (replacement|None, _unused)``."""
    replaced = 0
    removed = 0

    def _sub(match: re.Match) -> str:
        nonlocal replaced, removed
        replacement, _ = resolver(int(match.group(1)))
        if replacement is None:
            removed += 1
            return ""
        replaced += 1
        return replacement

    return MARKER_PATTERN.sub(_sub, text), replaced, removed


def document_text(document: DocumentIR) -> str:
    """Flatten a document to plain text (used for leftover-marker detection)."""
    parts: List[str] = [document.title]
    for section in document.content:
        parts.append(section.title)
        for block in section.blocks:
            if isinstance(block, Paragraph) or isinstance(block, Quote):
                parts.append("".join(run.text for run in block.content))
            elif isinstance(block, ListBlock):
                for item in block.items:
                    parts.append("".join(run.text for run in item))
            elif isinstance(block, Table):
                for row in block.rows:
                    parts.extend(row)
    return "\n".join(parts)
