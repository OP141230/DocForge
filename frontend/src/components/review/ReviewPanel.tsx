import { useState } from 'react'
import { api } from '../../api/client'
import FindingsList from './FindingsList'
import SuggestedChange from './SuggestedChange'
import {
  ALL_CATEGORIES,
  CATEGORY_LABELS,
  MODE_DESCRIPTIONS,
  MODE_LABELS,
  SEVERITY_LABELS,
  type EditProposal,
  type FindingStatus,
  type ReviewCategory,
  type ReviewFinding,
  type ReviewMode,
  type ReviewReport,
  type Severity,
} from '../../types/review'

interface SectionOption {
  id: string
  title: string
}

interface Props {
  documentId: string
  sections: SectionOption[]
  report: ReviewReport | null
  onReportChange: (report: ReviewReport | null) => void
  /** Called after an accepted edit so the parent can reload the document. */
  onDocumentUpdated?: () => void | Promise<void>
}

export default function ReviewPanel({
  documentId,
  sections,
  report,
  onReportChange,
  onDocumentUpdated,
}: Props) {
  const [mode, setMode] = useState<ReviewMode>('full')
  const [categories, setCategories] = useState<ReviewCategory[]>([])
  const [scope, setScope] = useState<'document' | 'section'>('document')
  const [sectionId, setSectionId] = useState<string>('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busyFinding, setBusyFinding] = useState<string | null>(null)
  const [proposal, setProposal] = useState<EditProposal | null>(null)
  const [proposalBusy, setProposalBusy] = useState(false)

  const runReview = async () => {
    setRunning(true)
    setError(null)
    try {
      const result = (await api.startReview(documentId, {
        mode,
        scope,
        categories: mode === 'custom' ? categories : undefined,
        section_id: scope === 'section' ? sectionId : undefined,
      })) as ReviewReport
      onReportChange(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Review failed')
    } finally {
      setRunning(false)
    }
  }

  const changeStatus = async (findingId: string, status: FindingStatus) => {
    setBusyFinding(findingId)
    try {
      await api.updateFinding(findingId, status)
      if (report) {
        onReportChange({
          ...report,
          findings: report.findings.map((finding) =>
            finding.id === findingId ? { ...finding, status } : finding,
          ),
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update finding')
    } finally {
      setBusyFinding(null)
    }
  }

  const requestEdit = async (finding: ReviewFinding) => {
    if (!finding.section_id) return
    setProposalBusy(true)
    setError(null)
    try {
      const created = (await api.proposeEdit(documentId, {
        operation: finding.category === 'grammar' || finding.category === 'spelling'
          ? 'fix_grammar'
          : 'improve_clarity',
        target_type: 'section',
        section_id: finding.section_id,
      })) as EditProposal
      setProposal(created)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not generate a suggestion')
    } finally {
      setProposalBusy(false)
    }
  }

  const canRun = mode !== 'custom' || categories.length > 0

  return (
    <div className="space-y-6">
      <section className="bg-white border border-gray-200 rounded-lg p-5">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">Review this document</h3>
        <p className="text-sm text-gray-600 mb-4">
          Findings are suggestions. Nothing changes until you accept a specific edit.
        </p>

        <div className="grid gap-3 sm:grid-cols-2 mb-3">
          {(Object.keys(MODE_LABELS) as ReviewMode[]).map((value) => (
            <label
              key={value}
              className={`border rounded-lg p-3 cursor-pointer text-sm ${
                mode === value
                  ? 'border-blue-500 ring-1 ring-blue-300 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="radio"
                name="review-mode"
                className="sr-only"
                value={value}
                checked={mode === value}
                onChange={() => setMode(value)}
              />
              <span className="font-medium text-gray-900 block">{MODE_LABELS[value]}</span>
              <span className="text-gray-600">{MODE_DESCRIPTIONS[value]}</span>
            </label>
          ))}
        </div>

        {mode === 'custom' && (
          <fieldset className="mb-3">
            <legend className="text-sm font-medium text-gray-700 mb-2">Categories</legend>
            <div className="flex flex-wrap gap-2">
              {ALL_CATEGORIES.map((category) => {
                const checked = categories.includes(category)
                return (
                  <label
                    key={category}
                    className={`text-xs px-2 py-1 rounded border cursor-pointer ${
                      checked
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={checked}
                      onChange={() =>
                        setCategories((current) =>
                          checked
                            ? current.filter((item) => item !== category)
                            : [...current, category],
                        )
                      }
                    />
                    {CATEGORY_LABELS[category]}
                  </label>
                )
              })}
            </div>
          </fieldset>
        )}

        <div className="flex flex-wrap items-center gap-3 mb-4">
          <label className="text-sm text-gray-700">
            Scope
            <select
              className="ml-2 border border-gray-300 rounded px-2 py-1 text-sm"
              value={scope}
              onChange={(event) => setScope(event.target.value as 'document' | 'section')}
            >
              <option value="document">Whole document</option>
              <option value="section">One section</option>
            </select>
          </label>

          {scope === 'section' && (
            <select
              aria-label="Section"
              className="border border-gray-300 rounded px-2 py-1 text-sm"
              value={sectionId}
              onChange={(event) => setSectionId(event.target.value)}
            >
              <option value="">Select a section…</option>
              {sections.map((section) => (
                <option key={section.id} value={section.id}>
                  {section.title}
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={runReview}
            disabled={running || !canRun || (scope === 'section' && !sectionId)}
            className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {running ? 'Reviewing…' : 'Run review'}
          </button>
        </div>

        {running && (
          <div className="flex items-center gap-2 text-sm text-gray-600" role="status">
            <span className="h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            Analysing the document. This can take a moment.
          </div>
        )}

        {error && (
          <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {error}
          </p>
        )}
      </section>

      {report && (
        <section className="bg-white border border-gray-200 rounded-lg p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2 mb-3">
            <h3 className="text-lg font-semibold text-gray-900">
              {report.summary.total} finding{report.summary.total === 1 ? '' : 's'}
            </h3>
            <p className="text-xs text-gray-500">
              {MODE_LABELS[report.session.mode]} · {report.session.scope === 'section' ? 'section' : 'whole document'} ·{' '}
              {report.summary.open} open
              {report.summary.stale > 0 ? ` · ${report.summary.stale} stale` : ''}
            </p>
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            {(Object.keys(SEVERITY_LABELS) as Severity[]).map((severity) => (
              <span
                key={severity}
                className="text-xs px-2 py-1 rounded border border-gray-200 bg-gray-50 text-gray-700"
              >
                {SEVERITY_LABELS[severity]}: {report.summary.by_severity[severity] ?? 0}
              </span>
            ))}
          </div>

          {report.limitations.length > 0 && (
            <details className="mb-4 text-sm">
              <summary className="cursor-pointer text-gray-600">
                What this review can and cannot tell you
              </summary>
              <ul className="mt-2 list-disc pl-5 space-y-1 text-gray-600">
                {report.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </details>
          )}

          <FindingsList
            findings={report.findings}
            onStatusChange={changeStatus}
            onRequestEdit={requestEdit}
            busyFindingId={busyFinding}
          />

          {proposalBusy && (
            <p className="text-sm text-gray-600 mt-4" role="status">
              Generating a suggestion…
            </p>
          )}

          {proposal && (
            <div className="mt-5">
              <SuggestedChange
                proposal={proposal}
                onApply={async (item) => {
                  await api.applyProposal(item.id)
                  setProposal(null)
                  if (onDocumentUpdated) await onDocumentUpdated()
                }}
                onReject={async (item) => {
                  await api.rejectProposal(item.id)
                  setProposal(null)
                }}
              />
            </div>
          )}
        </section>
      )}

      {!report && !running && (
        <section className="bg-white border border-dashed border-gray-300 rounded-lg p-8 text-center">
          <p className="font-medium text-gray-700">No review yet</p>
          <p className="text-sm text-gray-500 mt-1">
            Choose a mode above and run a review to see findings here.
          </p>
        </section>
      )}
    </div>
  )
}
