import { X, FileText } from 'lucide-react'
import { KnowledgeFile, ExtractedContent, formatFileSize } from '../../types/knowledge'
import { useEffect } from 'react'

interface FilePreviewProps {
  file: KnowledgeFile;
  content: ExtractedContent | null;
  loading: boolean;
  onClose: () => void;
}

export default function FilePreview({ file, content, loading, onClose }: FilePreviewProps) {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [])

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-gray-200">
          <div className="flex-1 pr-4">
            <div className="flex items-center space-x-3 mb-2">
              <FileText className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-semibold text-gray-900 truncate">
                {file.original_filename}
              </h2>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
              <span>Type: <span className="font-medium uppercase">{file.file_extension.replace('.', '')}</span></span>
              <span>Size: <span className="font-medium">{formatFileSize(file.file_size_bytes)}</span></span>
              {content?.page_count && (
                <span>Pages: <span className="font-medium">{content.page_count}</span></span>
              )}
              {content?.word_count && (
                <span>Words: <span className="font-medium">{content.word_count.toLocaleString()}</span></span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1"
            aria-label="Close"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-gray-600">Loading content...</p>
            </div>
          ) : content ? (
            <div className="prose prose-sm max-w-none">
              <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                {content.raw_text}
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No content available</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
