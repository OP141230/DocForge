import { useEffect } from 'react'
import { createPortal } from 'react-dom'

interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
  variant?: 'danger' | 'default'
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  variant = 'default',
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel()
      }
    }

    const handleEnter = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && e.target instanceof HTMLButtonElement) {
        e.preventDefault()
      }
    }

    document.addEventListener('keydown', handleEscape)
    document.addEventListener('keydown', handleEnter)
    
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.removeEventListener('keydown', handleEnter)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onCancel])

  if (!isOpen) return null

  const confirmButtonClass = variant === 'danger'
    ? 'px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500'
    : 'btn-primary focus:ring-2 focus:ring-blue-500'

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-backdrop"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-message"
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="dialog-title" className="text-xl font-semibold text-gray-900 mb-3">
          {title}
        </h2>
        <p id="dialog-message" className="text-gray-600 mb-6">
          {message}
        </p>
        <div className="flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="btn-secondary focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={confirmButtonClass}
            autoFocus
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
