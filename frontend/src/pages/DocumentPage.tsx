import { useState, useEffect } from 'react'
import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { DocumentIR } from '../types/document'

export default function DocumentPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [document, setDocument] = useState<DocumentIR | null>(null)
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'unsaved'>('saved')

  useEffect(() => {
    if (id && id !== 'new') {
      loadDocument(id)
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

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      // Simple approach: Generate outline from prompt, then content directly
      const outlineResponse = await api.generateOutline({
        document_type: 'general_report',
        topic: prompt,
        title: prompt.split('.')[0] || prompt.substring(0, 50),
        tone: 'professional',
        language: 'en',
        length: 'medium',
      })

      // Pass the outline array, not the whole response object
      const doc = await api.generateContent(
        outlineResponse.outline,  // Just the array, not the whole object
        {
          document_type: 'general_report',
          topic: prompt,
          title: prompt.split('.')[0] || prompt.substring(0, 50),
          tone: 'professional',
          language: 'en',
          length: 'medium',
        }
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
              <span className="text-sm text-gray-500">{saveStatus}</span>
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
        {/* Prompt Input (if no document yet) */}
        {!document && (
          <div className="bg-white rounded-lg shadow-md p-8 max-w-3xl mx-auto">
            <h2 className="text-2xl font-semibold mb-6">What would you like to create?</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Describe your document
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="input-field min-h-[200px] resize-y"
                  placeholder="Example: Create a technical documentation for a REST API that explains authentication, endpoints, and error handling..."
                  disabled={loading}
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                  {error}
                </div>
              )}

              <button
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="btn-primary w-full text-lg py-3"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Generating...
                  </span>
                ) : (
                  '✨ Generate Document'
                )}
              </button>

              <p className="text-sm text-gray-500 text-center mt-4">
                Using mock AI provider (no API key needed). For better results, configure OpenAI in .env
              </p>
            </div>
          </div>
        )}

        {/* Document Content View */}
        {document && (
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

            <div className="mt-8 pt-6 border-t border-gray-200 flex justify-center">
              <button
                onClick={() => {
                  setDocument(null)
                  setPrompt('')
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
    </div>
  )
}
