"""Phase 5 models: research sessions, sources, evidence, citations, verification.

Design notes
------------
Every record in this module is *owned*. The owner (``user_id``) is never taken
from a request body - it always comes from the authenticated session in the API
layer (see :mod:`app.api.routes.research`).

The models are deliberately explicit about what is *unknown*. Anything that we
could not verify (author, publication date, page number, DOI) stays ``None``
instead of being guessed, so the citation formatters and the UI can state a
limitation rather than invent metadata.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ResearchStatus(str, Enum):
    """Lifecycle of a research session."""

    DRAFT = "draft"
    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"      # finished, but at least one source/question failed
    FAILED = "failed"


class SourceType(str, Enum):
    """Where a source came from."""

    WEB = "web"
    KNOWLEDGE_BASE = "knowledge_base"
    USER_URL = "user_url"


class RetrievalStatus(str, Enum):
    """How far we got with a source."""

    DISCOVERED = "discovered"    # search result, not fetched yet
    FETCHED = "fetched"          # content retrieved successfully
    FAILED = "failed"            # network/parse error
    BLOCKED = "blocked"          # rejected by URL safety checks
    UNSUPPORTED = "unsupported"  # content type we cannot read


class EvidenceType(str, Enum):
    """Kind of evidence passage."""

    SUPPORTING = "supporting"
    CONTRADICTING = "contradicting"
    CONTEXT = "context"
    QUOTATION = "quotation"


class CitationStyle(str, Enum):
    """Supported citation styles (see app/services/citations.py)."""

    APA = "apa"
    IEEE = "ieee"
    MLA = "mla"
    CHICAGO = "chicago"


class VerificationStatus(str, Enum):
    """Exact conceptual statuses required by the Phase 5 specification."""

    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NOT_CHECKED = "not_checked"


VERIFICATION_STATUS_LABELS = {
    VerificationStatus.SUPPORTED: "Supported",
    VerificationStatus.CONTRADICTED: "Contradicted",
    VerificationStatus.INSUFFICIENT_EVIDENCE: "Insufficient Evidence",
    VerificationStatus.NOT_CHECKED: "Not Checked",
}


# ---------------------------------------------------------------------------
# Core records
# ---------------------------------------------------------------------------

class ResearchQuestion(BaseModel):
    """A single research question belonging to a session."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    question: str
    rationale: Optional[str] = None
    order_index: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchSession(BaseModel):
    """A research session bound to a brief and/or a document."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    brief_id: Optional[str] = None
    document_id: Optional[str] = None
    title: str
    status: ResearchStatus = ResearchStatus.DRAFT

    external_research: bool = False
    include_knowledge_base: bool = True
    citation_style: CitationStyle = CitationStyle.APA
    requested_urls: List[str] = Field(default_factory=list)
    knowledge_file_ids: List[str] = Field(default_factory=list)

    provider: Optional[str] = None          # provider actually used
    provider_message: Optional[str] = None  # e.g. "no provider configured"
    error: Optional[str] = None
    progress_message: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ResearchSource(BaseModel):
    """A retrieved (or attempted) source."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    user_id: str
    research_question_id: Optional[str] = None

    source_type: SourceType = SourceType.WEB
    retrieval_status: RetrievalStatus = RetrievalStatus.DISCOVERED

    title: str
    url: Optional[str] = None
    canonical_url: Optional[str] = None
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    accessed_at: Optional[datetime] = None

    content_text: Optional[str] = None
    excerpt: Optional[str] = None
    word_count: int = 0
    http_status: Optional[int] = None
    error: Optional[str] = None

    # Transparent, explainable evaluation - not an "objective truth" score.
    source_type_label: str = "unknown"   # peer_reviewed / official / news / blog ...
    evaluation_notes: List[str] = Field(default_factory=list)
    relevance_score: Optional[float] = None

    # Phase 4 linkage
    knowledge_file_id: Optional[str] = None
    chunk_id: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None

    selected: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceRecord(BaseModel):
    """A traceable passage tied to a source and a research question."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    source_id: str
    user_id: str
    research_question_id: Optional[str] = None

    claim_or_finding: str
    passage: str
    evidence_type: EvidenceType = EvidenceType.CONTEXT

    url: Optional[str] = None
    knowledge_file_id: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None

    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    user_selected: bool = True
    notes: Optional[str] = None


class CitationRecord(BaseModel):
    """A citation used inside a document, linked to a real source record."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    document_id: str
    source_id: str
    research_session_id: Optional[str] = None
    evidence_id: Optional[str] = None

    section_id: Optional[str] = None
    section_title: Optional[str] = None
    marker: Optional[str] = None        # original [S1] marker
    locator: Optional[str] = None       # page / section used in the citation
    style: CitationStyle = CitationStyle.APA
    in_text: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClaimVerification(BaseModel):
    """A verification finding for one claim in a document."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    document_id: str
    research_session_id: Optional[str] = None

    claim_id: str
    claim_text: str
    section_id: Optional[str] = None
    section_title: Optional[str] = None

    status: VerificationStatus = VerificationStatus.NOT_CHECKED
    explanation: Optional[str] = None
    verification_method: str = "deterministic"
    time_sensitive: bool = False
    manual_review: bool = False

    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)

    checked_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# API request models
# ---------------------------------------------------------------------------

class CreateResearchSessionRequest(BaseModel):
    """Create a research session."""

    brief_id: Optional[str] = None
    document_id: Optional[str] = None
    title: Optional[str] = None
    external_research: bool = False
    include_knowledge_base: bool = True
    citation_style: CitationStyle = CitationStyle.APA
    knowledge_file_ids: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)


class UpdateResearchSessionRequest(BaseModel):
    """Update research settings before a run."""

    title: Optional[str] = None
    external_research: Optional[bool] = None
    include_knowledge_base: Optional[bool] = None
    citation_style: Optional[CitationStyle] = None
    knowledge_file_ids: Optional[List[str]] = None
    urls: Optional[List[str]] = None


class ResearchQuestionInput(BaseModel):
    """A research question supplied by the user."""

    question: str = Field(min_length=3, max_length=500)
    rationale: Optional[str] = Field(default=None, max_length=1000)


class UpdateQuestionsRequest(BaseModel):
    """Replace the ordered list of research questions."""

    questions: List[ResearchQuestionInput]


class UpdateSourceRequest(BaseModel):
    """Select or exclude a source."""

    selected: bool


class CreateEvidenceRequest(BaseModel):
    """Attach a manual evidence passage to a source."""

    source_id: str
    passage: str = Field(min_length=1, max_length=20000)
    claim_or_finding: str = Field(min_length=1, max_length=2000)
    research_question_id: Optional[str] = None
    evidence_type: EvidenceType = EvidenceType.CONTEXT


class UpdateEvidenceRequest(BaseModel):
    """Change evidence selection/type."""

    user_selected: Optional[bool] = None
    evidence_type: Optional[EvidenceType] = None
    notes: Optional[str] = None


class GenerateFromBriefRequest(BaseModel):
    """Optional body for brief generation, enabling research-backed output."""

    research_session_id: Optional[str] = None
    citation_style: Optional[CitationStyle] = None
    use_research: bool = True


class VerifyDocumentRequest(BaseModel):
    """Start a verification pass for a document."""

    research_session_id: Optional[str] = None
    max_claims: Optional[int] = Field(default=None, ge=1, le=200)
    section_titles: Optional[List[str]] = None


class UpdateVerificationRequest(BaseModel):
    """User actions on a finding."""

    manual_review: Optional[bool] = None


class ChangeCitationStyleRequest(BaseModel):
    """Re-render a document's citations in another style."""

    style: CitationStyle


# ---------------------------------------------------------------------------
# API response models
# ---------------------------------------------------------------------------

class CitationIssue(BaseModel):
    """A citation-integrity problem. Formatting correct != citation valid."""

    code: str
    severity: str  # "error" | "warning"
    message: str
    citation_id: Optional[str] = None
    source_id: Optional[str] = None


class ReferenceEntry(BaseModel):
    """One rendered reference-list entry."""

    citation_id: str
    source_id: str
    index: int
    text: str


class ReferenceListResponse(BaseModel):
    """Formatted reference list plus integrity findings."""

    document_id: str
    style: CitationStyle
    entries: List[ReferenceEntry]
    issues: List[CitationIssue]
    uncited_source_ids: List[str] = Field(default_factory=list)


class VerificationSummary(BaseModel):
    """Aggregate counts by status."""

    supported: int = 0
    contradicted: int = 0
    insufficient_evidence: int = 0
    not_checked: int = 0
    total: int = 0
    time_sensitive: int = 0


class VerificationReport(BaseModel):
    """Everything the verification workspace needs for one document."""

    document_id: str
    research_session_id: Optional[str] = None
    summary: VerificationSummary
    findings: List[ClaimVerification]
    limitations: List[str] = Field(default_factory=list)


class ResearchSessionDetail(BaseModel):
    """Session plus its questions and counters."""

    session: ResearchSession
    questions: List[ResearchQuestion]
    source_counts: Dict[str, int] = Field(default_factory=dict)
    evidence_count: int = 0


class ResearchRunResponse(BaseModel):
    """Returned when a run is accepted or already running."""

    session_id: str
    status: ResearchStatus
    message: str


class SourcePassage(BaseModel):
    """Extracted passage returned for inspection."""

    text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None


# Re-exported for convenience in route modules.
ResearchUrl = HttpUrl

__all__ = [
    "ResearchStatus",
    "SourceType",
    "RetrievalStatus",
    "EvidenceType",
    "CitationStyle",
    "VerificationStatus",
    "VERIFICATION_STATUS_LABELS",
    "ResearchQuestion",
    "ResearchSession",
    "ResearchSource",
    "EvidenceRecord",
    "CitationRecord",
    "ClaimVerification",
    "CreateResearchSessionRequest",
    "UpdateResearchSessionRequest",
    "ResearchQuestionInput",
    "UpdateQuestionsRequest",
    "UpdateSourceRequest",
    "CreateEvidenceRequest",
    "UpdateEvidenceRequest",
    "GenerateFromBriefRequest",
    "VerifyDocumentRequest",
    "UpdateVerificationRequest",
    "ChangeCitationStyleRequest",
    "CitationIssue",
    "ReferenceEntry",
    "ReferenceListResponse",
    "VerificationSummary",
    "VerificationReport",
    "ResearchSessionDetail",
    "ResearchRunResponse",
    "SourcePassage",
]
