import { useState } from 'react'
import { api } from '../../api/client'
import { COMPLIANCE_LABELS, type ComplianceReport, type ComplianceStatus } from '../../types/review'

const STATUS_STYLES: Record<ComplianceStatus, string> = {
  met: 'bg-green-100 text-green-800 border-green-200',
  partially_met: 'bg-amber-100 text-amber-800 border-amber-200',
  not_met: 'bg-red-100 text-red-800 border-red-200',
  not_applicable: 'bg-gray-100 text-gray-600 border-gray-200',
  needs_review: 'bg-blue-100 text-blue-800 border-blue-200',
}

interface Props {
  documentId: string
  report: ComplianceReport | null
  onReportChange: (report: ComplianceReport | null) => void
}

export default function CompliancePanel({ documentId, report, onReportChange }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = (await api.checkCompliance(documentId)) as ComplianceReport
      onReportChange(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Compliance check failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <section className="bg-white border border-gray-200 rounded-lg p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Brief compliance</h3>
            <p className="text-sm text-gray-600">
              Compares the document with the requirements you set when it was created.
            </p>
          </div>
          <button
            type="button"
            onClick={run}
            disabled={loading}
            className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Checking…' : report ? 'Re-check' : 'Check compliance'}
          </button>
        </div>

        {error && (
          <p role="alert" className="mt-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {error}
          </p>
        )}
      </section>

      {report && (
        <section className="bg-white border border-gray-200 rounded-lg p-5">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <span className="text-sm text-gray-600">Overall:</span>
            <span
              className={`text-sm font-semibold px-2 py-0.5 rounded border ${STATUS_STYLES[report.overall]}`}
              data-testid="compliance-overall"
            >
              {COMPLIANCE_LABELS[report.overall]}
            </span>
            {report.brief_title && (
              <span className="text-xs text-gray-500">Brief: {report.brief_title}</span>
            )}
          </div>

          {report.results.length === 0 ? (
            <p className="text-sm text-gray-500">
              This document is not linked to a brief, so there is nothing to check.
            </p>
          ) : (
            <ul className="space-y-2">
              {report.results.map((result) => (
                <li
                  key={`${result.requirement}-${result.id}`}
                  className="border border-gray-200 rounded p-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="font-medium text-gray-900 text-sm">{result.requirement}</p>
                    <span
                      className={`text-xs font-semibold px-2 py-0.5 rounded border ${STATUS_STYLES[result.status]}`}
                    >
                      {COMPLIANCE_LABELS[result.status]}
                    </span>
                  </div>
                  {result.explanation && (
                    <p className="text-sm text-gray-600 mt-1">{result.explanation}</p>
                  )}
                  {result.suggested_action && (
                    <p className="text-xs text-blue-700 mt-1">Suggested: {result.suggested_action}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {result.method === 'deterministic'
                      ? 'Measured automatically'
                      : result.method === 'ai'
                        ? 'Assessed by AI (an opinion, not a measurement)'
                        : 'Needs your judgement'}
                  </p>
                </li>
              ))}
            </ul>
          )}

          {report.limitations.length > 0 && (
            <details className="mt-4 text-sm">
              <summary className="cursor-pointer text-gray-600">Limitations</summary>
              <ul className="mt-2 list-disc pl-5 space-y-1 text-gray-600">
                {report.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </details>
          )}
        </section>
      )}
    </div>
  )
}
