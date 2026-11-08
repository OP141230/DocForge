import type {
  ComplianceReport,
  EditProposal,
  ReviewFinding,
  ReviewReport,
  VersionEntry,
} from '../types/review'

export function makeFinding(overrides: Partial<ReviewFinding> = {}): ReviewFinding {
  return {
    id: 'finding-1',
    user_id: 'user-1',
    review_id: 'review-1',
    document_id: 'doc-1',
    category: 'grammar',
    severity: 'medium',
    source: 'deterministic',
    title: 'Passive voice in a key sentence',
    explanation: 'Consider naming the actor: "The auditor reviews the policy".',
    section_id: 'section-1',
    section_title: 'Introduction',
    block_id: 'block-1',
    original_text: 'The policy is reviewed by the auditor.',
    start_offset: 0,
    end_offset: 39,
    suggested_text: 'The auditor reviews the policy.',
    status: 'open',
    evidence_ids: [],
    citation_ids: [],
    document_fingerprint: 'abc',
    is_stale: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

export function makeReport(findings: ReviewFinding[]): ReviewReport {
  const bySeverity: Record<string, number> = {}
  const byCategory: Record<string, number> = {}
  const byStatus: Record<string, number> = {}
  for (const finding of findings) {
    bySeverity[finding.severity] = (bySeverity[finding.severity] ?? 0) + 1
    byCategory[finding.category] = (byCategory[finding.category] ?? 0) + 1
    byStatus[finding.status] = (byStatus[finding.status] ?? 0) + 1
  }
  return {
    session: {
      id: 'review-1',
      user_id: 'user-1',
      document_id: 'doc-1',
      brief_id: null,
      mode: 'full',
      categories: [],
      scope: 'document',
      section_id: null,
      status: 'completed',
      document_fingerprint: 'abc',
      provider: 'mock',
      provider_message: null,
      error: null,
      progress_message: null,
      findings_total: findings.length,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      completed_at: '2026-01-01T00:00:00Z',
    },
    findings,
    summary: {
      total: findings.length,
      by_severity: bySeverity,
      by_category: byCategory,
      by_status: byStatus,
      stale: findings.filter((finding) => finding.is_stale).length,
      open: findings.filter((finding) => finding.status === 'open').length,
    },
    limitations: ['AI findings are suggestions, not facts.'],
  }
}

export function makeProposal(overrides: Partial<EditProposal> = {}): EditProposal {
  return {
    id: 'proposal-1',
    document_id: 'doc-1',
    review_id: null,
    finding_id: null,
    operation: 'improve_clarity',
    target_type: 'section',
    section_id: 'section-1',
    block_id: null,
    original_text: 'The policy is reviewed by the auditor.',
    proposed_text: 'The auditor reviews the policy.',
    status: 'proposed',
    impact: {},
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

export function makeCompliance(overrides: Partial<ComplianceReport> = {}): ComplianceReport {
  return {
    document_id: 'doc-1',
    brief_id: 'brief-1',
    brief_title: 'Security audit report',
    overall: 'partially_met',
    results: [
      {
        id: 'row-1',
        requirement: 'Word count between 500 and 1200',
        status: 'met',
        explanation: 'The document contains 840 words.',
        section_title: null,
        suggested_action: null,
        method: 'deterministic',
      },
      {
        id: 'row-2',
        requirement: 'Include a risk assessment section',
        status: 'not_met',
        explanation: 'No section covering risk assessment was found.',
        section_title: null,
        suggested_action: 'Add a section titled "Risk Assessment".',
        method: 'deterministic',
      },
    ],
    limitations: [],
    document_fingerprint: 'abc',
    generated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

export function makeVersion(overrides: Partial<VersionEntry> = {}): VersionEntry {
  return {
    version_number: 1,
    created_at: '2026-01-01T00:00:00Z',
    origin: 'manual',
    operation: null,
    summary: 'Initial draft',
    word_count: 840,
    ...overrides,
  }
}
