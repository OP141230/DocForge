import { useMemo, useState } from 'react'
import {
  CATEGORY_LABELS,
  SEVERITY_LABELS,
  type FindingStatus,
  type ReviewFinding,
  type ReviewCategory,
  type Severity,
} from '../../types/review'

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
  suggestion: 'bg-gray-100 text-gray-700 border-gray-200',
}

const STATUS_STYLES: Record<FindingStatus, string> = {
  open: 'bg-white text-gray-700 border-gray-300',
  accepted: 'bg-green-50 text-green-700 border-green-300',
  rejected: 'bg-red-50 text-red-700 border-red-300',
  resolved: 'bg-emerald-50 text-emerald-700 border-emerald-300',
  ignored: 'bg-gray-50 text-gray-500 border-gray-300',
}

interface Props {
  findings: ReviewFinding[]
  onStatusChange: (findingId: string, status: FindingStatus) => void | Promise<void>
  onRequestEdit?: (finding: ReviewFinding) => void
  busyFindingId?: string | null
}

export default function FindingsList({ findings, onStatusChange, onRequestEdit, busyFindingId }: Props) {
  const [category, setCategory] = useState<ReviewCategory | 'all'>('all')
  const [severity, setSeverity] = useState<Severity | 'all'>('all')
  const [status, setStatus] = useState<FindingStatus | 'all'>('all')
  const [expanded, setExpanded] = useState<string | null>(null)

  const availableCategories = useMemo(
    () => Array.from(new Set(findings.map((finding) => finding.category))),
    [findings],
  )

  const visible = useMemo(
    () =>
      findings.filter(
        (finding) =>
          (category === 'all' || finding.category === category) &&
          (severity === 'all' || finding.severity === severity) &&
          (status === 'all' || finding.status === status),
      ),
    [findings, category, severity, status],
  )

  if (findings.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500">
        <p className="text-base font-medium text-gray-700">No findings</p>
        <p className="text-sm mt-1">
          This review did not find problems in the checked categories.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4" role="group" aria-label="Finding filters">
        <select
          aria-label="Filter by category"
          className="text-sm border border-gray-300 rounded px-2 py-1"
          value={category}
          onChange={(event) => setCategory(event.target.value as ReviewCategory | 'all')}
        >
          <option value="all">All categories</option>
          {availableCategories.map((value) => (
            <option key={value} value={value}>
              {CATEGORY_LABELS[value]}
            </option>
          ))}
        </select>

        <select
          aria-label="Filter by severity"
          className="text-sm border border-gray-300 rounded px-2 py-1"
          value={severity}
          onChange={(event) => setSeverity(event.target.value as Severity | 'all')}
        >
          <option value="all">All severities</option>
          {(Object.keys(SEVERITY_LABELS) as Severity[]).map((value) => (
            <option key={value} value={value}>
              {SEVERITY_LABELS[value]}
            </option>
          ))}
        </select>

        <select
          aria-label="Filter by status"
          className="text-sm border border-gray-300 rounded px-2 py-1"
          value={status}
          onChange={(event) => setStatus(event.target.value as FindingStatus | 'all')}
        >
          <option value="all">All statuses</option>
          <option value="open">Open</option>
          <option value="accepted">Accepted</option>
          <option value="rejected">Rejected</option>
          <option value="resolved">Resolved</option>
          <option value="ignored">Ignored</option>
        </select>

        <span className="text-sm text-gray-500 self-center">
          {visible.length} of {findings.length}
        </span>
      </div>

      {visible.length === 0 ? (
        <p className="text-sm text-gray-500 py-6 text-center">No findings match these filters.</p>
      ) : (
        <ul className="space-y-3">
          {visible.map((finding) => {
            const isOpen = expanded === finding.id
            return (
              <li
                key={finding.id}
                className={`border rounded-lg p-4 ${STATUS_STYLES[finding.status]}`}
                data-testid={`finding-${finding.id}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded border ${SEVERITY_STYLES[finding.severity]}`}
                      >
                        {SEVERITY_LABELS[finding.severity]}
                      </span>
                      <span className="text-xs text-gray-600">
                        {CATEGORY_LABELS[finding.category]}
                      </span>
                      <span className="text-xs text-gray-400">
                        {finding.source === 'deterministic' ? 'Checked automatically' : 'AI suggestion'}
                      </span>
                      {finding.is_stale && (
                        <span
                          className="text-xs font-semibold px-2 py-0.5 rounded border border-purple-200 bg-purple-50 text-purple-700"
                          title="The document changed after this review ran"
                        >
                          Stale
                        </span>
                      )}
                    </div>
                    <p className="font-medium text-gray-900">{finding.title}</p>
                    {finding.section_title && (
                      <p className="text-xs text-gray-500 mt-0.5">in “{finding.section_title}”</p>
                    )}
                  </div>
                  <button
                    type="button"
                    className="text-sm text-blue-700 hover:underline shrink-0"
                    onClick={() => setExpanded(isOpen ? null : finding.id)}
                    aria-expanded={isOpen}
                  >
                    {isOpen ? 'Hide' : 'Details'}
                  </button>
                </div>

                {isOpen && (
                  <div className="mt-3 space-y-3 text-sm">
                    <p className="text-gray-700">{finding.explanation}</p>

                    {finding.original_text && (
                      <div>
                        <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                          Affected text
                        </p>
                        <p className="bg-white border border-gray-200 rounded p-2 text-gray-800 whitespace-pre-wrap">
                          {finding.original_text}
                        </p>
                      </div>
                    )}

                    {finding.suggested_text && (
                      <div>
                        <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                          Suggested replacement
                        </p>
                        <p className="bg-green-50 border border-green-200 rounded p-2 text-gray-800 whitespace-pre-wrap">
                          {finding.suggested_text}
                        </p>
                      </div>
                    )}

                    {finding.is_stale && (
                      <p className="text-xs text-purple-700">
                        This finding refers to an older version of the text. Re-run the review before
                        acting on it.
                      </p>
                    )}

                    {(finding.citation_ids.length > 0 || finding.evidence_ids.length > 0) && (
                      <p className="text-xs text-gray-500">
                        Linked to {finding.citation_ids.length} citation(s) and{' '}
                        {finding.evidence_ids.length} evidence record(s).
                      </p>
                    )}
                  </div>
                )}

                <div className="mt-3 flex flex-wrap gap-2">
                  {(['accepted', 'rejected', 'ignored', 'resolved'] as FindingStatus[]).map((next) => (
                    <button
                      key={next}
                      type="button"
                      disabled={busyFindingId === finding.id || finding.status === next}
                      onClick={() => onStatusChange(finding.id, next)}
                      className="text-xs px-2 py-1 rounded border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed capitalize"
                    >
                      {next}
                    </button>
                  ))}
                  {onRequestEdit && finding.section_id && (
                    <button
                      type="button"
                      onClick={() => onRequestEdit(finding)}
                      className="text-xs px-2 py-1 rounded border border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100"
                    >
                      Fix with AI
                    </button>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
