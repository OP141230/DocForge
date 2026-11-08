"""Phase 6 models: AI review, findings, edit proposals, compliance, versions.

Design notes
------------
* **Nothing here trusts the model.** :class:`RawFinding` is the *unvalidated*
  shape a provider returns. ``review_service`` converts it into a
  :class:`ReviewFinding` only after the quoted text has been located in the
  real document. Offsets are always computed by us, never taken from the model.
* **Findings are versioned by fingerprint.** ``document_fingerprint`` is a hash
  of the document content the finding was produced from. If the document later
  changes, the finding is surfaced as *stale* instead of being silently applied
  to unrelated text.
* **Edits are proposals.** An :class:`EditProposal` never mutates the document.
  Applying it is a separate, explicit call that creates a new version.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ReviewCategory(str, Enum):
    GRAMMAR = "grammar"
    SPELLING = "spelling"
    CLARITY = "clarity"
    STRUCTURE = "structure"
    REPETITION = "repetition"
    TONE = "tone"
    TERMINOLOGY = "terminology"
    COMPLETENESS = "completeness"
    CITATIONS = "citations"
    FACTUAL = "factual"


CATEGORY_LABELS = {
    ReviewCategory.GRAMMAR: "Grammar",
    ReviewCategory.SPELLING: "Spelling",
    ReviewCategory.CLARITY: "Clarity & Readability",
    ReviewCategory.STRUCTURE: "Structure & Organization",
    ReviewCategory.REPETITION: "Repetition",
    ReviewCategory.TONE: "Tone & Consistency",
    ReviewCategory.TERMINOLOGY: "Terminology",
    ReviewCategory.COMPLETENESS: "Completeness",
    ReviewCategory.CITATIONS: "Citations & References",
    ReviewCategory.FACTUAL: "Factual Accuracy",
}


class Severity(str, Enum):
    """Ordered from most to least urgent; ``SEVERITY_ORDER`` maps to rank."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SUGGESTION = "suggestion"


SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.SUGGESTION: 4,
}


class FindingStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class FindingSource(str, Enum):
    """Whether a finding came from code or from the model."""

    DETERMINISTIC = "deterministic"
    AI = "ai"


class ReviewMode(str, Enum):
    QUICK = "quick"
    FULL = "full"
    ACADEMIC = "academic"
    TECHNICAL = "technical"
    CUSTOM = "custom"


MODE_CATEGORIES: Dict[ReviewMode, List[ReviewCategory]] = {
    ReviewMode.QUICK: [
        ReviewCategory.GRAMMAR,
        ReviewCategory.SPELLING,
        ReviewCategory.CLARITY,
    ],
    ReviewMode.FULL: list(ReviewCategory),
    ReviewMode.ACADEMIC: [
        ReviewCategory.GRAMMAR,
        ReviewCategory.CLARITY,
        ReviewCategory.STRUCTURE,
        ReviewCategory.TONE,
        ReviewCategory.TERMINOLOGY,
        ReviewCategory.CITATIONS,
        ReviewCategory.FACTUAL,
    ],
    ReviewMode.TECHNICAL: [
        ReviewCategory.GRAMMAR,
        ReviewCategory.CLARITY,
        ReviewCategory.STRUCTURE,
        ReviewCategory.TERMINOLOGY,
        ReviewCategory.COMPLETENESS,
    ],
}


class ReviewStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewScope(str, Enum):
    DOCUMENT = "document"
    SECTION = "section"


class EditOperation(str, Enum):
    """Every operation is a prompt recipe plus a scope, not bespoke code."""

    # Writing improvements
    IMPROVE_CLARITY = "improve_clarity"
    FIX_GRAMMAR = "fix_grammar"
    MAKE_CONCISE = "make_concise"
    EXPAND_EXPLANATION = "expand_explanation"
    SIMPLIFY = "simplify"
    IMPROVE_TRANSITIONS = "improve_transitions"
    IMPROVE_PROFESSIONALISM = "improve_professionalism"
    # Tone
    TONE_FORMAL = "tone_formal"
    TONE_ACADEMIC = "tone_academic"
    TONE_PROFESSIONAL = "tone_professional"
    TONE_CONVERSATIONAL = "tone_conversational"
    TONE_TECHNICAL = "tone_technical"
    TONE_PERSUASIVE = "tone_persuasive"
    # Structure
    REWRITE_PARAGRAPH = "rewrite_paragraph"
    IMPROVE_INTRODUCTION = "improve_introduction"
    IMPROVE_CONCLUSION = "improve_conclusion"
    REORGANIZE_SECTION = "reorganize_section"
    TO_BULLETS = "to_bullets"
    FROM_BULLETS = "from_bullets"
    ADD_EXAMPLES = "add_examples"
    SUMMARIZE = "summarize"
    EXPAND_SECTION = "expand_section"
    # Consistency
    STANDARDIZE_TERMINOLOGY = "standardize_terminology"
    NORMALIZE_TONE = "normalize_tone"
    REDUCE_REPETITION = "reduce_repetition"
    ALIGN_OUTLINE = "align_outline"
    ALIGN_BRIEF = "align_brief"


OPERATION_LABELS = {
    EditOperation.IMPROVE_CLARITY: "Improve clarity",
    EditOperation.FIX_GRAMMAR: "Fix grammar",
    EditOperation.MAKE_CONCISE: "Make more concise",
    EditOperation.EXPAND_EXPLANATION: "Expand explanation",
    EditOperation.SIMPLIFY: "Simplify",
    EditOperation.IMPROVE_TRANSITIONS: "Improve transitions",
    EditOperation.IMPROVE_PROFESSIONALISM: "Improve professionalism",
    EditOperation.TONE_FORMAL: "Rewrite in a formal tone",
    EditOperation.TONE_ACADEMIC: "Rewrite in an academic tone",
    EditOperation.TONE_PROFESSIONAL: "Rewrite in a professional tone",
    EditOperation.TONE_CONVERSATIONAL: "Rewrite in a conversational tone",
    EditOperation.TONE_TECHNICAL: "Rewrite in a technical tone",
    EditOperation.TONE_PERSUASIVE: "Rewrite in a persuasive tone",
    EditOperation.REWRITE_PARAGRAPH: "Rewrite paragraph",
    EditOperation.IMPROVE_INTRODUCTION: "Improve introduction",
    EditOperation.IMPROVE_CONCLUSION: "Improve conclusion",
    EditOperation.REORGANIZE_SECTION: "Reorganize section",
    EditOperation.TO_BULLETS: "Convert to bullet points",
    EditOperation.FROM_BULLETS: "Convert to paragraphs",
    EditOperation.ADD_EXAMPLES: "Add examples",
    EditOperation.SUMMARIZE: "Summarize",
    EditOperation.EXPAND_SECTION: "Expand",
    EditOperation.STANDARDIZE_TERMINOLOGY: "Standardize terminology",
    EditOperation.NORMALIZE_TONE: "Normalize tone",
    EditOperation.REDUCE_REPETITION: "Reduce repetition",
    EditOperation.ALIGN_OUTLINE: "Align with outline",
    EditOperation.ALIGN_BRIEF: "Align with brief requirements",
}


class ProposalStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ComplianceStatus(str, Enum):
    MET = "met"
    PARTIALLY_MET = "partially_met"
    NOT_MET = "not_met"
    NOT_APPLICABLE = "not_applicable"
    NEEDS_REVIEW = "needs_review"


COMPLIANCE_LABELS = {
    ComplianceStatus.MET: "Met",
    ComplianceStatus.PARTIALLY_MET: "Partially Met",
    ComplianceStatus.NOT_MET: "Not Met",
    ComplianceStatus.NOT_APPLICABLE: "Not Applicable",
    ComplianceStatus.NEEDS_REVIEW: "Needs Manual Review",
}


class VersionOrigin(str, Enum):
    MANUAL = "manual"
    AI_ACCEPTED = "ai_accepted"
    RESTORE = "restore"
    IMPORT = "import"


# ---------------------------------------------------------------------------
# Stored records
# ---------------------------------------------------------------------------

class ReviewSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    document_id: str
    brief_id: Optional[str] = None

    mode: ReviewMode = ReviewMode.QUICK
    categories: List[ReviewCategory] = Field(default_factory=list)
    scope: ReviewScope = ReviewScope.DOCUMENT
    section_id: Optional[str] = None

    status: ReviewStatus = ReviewStatus.PENDING
    document_fingerprint: Optional[str] = None
    provider: Optional[str] = None
    provider_message: Optional[str] = None
    error: Optional[str] = None
    progress_message: Optional[str] = None

    findings_total: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ReviewFinding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    review_id: str
    document_id: str

    category: ReviewCategory
    severity: Severity
    source: FindingSource = FindingSource.AI
    title: str
    explanation: str

    # Anchors. ``block_id``/``section_id`` come from the DocumentIR so they are
    # stable across edits; offsets are relative to the block's own text.
    section_id: Optional[str] = None
    section_title: Optional[str] = None
    block_id: Optional[str] = None
    original_text: Optional[str] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None

    suggested_text: Optional[str] = None
    status: FindingStatus = FindingStatus.OPEN

    evidence_ids: List[str] = Field(default_factory=list)
    citation_ids: List[str] = Field(default_factory=list)

    document_fingerprint: Optional[str] = None
    # Filled on read, never stored: True when the document changed since review.
    is_stale: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EditProposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    document_id: str
    review_id: Optional[str] = None
    finding_id: Optional[str] = None

    operation: EditOperation
    target_type: str = "section"          # document | section | block
    section_id: Optional[str] = None
    block_id: Optional[str] = None

    original_text: str
    proposed_text: str
    status: ProposalStatus = ProposalStatus.PROPOSED

    base_fingerprint: Optional[str] = None
    provider: Optional[str] = None
    notes: Optional[str] = None
    # JSON-serialized impact analysis (citations/verifications to recheck).
    impact: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentVersionNote(BaseModel):
    document_id: str
    version_number: int
    user_id: str
    origin: VersionOrigin = VersionOrigin.MANUAL
    operation: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    requirement: str
    status: ComplianceStatus
    explanation: str = ""
    section_title: Optional[str] = None
    suggested_action: Optional[str] = None
    method: str = "deterministic"   # deterministic | ai | manual


class ComplianceReport(BaseModel):
    document_id: str
    brief_id: Optional[str] = None
    brief_title: Optional[str] = None
    overall: ComplianceStatus = ComplianceStatus.NEEDS_REVIEW
    results: List[ComplianceResult] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    document_fingerprint: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Aggregates returned to the client
# ---------------------------------------------------------------------------

class ReviewSummary(BaseModel):
    total: int = 0
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_category: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)
    stale: int = 0
    open: int = 0


class ReviewReport(BaseModel):
    session: ReviewSession
    findings: List[ReviewFinding] = Field(default_factory=list)
    summary: ReviewSummary = Field(default_factory=ReviewSummary)
    limitations: List[str] = Field(default_factory=list)


class VersionComparison(BaseModel):
    document_id: str
    from_version: int
    to_version: int
    from_title: str
    to_title: str
    from_word_count: int
    to_word_count: int
    # Line-oriented unified diff of the flattened text; easy to render and
    # independent of the editor implementation.
    diff: List[str] = Field(default_factory=list)
    changed_sections: List[str] = Field(default_factory=list)


class VersionEntry(BaseModel):
    version_number: int
    created_at: datetime
    origin: VersionOrigin = VersionOrigin.MANUAL
    operation: Optional[str] = None
    summary: Optional[str] = None
    word_count: int = 0


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class StartReviewRequest(BaseModel):
    mode: ReviewMode = ReviewMode.FULL
    categories: Optional[List[ReviewCategory]] = None
    scope: ReviewScope = ReviewScope.DOCUMENT
    section_id: Optional[str] = None
    # Opt out of the model entirely (deterministic checks only).
    use_ai: bool = True


class UpdateFindingRequest(BaseModel):
    status: FindingStatus


class ProposeEditRequest(BaseModel):
    operation: EditOperation
    target_type: str = "section"
    section_id: Optional[str] = None
    block_id: Optional[str] = None
    # Free-text instruction for CUSTOM-style rewrites.
    instruction: Optional[str] = Field(default=None, max_length=2000)


class ApplyProposalRequest(BaseModel):
    # Optimistic concurrency: the fingerprint the client saw when it accepted.
    expected_fingerprint: Optional[str] = None


class CompareVersionsRequest(BaseModel):
    from_version: int
    to_version: int


# ---------------------------------------------------------------------------
# Untrusted provider output (validated before use)
# ---------------------------------------------------------------------------

class RawFinding(BaseModel):
    """What a provider is allowed to return. Deliberately loose + bounded."""

    category: str
    severity: str = "medium"
    title: str = ""
    explanation: str = ""
    original_text: str = ""
    suggested_text: Optional[str] = None
    section_title: Optional[str] = None


class RawReviewResponse(BaseModel):
    findings: List[RawFinding] = Field(default_factory=list)


class RawComplianceResult(BaseModel):
    requirement: str
    status: str = "needs_review"
    explanation: str = ""
    suggested_action: Optional[str] = None


class RawComplianceResponse(BaseModel):
    results: List[RawComplianceResult] = Field(default_factory=list)


__all__ = [
    "ReviewCategory",
    "CATEGORY_LABELS",
    "Severity",
    "SEVERITY_ORDER",
    "FindingStatus",
    "FindingSource",
    "ReviewMode",
    "MODE_CATEGORIES",
    "ReviewStatus",
    "ReviewScope",
    "EditOperation",
    "OPERATION_LABELS",
    "ProposalStatus",
    "ComplianceStatus",
    "COMPLIANCE_LABELS",
    "VersionOrigin",
    "ReviewSession",
    "ReviewFinding",
    "EditProposal",
    "DocumentVersionNote",
    "ComplianceResult",
    "ComplianceReport",
    "ReviewSummary",
    "ReviewReport",
    "VersionComparison",
    "VersionEntry",
    "StartReviewRequest",
    "UpdateFindingRequest",
    "ProposeEditRequest",
    "ApplyProposalRequest",
    "CompareVersionsRequest",
    "RawFinding",
    "RawReviewResponse",
    "RawComplianceResult",
    "RawComplianceResponse",
]
