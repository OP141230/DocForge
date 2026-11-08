import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import CompliancePanel from './CompliancePanel'
import ReviewPanel from './ReviewPanel'
import VersionHistoryPanel from './VersionHistoryPanel'
import type { ComplianceReport, ReviewReport, VersionEntry } from '../../types/review'

type Tab = 'review' | 'compliance' | 'versions'

interface Props {
  documentId: string
  sections: { id: string; title: string }[]
  onDocumentUpdated?: () => void | Promise<void>
}

const TABS: { id: Tab; label: string }[] = [
  { id: 'review', label: 'AI Review' },
  { id: 'compliance', label: 'Brief Compliance' },
  { id: 'versions', label: 'Version History' },
]

/**
 * The Phase 6 workspace. It sits alongside the document and never replaces the
 * document view itself - review and editing are additive.
 */
export default function ReviewWorkspace({ documentId, sections, onDocumentUpdated }: Props) {
  const [tab, setTab] = useState<Tab>('review')
  const [report, setReport] = useState<ReviewReport | null>(null)
  const [compliance, setCompliance] = useState<ComplianceReport | null>(null)
  const [versions, setVersions] = useState<VersionEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadVersions = useCallback(async () => {
    try {
      setVersions((await api.getVersionHistory(documentId)) as VersionEntry[])
    } catch {
      // A document with no versions returns an empty list; a hard failure is
      // surfaced by the review/compliance panels instead of blocking the page.
      setVersions([])
    }
  }, [documentId])

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [latest, latestCompliance] = await Promise.all([
          api.getLatestReview(documentId),
          api.getLatestCompliance(documentId),
        ])
        if (cancelled) return
        setReport((latest as ReviewReport | null) ?? null)
        setCompliance((latestCompliance as ComplianceReport | null) ?? null)
        await loadVersions()
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Could not load the review workspace')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [documentId, loadVersions])

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg">
      <div className="flex flex-wrap gap-1 border-b border-gray-200 px-3 pt-3" role="tablist">
        {TABS.map((item) => (
          <button
            key={item.id}
            role="tab"
            aria-selected={tab === item.id}
            onClick={() => setTab(item.id)}
            className={`px-3 py-2 text-sm rounded-t ${
              tab === item.id
                ? 'bg-white border border-b-0 border-gray-200 font-semibold text-gray-900'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {loading && (
          <p className="text-sm text-gray-600" role="status">
            Loading review workspace…
          </p>
        )}

        {error && (
          <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {error}
          </p>
        )}

        {!loading && !error && tab === 'review' && (
          <ReviewPanel
            documentId={documentId}
            sections={sections}
            report={report}
            onReportChange={setReport}
            onDocumentUpdated={async () => {
              await onDocumentUpdated?.()
              await loadVersions()
            }}
          />
        )}

        {!loading && !error && tab === 'compliance' && (
          <CompliancePanel
            documentId={documentId}
            report={compliance}
            onReportChange={setCompliance}
          />
        )}

        {!loading && !error && tab === 'versions' && (
          <VersionHistoryPanel
            documentId={documentId}
            versions={versions}
            onReload={async () => {
              await onDocumentUpdated?.()
            }}
            onRefreshVersions={loadVersions}
          />
        )}
      </div>
    </div>
  )
}
