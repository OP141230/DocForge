import { useState, useEffect } from 'react'
import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { DocumentIR, DocumentRequirements } from '../types/document'
import DocumentConfigModal from '../components/DocumentConfigModal'

export default function DocumentPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [document, setDocument] = useState<DocumentIR | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfigModal, setShowConfigModal] = useState(false)

  useEffect(() => {
    if (id && id !== 'new') {
      loadDocument(id)
    } else if (id === 'new') {
      // Auto-open config modal for new documents
      setShowConfigModal(true)
    }
  }, [id])

  const loadDocument = async (docId: string) => {
    try {
      const doc = await api.getDocument(docId)
      setDocument(doc)
    } catch (error) {
      console.error('Failed to load document:', error)
      setError('Failed to load document')
    }
  }

  const handleGenerate = async (requirements: DocumentRequirements) => {
    setLoading(true)
    setError(null)
    setShowConfigModal(false)
    
    try {
      // Generate outline from requirements
      const outlineResponse = await api.generateOutline(requirements)

      // Generate content from outline
      const doc = await api.generateContent(
        outlineResponse.outline,
        requirements
      )

      const created = await api.createDocument(doc)
      setDocument(created)
      navigate(`/document/${created.id}`, { replace: true })
    } catch (error: any) {
      console.error('Failed to generate:', error)
      setError(error.message || 'Failed to generate document. Make sure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleReconfigure = () => {
    setShowConfigModal(true)
  }

  const handleExport = async (format: string) => {
    if (!document) return
    try {
      const { blob, filename } = await api.exportDocument(document.id, format)
      const url = URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      setError(`Failed to export as ${format}`)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button onClick={() => navigate('/')} className="text-gray-600 hover:text-gray-900">
              ← Back
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              {document?.title || 'New Document'}
            </h1>
          </div>
          {document && (
            <div className="flex items-center space-x-4">
              <div className="relative">
                <select
                  onChange={(e) => {
                    if (e.target.value) handleExport(e.target.value)
                    e.target.value = ''
                  }}
                  className="btn-secondary"
                  defaultValue=""
                >
                  <option value="" disabled>Export</option>
                  <option value="docx">Word (DOCX)</option>
                  <option value="pdf">PDF</option>
                  <option value="markdown">Markdown</option>
                  <option value="html">HTML</option>
                  <option value="text">Plain Text</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-lg shadow-md p-8 max-w-3xl mx-auto text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-xl font-semibold text-gray-900">Generating your document...</span>
            </div>
            <p className="text-gray-600">This may take a few moments. Please wait.</p>
          </div>
        )}

        {/* Error Display */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 max-w-3xl mx-auto">
            <div className="flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="text-red-700 hover:text-red-900 font-semibold"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Prompt to configure (if no document and not loading) */}
        {!document && !loading && (
          <div className="bg-white rounded-lg shadow-md p-8 max-w-3xl mx-auto text-center">
            <div className="text-6xl mb-4">📝</div>
            <h2 className="text-2xl font-semibold mb-4">Ready to Create Your Document</h2>
            <p className="text-gray-600 mb-6">
              Click the button below to configure your document settings and start generating.
            </p>
            <button
              onClick={() => setShowConfigModal(true)}
              className="btn-primary text-lg px-8 py-3"
            >
              ⚙️ Configure & Generate
            </button>
            <p className="text-sm text-gray-500 mt-4">
              Using mock AI provider (no API key needed)
            </p>
          </div>
        )}

        {/* Document Content View */}
        {document && !loading && (
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="prose max-w-none">
              <h1>{document.title}</h1>
              {document.content.map((section) => (
                <div key={section.id} className="mb-6">
                  {React.createElement(`h${section.level}`, {}, section.title)}
                  {section.blocks.map((block: any) => {
                    if (block.type === 'paragraph') {
                      return (
                        <p key={block.id}>
                          {block.content.map((inline: any, i: number) => (
                            <span key={i} className={`
                              ${inline.bold ? 'font-bold' : ''}
                              ${inline.italic ? 'italic' : ''}
                              ${inline.underline ? 'underline' : ''}
                            `}>
                              {inline.link ? (
                                <a href={inline.link} className="text-blue-600 hover:underline">
                                  {inline.text}
                                </a>
                              ) : (
                                inline.text
                              )}
                            </span>
                          ))}
                        </p>
                      )
                    }
                    if (block.type === 'list') {
                      const ListTag = block.ordered ? 'ol' : 'ul'
                      return (
                        <ListTag key={block.id} className={block.ordered ? 'list-decimal' : 'list-disc'}>
                          {block.items.map((item: any, i: number) => (
                            <li key={i}>
                              {item.map((inline: any, j: number) => (
                                <span key={j}>{inline.text}</span>
                              ))}
                            </li>
                          ))}
                        </ListTag>
                      )
                    }
                    if (block.type === 'code_block') {
                      return (
                        <pre key={block.id} className="bg-gray-100 p-4 rounded overflow-x-auto">
                          <code>{block.code}</code>
                        </pre>
                      )
                    }
                    if (block.type === 'quote') {
                      return (
                        <blockquote key={block.id} className="border-l-4 border-gray-300 pl-4 italic">
                          {block.content.map((inline: any, i: number) => (
                            <span key={i}>{inline.text}</span>
                          ))}
                        </blockquote>
                      )
                    }
                    return null
                  })}
                </div>
              ))}
            </div>

            <div className="mt-8 pt-6 border-t border-gray-200 flex justify-center space-x-4">
              <button
                onClick={handleReconfigure}
                className="btn-secondary"
              >
                ⚙️ Reconfigure & Regenerate
              </button>
              <button
                onClick={() => {
                  setDocument(null)
                  navigate('/document/new', { replace: true })
                }}
                className="btn-secondary"
              >
                Create Another Document
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Document Configuration Modal */}
      <DocumentConfigModal
        isOpen={showConfigModal}
        initialConfig={
          document
            ? {
                document_type: document.metadata.document_type,
                title: document.title,
                topic: document.title,
                audience: document.metadata.audience || undefined,
                tone: document.metadata.tone || undefined,
                language: document.metadata.language,
              }
            : undefined
        }
        onConfirm={handleGenerate}
        onCancel={() => {
          setShowConfigModal(false)
          // If we're on /new and user cancels, go back to dashboard
          if (id === 'new' && !document) {
            navigate('/')
          }
        }}
      />
    </div>
  )
}
