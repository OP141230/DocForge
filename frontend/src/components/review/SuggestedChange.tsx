import { useMemo, useState } from 'react'
import type { EditProposal } from '../../types/review'
import { diffWords, isTrivialChange } from './diff'

interface Props {
  proposal: EditProposal
  onApply: (proposal: EditProposal) => Promise<void> | void
  onReject: (proposal: EditProposal) => Promise<void> | void
}

/**
 * Original vs proposed comparison.
 *
 * The diff is rendered inline (removed text struck through in red, added text in
 * green) because a single column reads better than two narrow columns for
 * paragraph-length rewrites. The full texts remain available side by side for
 * copy/paste.
 */
export default function SuggestedChange({ proposal, onApply, onReject }: Props) {
  const [showSideBySide, setShowSideBySide] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const segments = useMemo(
    () => diffWords(proposal.original_text, proposal.proposed_text),
    [proposal.original_text, proposal.proposed_text],
  )

  const trivial = isTrivialChange(proposal.original_text, proposal.proposed_text)
  const recheck =
    proposal.impact?.citation_review_required || proposal.impact?.verification_recheck_required

  const run = async (action: () => Promise<void> | void) => {
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between gap-3 mb-3">
        <h4 className="font-semibold text-gray-900">Suggested change</h4>
        <button
          type="button"
          className="text-xs text-blue-700 hover:underline"
          onClick={() => setShowSideBySide((value) => !value)}
        >
          {showSideBySide ? 'Show inline diff' : 'Show side by side'}
        </button>
      </div>

      {trivial && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2 mb-3">
          This suggestion only changes capitalisation or spacing.
        </p>
      )}

      {showSideBySide ? (
        <div className="grid md:grid-cols-2 gap-3 mb-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Original</p>
            <p className="border border-gray-200 rounded p-2 text-sm whitespace-pre-wrap text-gray-800 bg-gray-50">
              {proposal.original_text}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Proposed</p>
            <p className="border border-green-200 rounded p-2 text-sm whitespace-pre-wrap text-gray-800 bg-green-50">
              {proposal.proposed_text}
            </p>
          </div>
        </div>
      ) : (
        <p
          className="border border-gray-200 rounded p-3 text-sm whitespace-pre-wrap leading-relaxed mb-3"
          data-testid="proposal-diff"
        >
          {segments.map((segment, index) => {
            if (segment.op === 'removed') {
              return (
                <del key={index} className="bg-red-100 text-red-800">
                  {segment.text}
                </del>
              )
            }
            if (segment.op === 'added') {
              return (
                <ins key={index} className="bg-green-100 text-green-800 no-underline">
                  {segment.text}
                </ins>
              )
            }
            return <span key={index}>{segment.text}</span>
          })}
        </p>
      )}

      {recheck && (
        <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2 mb-3">
          {proposal.impact?.notes ??
            'Citations or verified claims in this section will be marked for re-checking.'}
        </p>
      )}

      {error && (
        <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2 mb-3">
          {error}
        </p>
      )}

      <div className="flex gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => run(() => onApply(proposal))}
          className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Applying…' : 'Accept change'}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => run(() => onReject(proposal))}
          className="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </div>
  )
}
