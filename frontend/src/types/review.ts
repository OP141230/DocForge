// Phase 6 types: reviews, findings, edit proposals, compliance, versions.
// These mirror backend/app/models/review.py. Keeping them hand-written (rather
// than generated) is deliberate: the API is small and a mismatch shows up as a
// TypeScript error instead of a runtime surprise.

export type ReviewCategory =
  | 'grammar'
  | 'spelling'
  | 'clarity'
  | 'structure'
  | 'repetition'
  | 'tone'
  | 'terminology'
  | 'completeness'
  | 'citations'
  | 'factual';

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'suggestion';

export type FindingStatus = 'open' | 'accepted' | 'rejected' | 'resolved' | 'ignored';

export type ReviewMode = 'quick' | 'full' | 'academic' | 'technical' | 'custom';

export type ReviewStatus = 'pending' | 'running' | 'completed' | 'failed';

export type ComplianceStatus =
  | 'met'
  | 'partially_met'
  | 'not_met'
  | 'not_applicable'
  | 'needs_review';

export type VersionOrigin = 'manual' | 'ai_accepted' | 'restore' | 'import';

export interface ReviewSession {
  id: string;
  user_id: string;
  document_id: string;
  brief_id: string | null;
  mode: ReviewMode;
  categories: ReviewCategory[];
  scope: 'document' | 'section';
  section_id: string | null;
  status: ReviewStatus;
  document_fingerprint: string | null;
  provider: string | null;
  provider_message: string | null;
  error: string | null;
  progress_message: string | null;
  findings_total: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface ReviewFinding {
  id: string;
  user_id: string;
  review_id: string;
  document_id: string;
  category: ReviewCategory;
  severity: Severity;
  source: 'deterministic' | 'ai';
  title: string;
  explanation: string;
  section_id: string | null;
  section_title: string | null;
  block_id: string | null;
  original_text: string | null;
  start_offset: number | null;
  end_offset: number | null;
  suggested_text: string | null;
  status: FindingStatus;
  evidence_ids: string[];
  citation_ids: string[];
  document_fingerprint: string | null;
  is_stale: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReviewSummary {
  total: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  stale: number;
  open: number;
}

export interface ReviewReport {
  session: ReviewSession;
  findings: ReviewFinding[];
  summary: ReviewSummary;
  limitations: string[];
}

export interface ComplianceResult {
  id: string;
  requirement: string;
  status: ComplianceStatus;
  explanation: string;
  section_title: string | null;
  suggested_action: string | null;
  method: 'deterministic' | 'ai' | 'manual';
}

export interface ComplianceReport {
  document_id: string;
  brief_id: string | null;
  brief_title: string | null;
  overall: ComplianceStatus;
  results: ComplianceResult[];
  limitations: string[];
  document_fingerprint: string | null;
  generated_at: string;
}

export interface EditProposal {
  id: string;
  document_id: string;
  review_id: string | null;
  finding_id: string | null;
  operation: string;
  target_type: 'document' | 'section' | 'block';
  section_id: string | null;
  block_id: string | null;
  original_text: string;
  proposed_text: string;
  status: 'proposed' | 'accepted' | 'rejected';
  impact: {
    citations_in_scope?: string[];
    markers_removed?: string[];
    markers_added?: string[];
    citation_review_required?: boolean;
    verification_recheck_required?: boolean;
    notes?: string;
  };
  created_at: string;
}

export interface VersionEntry {
  version_number: number;
  created_at: string;
  origin: VersionOrigin;
  operation: string | null;
  summary: string | null;
  word_count: number;
}

export interface VersionComparison {
  document_id: string;
  from_version: number;
  to_version: number;
  from_title: string;
  to_title: string;
  from_word_count: number;
  to_word_count: number;
  diff: string[];
  changed_sections: string[];
}

export const CATEGORY_LABELS: Record<ReviewCategory, string> = {
  grammar: 'Grammar',
  spelling: 'Spelling',
  clarity: 'Clarity',
  structure: 'Structure',
  repetition: 'Repetition',
  tone: 'Tone',
  terminology: 'Terminology',
  completeness: 'Completeness',
  citations: 'Citations',
  factual: 'Factual accuracy',
};

export const SEVERITY_LABELS: Record<Severity, string> = {
  critical: 'Critical',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
  suggestion: 'Suggestion',
};

export const COMPLIANCE_LABELS: Record<ComplianceStatus, string> = {
  met: 'Met',
  partially_met: 'Partially Met',
  not_met: 'Not Met',
  not_applicable: 'Not Applicable',
  needs_review: 'Needs Manual Review',
};

export const MODE_LABELS: Record<ReviewMode, string> = {
  quick: 'Quick Review',
  full: 'Full Review',
  academic: 'Academic Review',
  technical: 'Technical Review',
  custom: 'Custom Review',
};

export const MODE_DESCRIPTIONS: Record<ReviewMode, string> = {
  quick: 'Grammar, spelling and clarity. Fast and cheap.',
  full: 'Every category, including structure, citations and factual accuracy.',
  academic: 'Academic tone, structure, citations and evidence.',
  technical: 'Technical clarity, terminology and completeness.',
  custom: 'Choose exactly which categories to check.',
};

export const ALL_CATEGORIES = Object.keys(CATEGORY_LABELS) as ReviewCategory[];

export const EDIT_OPERATIONS: { value: string; label: string; group: string }[] = [
  { value: 'improve_clarity', label: 'Improve clarity', group: 'Writing' },
  { value: 'fix_grammar', label: 'Fix grammar', group: 'Writing' },
  { value: 'make_concise', label: 'Make more concise', group: 'Writing' },
  { value: 'expand_explanation', label: 'Expand explanation', group: 'Writing' },
  { value: 'simplify', label: 'Simplify', group: 'Writing' },
  { value: 'improve_transitions', label: 'Improve transitions', group: 'Writing' },
  { value: 'rewrite_paragraph', label: 'Rewrite paragraph', group: 'Structure' },
  { value: 'improve_introduction', label: 'Improve introduction', group: 'Structure' },
  { value: 'improve_conclusion', label: 'Improve conclusion', group: 'Structure' },
  { value: 'to_bullets', label: 'Convert to bullet points', group: 'Structure' },
  { value: 'from_bullets', label: 'Convert bullets to paragraphs', group: 'Structure' },
  { value: 'add_examples', label: 'Add examples', group: 'Structure' },
  { value: 'summarize', label: 'Summarize', group: 'Structure' },
  { value: 'expand_section', label: 'Expand section', group: 'Structure' },
  { value: 'standardize_terminology', label: 'Standardize terminology', group: 'Consistency' },
  { value: 'normalize_tone', label: 'Normalize tone', group: 'Consistency' },
  { value: 'reduce_repetition', label: 'Reduce repetition', group: 'Consistency' },
  { value: 'align_outline', label: 'Align with outline', group: 'Consistency' },
  { value: 'align_brief', label: 'Align with brief', group: 'Consistency' },
  { value: 'tone_formal', label: 'Formal tone', group: 'Tone' },
  { value: 'tone_academic', label: 'Academic tone', group: 'Tone' },
  { value: 'tone_professional', label: 'Professional tone', group: 'Tone' },
  { value: 'tone_conversational', label: 'Conversational tone', group: 'Tone' },
  { value: 'tone_technical', label: 'Technical tone', group: 'Tone' },
  { value: 'tone_persuasive', label: 'Persuasive tone', group: 'Tone' },
];
