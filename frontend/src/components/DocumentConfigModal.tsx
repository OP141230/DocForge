import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import {
  DocumentRequirements,
  DocumentTone,
  DocumentLength,
  DocumentAudience,
  DOCUMENT_TYPE_LABELS,
  DOCUMENT_TONE_LABELS,
  DOCUMENT_LENGTH_LABELS,
  DOCUMENT_AUDIENCE_LABELS,
  getDefaultRequirements,
} from '../types/document'
import { saveDocumentConfig, loadDocumentConfig } from '../utils/storage'

interface DocumentConfigModalProps {
  isOpen: boolean
  initialConfig?: Partial<DocumentRequirements>
  onConfirm: (config: DocumentRequirements) => void
  onCancel: () => void
}

export default function DocumentConfigModal({
  isOpen,
  initialConfig,
  onConfirm,
  onCancel,
}: DocumentConfigModalProps) {
  const [config, setConfig] = useState<DocumentRequirements>(getDefaultRequirements())
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!isOpen) return

    // Load from localStorage or use initial config or defaults
    const savedConfig = loadDocumentConfig()
    const baseConfig = savedConfig || getDefaultRequirements()
    
    setConfig({
      ...baseConfig,
      ...initialConfig,
    })
    setErrors({})

    // Handle ESC key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel()
      }
    }

    document.addEventListener('keydown', handleEscape)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, initialConfig, onCancel])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate
    const newErrors: Record<string, string> = {}
    if (!config.topic.trim()) {
      newErrors.topic = 'Topic is required'
    }
    if (!config.title.trim()) {
      newErrors.title = 'Title is required'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    // Save to localStorage
    saveDocumentConfig(config)

    // Confirm
    onConfirm(config)
  }

  const updateField = <K extends keyof DocumentRequirements>(
    field: K,
    value: DocumentRequirements[K]
  ) => {
    setConfig((prev) => ({ ...prev, [field]: value }))
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  if (!isOpen) return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop overflow-y-auto"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="config-modal-title"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8 modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <form onSubmit={handleSubmit}>
          <div className="p-6 border-b border-gray-200">
            <h2 id="config-modal-title" className="text-2xl font-semibold text-gray-900">
              Configure Document
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Customize your document settings to get the best results
            </p>
          </div>

          <div className="p-6 space-y-5 max-h-[60vh] overflow-y-auto">
            {/* Topic */}
            <div>
              <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
                Topic <span className="text-red-500">*</span>
              </label>
              <textarea
                id="topic"
                value={config.topic}
                onChange={(e) => updateField('topic', e.target.value)}
                className={`input-field min-h-[80px] resize-y ${
                  errors.topic ? 'border-red-500 focus:ring-red-500' : ''
                }`}
                placeholder="Describe what your document should be about..."
              />
              {errors.topic && (
                <p className="text-sm text-red-600 mt-1">{errors.topic}</p>
              )}
            </div>

            {/* Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                Document Title <span className="text-red-500">*</span>
              </label>
              <input
                id="title"
                type="text"
                value={config.title}
                onChange={(e) => updateField('title', e.target.value)}
                className={`input-field ${
                  errors.title ? 'border-red-500 focus:ring-red-500' : ''
                }`}
                placeholder="Enter a title for your document..."
              />
              {errors.title && (
                <p className="text-sm text-red-600 mt-1">{errors.title}</p>
              )}
            </div>

            {/* Document Type */}
            <div>
              <label htmlFor="document_type" className="block text-sm font-medium text-gray-700 mb-2">
                Document Type
              </label>
              <select
                id="document_type"
                value={config.document_type}
                onChange={(e) => updateField('document_type', e.target.value)}
                className="input-field"
              >
                {Object.entries(DOCUMENT_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Audience */}
            <div>
              <label htmlFor="audience" className="block text-sm font-medium text-gray-700 mb-2">
                Target Audience
              </label>
              <select
                id="audience"
                value={config.audience || DocumentAudience.GENERAL}
                onChange={(e) => updateField('audience', e.target.value)}
                className="input-field"
              >
                {Object.entries(DOCUMENT_AUDIENCE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Tone */}
            <div>
              <label htmlFor="tone" className="block text-sm font-medium text-gray-700 mb-2">
                Writing Tone
              </label>
              <select
                id="tone"
                value={config.tone || DocumentTone.PROFESSIONAL}
                onChange={(e) => updateField('tone', e.target.value)}
                className="input-field"
              >
                {Object.entries(DOCUMENT_TONE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Length */}
            <div>
              <label htmlFor="length" className="block text-sm font-medium text-gray-700 mb-2">
                Document Length
              </label>
              <select
                id="length"
                value={config.length || DocumentLength.MEDIUM}
                onChange={(e) => updateField('length', e.target.value)}
                className="input-field"
              >
                {Object.entries(DOCUMENT_LENGTH_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Language */}
            <div>
              <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
                Language Code
              </label>
              <input
                id="language"
                type="text"
                value={config.language || 'en'}
                onChange={(e) => updateField('language', e.target.value)}
                className="input-field"
                placeholder="en"
              />
              <p className="text-xs text-gray-500 mt-1">
                ISO 639-1 code (e.g., en, es, fr, de)
              </p>
            </div>

            {/* Additional Instructions */}
            <div>
              <label htmlFor="additional_instructions" className="block text-sm font-medium text-gray-700 mb-2">
                Additional Instructions (Optional)
              </label>
              <textarea
                id="additional_instructions"
                value={config.additional_instructions || ''}
                onChange={(e) => updateField('additional_instructions', e.target.value)}
                className="input-field min-h-[60px] resize-y"
                placeholder="Any specific requirements or preferences..."
              />
            </div>
          </div>

          <div className="p-6 border-t border-gray-200 flex justify-end space-x-3 bg-gray-50">
            <button
              type="button"
              onClick={onCancel}
              className="btn-secondary focus:outline-none focus:ring-2 focus:ring-gray-400"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Generate Document
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  )
}
