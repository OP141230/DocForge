import { useState } from 'react'
import { api } from '../../api/client'
import type { VersionComparison, VersionEntry } from '../../types/review'

interface Props {
  documentId: string
  versions: VersionEntry[]
  onReload: () => void | Promise<void>
  onRefreshVersions: () => void | Promise<void>
}

const ORIGIN_LABELS: Record<string, string> = {
  manual: 'Manual',
  ai_accepted: 'AI-assisted',
  restore: 'Restore point',
  import: 'Imported',
}

export default function VersionHistoryPanel({
  documentId,
  versions,
  onReload,
  onRefreshVersions,
}: Props) {
  const [comparison, setComparison] = useState<VersionComparison | null>(null)
  const [from, setFrom] = useState<number | null>(null)
  const [to, setTo] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmRestore, setConfirmRestore] = useState<number | null>(null)

  const compare = async () => {
    if (from === null || to === null) return
    setLoading(true)
    setError(null)
    try {
      const result = (await api.compareVersions(documentId, from, to)) as VersionComparison
      setComparison(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed')
    } finally {
      setLoading(false)
    }
  }

  const restore = async (versionNumber: number) => {
    setLoading(true)
    setError(null)
    try {
      await api.restoreVersionSnapshot(documentId, versionNumber)
      setConfirmRestore(null)
      await onReload()
      await onRefreshVersions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Restore failed')
    } finally {
      setLoading(false)
    }
  }

  if (versions.length === 0) {
    return (
      <div className="bg-white border border-dashed border-gray-300 rounded-lg p-8 text-center">
        <p className="font-medium text-gray-700">No versions yet</p>
        <p className="text-sm text-gray-500 mt-1">
          Versions are created automatically when you accept an AI edit.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <section className="bg-white border border-gray-200 rounded-lg p-5">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">Version history</h3>
        <p className="text-sm text-gray-600 mb-4">
          Restoring creates a new version first, so you can always undo the undo.
        </p>

        <ul className="divide-y divide-gray-100">
          {versions.map((version) => (
            <li key={version.version_number} className="py-3 flex flex-wrap items-center gap-3">
              <span className="font-mono text-sm text-gray-900">v{version.version_number}</span>
              <span className="text-xs px-2 py-0.5 rounded border border-gray-200 bg-gray-50 text-gray-700">
                {ORIGIN_LABELS[version.origin] ?? version.origin}
              </span>
              <span className="text-xs text-gray-500">{version.word_count} words</span>
              {version.summary && (
                <span className="text-xs text-gray-600 flex-1 min-w-[8rem]">{version.summary}</span>
              )}
              <span className="text-xs text-gray-400">
                {new Date(version.created_at).toLocaleString()}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="text-xs px-2 py-1 border border-gray-300 rounded hover:bg-gray-50"
                  onClick={() => setFrom(version.version_number)}
                  aria-label={`Use version ${version.version_number} as comparison base`}
                >
                  Set A
                </button>
                <button
                  type="button"
                  className="text-xs px-2 py-1 border border-gray-300 rounded hover:bg-gray-50"
                  onClick={() => setTo(version.version_number)}
                  aria-label={`Use version ${version.version_number} as comparison target`}
                >
                  Set B
                </button>
                <button
                  type="button"
                  className="text-xs px-2 py-1 border border-red-300 text-red-700 rounded hover:bg-red-50"
                  onClick={() => setConfirmRestore(version.version_number)}
                >
                  Restore
                </button>
              </div>
            </li>
          ))}
        </ul>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs text-gray-600">
            Compare A: {from ?? '—'} → B: {to ?? '—'}
          </span>
          <button
            type="button"
            onClick={compare}
            disabled={from === null || to === null || loading}
            className="text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Comparing…' : 'Compare'}
          </button>
        </div>

        {error && (
          <p role="alert" className="mt-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {error}
          </p>
        )}
      </section>

      {confirmRestore !== null && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <p className="text-sm text-amber-900 mb-3">
            Restore version {confirmRestore}? The current text is saved as a new version first, so
            nothing is lost.
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => restore(confirmRestore)}
              className="text-sm px-3 py-1.5 rounded bg-amber-600 text-white hover:bg-amber-700"
            >
              Yes, restore
            </button>
            <button
              type="button"
              onClick={() => setConfirmRestore(null)}
              className="text-sm px-3 py-1.5 rounded border border-gray-300 bg-white hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {comparison && (
        <section className="bg-white border border-gray-200 rounded-lg p-5">
          <h4 className="font-semibold text-gray-900 mb-2">
            v{comparison.from_version} → v{comparison.to_version}
          </h4>
          <p className="text-xs text-gray-500 mb-3">
            {comparison.from_word_count} → {comparison.to_word_count} words
            {comparison.changed_sections.length > 0 &&
              ` · changed: ${comparison.changed_sections.join(', ')}`}
          </p>
          <pre className="text-xs bg-gray-50 border border-gray-200 rounded p-3 overflow-x-auto whitespace-pre-wrap">
            {comparison.diff.map((line, index) => (
              <div
                key={index}
                className={
                  line.startsWith('+') && !line.startsWith('+++')
                    ? 'text-green-700'
                    : line.startsWith('-') && !line.startsWith('---')
                      ? 'text-red-700'
                      : 'text-gray-600'
                }
              >
                {line || ' '}
              </div>
            ))}
          </pre>
        </section>
      )}
    </div>
  )
}
