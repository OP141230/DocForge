import { useState } from 'react'
import { api } from '../../api/client'
import SuggestedChange from './SuggestedChange'
import { EDIT_OPERATIONS, type EditProposal } from '../../types/review'

interface Props {
  documentId: string
  sectionId: string
  sectionTitle: string
  onClose: () => void
  onApplied: () => void | Promise<void>
}

const GROUPS = Array.from(new Set(EDIT_OPERATIONS.map((operation) => operation.group)))

/**
 * Section-scoped AI editing.
 *
 * This is intentionally a dialog over the existing document view rather than a
 * replacement rich-text editor: Phase 6 must not rebuild the editor, and the
 * review flow is "generate -> compare -> accept", not "type into the model".
 */
export default function EditSectionDialog({
  documentId,
  sectionId,
  sectionTitle,
  onClose,
  onApplied,
}: Props) {
  const [operation, setOperation] = useState('improve_clarity')
  const [instruction, setInstruction] = useState('')
  const [proposal, setProposal] = useState<EditProposal | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generate = async () => {
    setLoading(true)
    setError(null)
    setProposal(null)
    try {
      const created = (await api.proposeEdit(documentId, {
        operation,
        target_type: 'section',
        section_id: sectionId,
        instruction: instruction.trim() || undefined,
      })) as EditProposal
      setProposal(created)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not generate a suggestion')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={`Edit section ${sectionTitle}`}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between gap-4 p-5 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Improve with AI</h3>
            <p className="text-sm text-gray-600">Section: “{sectionTitle}”</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="p-5 space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Operation
            <select
              aria-label="Operation"
              className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm"
              value={operation}
              onChange={(event) => setOperation(event.target.value)}
            >
              {GROUPS.map((group) => (
                <optgroup key={group} label={group}>
                  {EDIT_OPERATIONS.filter((item) => item.group === group).map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>

          <label className="block text-sm font-medium text-gray-700">
            Extra instruction (optional)
            <textarea
              className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm"
              rows={2}
              maxLength={2000}
              value={instruction}
              placeholder="e.g. keep the tone formal and mention the 2023 audit"
              onChange={(event) => setInstruction(event.target.value)}
            />
          </label>

          <button
            type="button"
            onClick={generate}
            disabled={loading}
            className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Generating…' : proposal ? 'Generate again' : 'Generate suggestion'}
          </button>

          {error && (
            <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
              {error}
            </p>
          )}

          {proposal && (
            <SuggestedChange
              proposal={proposal}
              onApply={async (item) => {
                await api.applyProposal(item.id)
                await onApplied()
                onClose()
              }}
              onReject={async (item) => {
                await api.rejectProposal(item.id)
                setProposal(null)
              }}
            />
          )}

          <p className="text-xs text-gray-500">
            The original text is preserved in version history. Accepting this change creates a new
            version and flags affected citations for re-checking.
          </p>
        </div>
      </div>
    </div>
  )
}
