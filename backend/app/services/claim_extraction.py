"""Deterministic factual-claim extraction from a Document IR.

Why deterministic instead of "ask the LLM to list claims"?
----------------------------------------------------------
Extraction must be reproducible, cheap, and auditable: the same document has to
produce the same claim IDs on every run so that a re-check updates an existing
finding instead of creating a duplicate. A regex/heuristic pass also makes the
*shape* of the data obvious (claim id, section, time-sensitivity) before any
model is involved.

The heuristics are intentionally conservative. Sentences that are clearly
opinions, recommendations, predictions or questions are **not** treated as
factual claims; they are counted and reported as skipped. Claim detection is
imperfect by nature - which is exactly why verification statuses include
"Insufficient Evidence" and findings carry a method label.

Limitation: sentence splitting is regex based and does not understand
abbreviations ("Dr.", "e.g."), so a small number of sentences may be split
awkwardly. Claims are limited to paragraph and list content; headings, quotes,
code and table cells are not treated as claims.
"""
import hashlib
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from app.models.document_ir import DocumentIR, InlineContent, ListBlock, Paragraph

MAX_CLAIM_CHARS = 400
MIN_CLAIM_WORDS = 5

OPINION_MARKERS = (
    "i think", "i believe", "in my opinion", "arguably", "it seems",
    "personally", "we feel", "unfortunately", "interestingly", "beautiful",
    "amazing", "terrible", "the best", "the worst", "clearly the",
)
RECOMMENDATION_MARKERS = (
    "should", "must ", "recommend", "we suggest", "consider ", "ought to",
    "it is advisable", "best practice is", "need to ",
)
PREDICTION_MARKERS = (
    "will ", "expected to", "likely to", "forecast", "projected",
    "is going to", "in the future", "by 20",
)
TIME_SENSITIVE_MARKERS = (
    "currently", "today", "nowadays", "recently", "latest", "this year",
    "last year", "as of", "at present", "right now", "so far",
)

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


@dataclass
class ExtractedClaim:
    """One candidate factual claim."""

    claim_id: str
    text: str
    section_id: Optional[str]
    section_title: Optional[str]
    time_sensitive: bool
    kind: str  # factual (only these are returned)


@dataclass
class SkippedSentence:
    """A sentence that was deliberately not treated as a factual claim."""

    text: str
    kind: str
    section_title: Optional[str]


@dataclass
class ClaimExtractionResult:
    """Claims plus a transparent account of what was skipped."""

    claims: List[ExtractedClaim]
    skipped: List[SkippedSentence]

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)


def _block_texts(blocks: Iterable) -> Iterable[str]:
    """Yield the plain text of content-bearing blocks."""
    for block in blocks:
        if isinstance(block, Paragraph):
            text = "".join(run.text for run in block.content)
            if text.strip():
                yield text
        elif isinstance(block, ListBlock):
            for item in block.items:
                text = "".join(run.text for run in item)
                if text.strip():
                    yield text


def _normalize(text: str) -> str:
    return " ".join(text.split())


def classify_sentence(sentence: str) -> str:
    """Classify a sentence as factual/opinion/recommendation/prediction/question."""
    lowered = sentence.lower().strip()

    if lowered.endswith("?"):
        return "question"
    if any(marker in lowered for marker in OPINION_MARKERS):
        return "opinion"
    if any(marker in lowered for marker in RECOMMENDATION_MARKERS):
        return "recommendation"
    if any(marker in lowered for marker in PREDICTION_MARKERS):
        return "prediction"
    if lowered.startswith(("i ", "we ", "my ", "our ")) and " is " not in lowered:
        return "subjective"
    return "factual"


def is_time_sensitive(sentence: str) -> bool:
    """Flag claims whose truth may change over time."""
    lowered = sentence.lower()
    if re.search(r"\b(1[89]\d{2}|20\d{2})\b", sentence):
        return True
    return any(marker in lowered for marker in TIME_SENSITIVE_MARKERS)


def make_claim_id(text: str, section_title: Optional[str]) -> str:
    """Stable id so re-checks update instead of duplicating findings."""
    payload = f"{_normalize(text).lower()}|{(section_title or '').strip().lower()}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def extract_claims(
    document: DocumentIR,
    section_titles: Optional[List[str]] = None,
) -> ClaimExtractionResult:
    """Extract factual claims from a document.

    Args:
        document: The document to scan.
        section_titles: Optional allow-list of section titles to scan.
    """
    claims: List[ExtractedClaim] = []
    skipped: List[SkippedSentence] = []
    seen_ids: set[str] = set()
    wanted = {title.strip().lower() for title in section_titles} if section_titles else None

    for section in document.content:
        if wanted is not None and (section.title or "").lower() not in wanted:
            continue

        for block_text in _block_texts(section.blocks):
            for raw_sentence in SENTENCE_SPLIT.split(block_text):
                sentence = _normalize(raw_sentence).strip("-•* \t")
                if not sentence:
                    continue

                words = sentence.split()
                if len(words) < MIN_CLAIM_WORDS:
                    skipped.append(SkippedSentence(sentence, "too_short", section.title))
                    continue
                if len(sentence) > MAX_CLAIM_CHARS:
                    skipped.append(SkippedSentence(sentence[:MAX_CLAIM_CHARS], "too_long", section.title))
                    continue

                kind = classify_sentence(sentence)
                if kind != "factual":
                    skipped.append(SkippedSentence(sentence, kind, section.title))
                    continue

                claim_id = make_claim_id(sentence, section.title)
                if claim_id in seen_ids:
                    continue
                seen_ids.add(claim_id)

                claims.append(
                    ExtractedClaim(
                        claim_id=claim_id,
                        text=sentence,
                        section_id=section.id,
                        section_title=section.title,
                        time_sensitive=is_time_sensitive(sentence),
                        kind=kind,
                    )
                )

    return ClaimExtractionResult(claims=claims, skipped=skipped)


def split_passages_for_claim(text: str, limit: int = 3) -> List[str]:
    """Helper used by the verifier to find the most relevant passage sentences."""
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    return sentences[:limit]


def document_text(document: DocumentIR) -> str:
    """Flatten a document to plain text (used for quick keyword checks)."""
    chunks: List[str] = [document.title]
    for section in document.content:
        chunks.append(section.title)
        chunks.extend(_block_texts(section.blocks))
    return "\n".join(chunks)


def iterative_runs(blocks: Iterable) -> Iterable[Tuple[str, InlineContent]]:
    """Expose inline runs so other services can rewrite citation markers."""
    for block in blocks:
        if isinstance(block, Paragraph):
            for run in block.content:
                yield "paragraph", run
        elif isinstance(block, ListBlock):
            for item in block.items:
                for run in item:
                    yield "list", run
