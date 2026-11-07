// Phase 5: Research, Citations, and Verification Types
// Mirror backend Pydantic models for type safety

export enum ResearchStatus {
  DRAFT = 'draft',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum SourceType {
  WIKIPEDIA = 'wikipedia',
  ARXIV = 'arxiv',
  PUBMED = 'pubmed',
  GOOGLE_SCHOLAR = 'google_scholar',
  WEB_SEARCH = 'web_search',
  USER_PROVIDED_URL = 'user_provided_url',
  KNOWLEDGE_BASE = 'knowledge_base',
}

export enum EvidenceType {
  DIRECT_QUOTE = 'direct_quote',
  PARAPHRASE = 'paraphrase',
  DATA = 'data',
  EXPERT_OPINION = 'expert_opinion',
  BACKGROUND = 'background',
}

export enum VerificationStatus {
  SUPPORTED = 'supported',
  CONTRADICTED = 'contradicted',
  INSUFFICIENT_EVIDENCE = 'insufficient_evidence',
  NOT_CHECKED = 'not_checked',
}

export enum CitationStyle {
  APA = 'apa',
  IEEE = 'ieee',
  MLA = 'mla',
  CHICAGO = 'chicago',
}

// Research Session
export interface ResearchSession {
  id: string;
  user_id: string;
  brief_id?: string | null;
  document_id?: string | null;
  title: string;
  external_research: boolean;
  include_knowledge_base: boolean;
  citation_style: CitationStyle;
  requested_urls: string[];
  knowledge_file_ids: string[];
  status: ResearchStatus;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchQuestion {
  id: string;
  session_id: string;
  user_id: string;
  question_text: string;
  order_index: number;
  created_at: string;
}

export interface ResearchSource {
  id: string;
  session_id: string;
  user_id: string;
  research_question_id?: string | null;
  source_type: SourceType;
  title: string;
  url?: string | null;
  knowledge_file_id?: string | null;
  page_number?: number | null;
  section_title?: string | null;
  authors?: string[] | null;
  publication_date?: string | null;
  publisher?: string | null;
  abstract_or_summary?: string | null;
  selected: boolean;
  created_at: string;
}

export interface EvidenceRecord {
  id: string;
  session_id: string;
  source_id: string;
  user_id: string;
  research_question_id?: string | null;
  claim_or_finding: string;
  passage: string;
  evidence_type: EvidenceType;
  url?: string | null;
  knowledge_file_id?: string | null;
  page_number?: number | null;
  section_title?: string | null;
  selected: boolean;
  created_at: string;
}

export interface SourceCount {
  source_type: SourceType;
  count: number;
}

export interface ResearchSessionDetail {
  session: ResearchSession;
  questions: ResearchQuestion[];
  source_counts: SourceCount[];
  evidence_count: number;
}

// Citations
export interface Citation {
  id: string;
  document_id: string;
  user_id: string;
  research_session_id?: string | null;
  research_source_id?: string | null;
  citation_key: string;
  in_text_format: string;
  reference_entry: string;
  section_id?: string | null;
  block_id?: string | null;
  created_at: string;
}

export interface CitationIntegrityFinding {
  type: 'unused' | 'missing_source' | 'duplicate_key';
  citation_id?: string | null;
  citation_key?: string | null;
  message: string;
}

export interface ReferenceListResponse {
  document_id: string;
  citation_style: CitationStyle;
  citations: Citation[];
  reference_list: string[];
  integrity_findings: CitationIntegrityFinding[];
}

// Verification
export interface ClaimVerification {
  id: string;
  document_id: string;
  user_id: string;
  research_session_id?: string | null;
  section_id?: string | null;
  block_id?: string | null;
  claim_text: string;
  verification_status: VerificationStatus;
  confidence_score: number;
  explanation: string;
  flagged_for_review: boolean;
  reviewed: boolean;
  reviewer_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface VerificationEvidence {
  id: string;
  verification_id: string;
  evidence_id: string;
  relevance_score: number;
  supporting: boolean;
}

export interface VerificationReport {
  document_id: string;
  total_claims: number;
  supported: number;
  contradicted: number;
  insufficient_evidence: number;
  not_checked: number;
  verifications: ClaimVerification[];
}

// API Request/Response types
export interface CreateResearchSessionRequest {
  title?: string | null;
  brief_id?: string | null;
  document_id?: string | null;
  external_research?: boolean;
  include_knowledge_base?: boolean;
  citation_style?: CitationStyle;
  urls?: string[];
  knowledge_file_ids?: string[];
}

export interface UpdateResearchSessionRequest {
  title?: string;
  external_research?: boolean;
  include_knowledge_base?: boolean;
  citation_style?: CitationStyle;
  urls?: string[];
  knowledge_file_ids?: string[];
}

export interface UpdateQuestionsRequest {
  questions: Array<{ question_text: string }>;
}

export interface ResearchRunResponse {
  session_id: string;
  status: ResearchStatus;
  message: string;
}

export interface CreateEvidenceRequest {
  source_id: string;
  research_question_id?: string | null;
  claim_or_finding: string;
  passage: string;
  evidence_type: EvidenceType;
}

export interface UpdateEvidenceRequest {
  claim_or_finding?: string;
  passage?: string;
  evidence_type?: EvidenceType;
  selected?: boolean;
}

export interface UpdateSourceRequest {
  selected: boolean;
}

export interface VerifyDocumentRequest {
  research_session_id?: string | null;
  max_claims?: number | null;
  section_titles?: string[] | null;
}

export interface ChangeCitationStyleRequest {
  style: CitationStyle;
}

export interface UpdateVerificationRequest {
  flagged_for_review?: boolean;
  reviewed?: boolean;
  reviewer_notes?: string | null;
}

export interface ProviderStatus {
  wikipedia: boolean;
  arxiv: boolean;
  pubmed: boolean;
  google_scholar: boolean;
  web_search: boolean;
}

export interface ResearchProviderInfo {
  provider: ProviderStatus;
  supported_styles: string[];
  limits: {
    max_questions: number;
    results_per_question: number;
    max_sources: number;
    max_user_urls: number;
    max_page_bytes: number;
    verification_max_claims: number;
  };
}

// UI Helper Labels
export const RESEARCH_STATUS_LABELS: Record<ResearchStatus, string> = {
  [ResearchStatus.DRAFT]: 'Draft',
  [ResearchStatus.RUNNING]: 'Running',
  [ResearchStatus.COMPLETED]: 'Completed',
  [ResearchStatus.FAILED]: 'Failed',
};

export const SOURCE_TYPE_LABELS: Record<SourceType, string> = {
  [SourceType.WIKIPEDIA]: 'Wikipedia',
  [SourceType.ARXIV]: 'arXiv',
  [SourceType.PUBMED]: 'PubMed',
  [SourceType.GOOGLE_SCHOLAR]: 'Google Scholar',
  [SourceType.WEB_SEARCH]: 'Web Search',
  [SourceType.USER_PROVIDED_URL]: 'User URL',
  [SourceType.KNOWLEDGE_BASE]: 'Knowledge Base',
};

export const EVIDENCE_TYPE_LABELS: Record<EvidenceType, string> = {
  [EvidenceType.DIRECT_QUOTE]: 'Direct Quote',
  [EvidenceType.PARAPHRASE]: 'Paraphrase',
  [EvidenceType.DATA]: 'Data',
  [EvidenceType.EXPERT_OPINION]: 'Expert Opinion',
  [EvidenceType.BACKGROUND]: 'Background',
};

export const VERIFICATION_STATUS_LABELS: Record<VerificationStatus, string> = {
  [VerificationStatus.SUPPORTED]: 'Supported',
  [VerificationStatus.CONTRADICTED]: 'Contradicted',
  [VerificationStatus.INSUFFICIENT_EVIDENCE]: 'Insufficient Evidence',
  [VerificationStatus.NOT_CHECKED]: 'Not Checked',
};

export const CITATION_STYLE_LABELS: Record<CitationStyle, string> = {
  [CitationStyle.APA]: 'APA',
  [CitationStyle.IEEE]: 'IEEE',
  [CitationStyle.MLA]: 'MLA',
  [CitationStyle.CHICAGO]: 'Chicago',
};

export const VERIFICATION_STATUS_COLORS: Record<VerificationStatus, string> = {
  [VerificationStatus.SUPPORTED]: 'bg-green-100 text-green-800 border-green-300',
  [VerificationStatus.CONTRADICTED]: 'bg-red-100 text-red-800 border-red-300',
  [VerificationStatus.INSUFFICIENT_EVIDENCE]: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  [VerificationStatus.NOT_CHECKED]: 'bg-gray-100 text-gray-800 border-gray-300',
};
