import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { DocumentIR } from '../types/document'

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentIR[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const data = await api.listDocuments()
      setDocuments(data.documents)
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const createNewDocument = () => {
    navigate('/document/new')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">DocForge</h1>
          <p className="text-lg text-gray-600">Plan. Generate. Edit. Export.</p>
        </div>

        {/* Create Button */}
        <div className="mb-8">
          <button
            onClick={createNewDocument}
            className="btn-primary text-lg px-6 py-3 shadow-lg hover:shadow-xl"
          >
            + Create New Document
          </button>
        </div>

        {/* Documents Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <div className="text-6xl mb-4">📄</div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">No documents yet</h2>
            <p className="text-gray-500 mb-6">Create your first document to get started</p>
            <button onClick={createNewDocument} className="btn-primary">
              Create Document
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => navigate(`/document/${doc.id}`)}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-shadow cursor-pointer"
              >
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{doc.title}</h3>
                <p className="text-sm text-gray-500 mb-2">
                  {doc.metadata.document_type.replace('_', ' ')}
                </p>
                <p className="text-xs text-gray-400">
                  Updated {new Date(doc.updated_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
