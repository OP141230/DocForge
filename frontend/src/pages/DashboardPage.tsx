import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../api/client'
import { DocumentIR } from '../types/document'
import { Conversation } from '../types/conversation'
import ConfirmDialog from '../components/ConfirmDialog'

type TabType = 'conversations' | 'documents' | 'briefs'

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentIR[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabType>('conversations')
  const [error, setError] = useState<string | null>(null)
  
  // Confirmation dialog state
  const [showDeleteConvDialog, setShowDeleteConvDialog] = useState(false)
  const [convToDelete, setConvToDelete] = useState<string | null>(null)
  const [showDeleteDocDialog, setShowDeleteDocDialog] = useState(false)
  const [docToDelete, setDocToDelete] = useState<string | null>(null)
  
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [docsData, convsData] = await Promise.all([
        api.listDocuments(),
        api.listConversations(),
      ])
      setDocuments(docsData.documents)
      setConversations(convsData.conversations)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const createNewDocument = () => {
    navigate('/document/new')
  }

  const createNewConversation = async () => {
    try {
      const conv = await api.createConversation('New Conversation')
      navigate(`/conversation/${conv.id}`)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const deleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setConvToDelete(id)
    setShowDeleteConvDialog(true)
  }

  const confirmDeleteConversation = async () => {
    if (!convToDelete) return
    
    try {
      await api.deleteConversation(convToDelete)
      setConversations(conversations.filter(c => c.id !== convToDelete))
      setShowDeleteConvDialog(false)
      setConvToDelete(null)
    } catch (error: any) {
      console.error('Failed to delete conversation:', error)
      setError(error.message || 'Failed to delete conversation')
      setShowDeleteConvDialog(false)
    }
  }

  const deleteDocument = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setDocToDelete(id)
    setShowDeleteDocDialog(true)
  }

  const confirmDeleteDocument = async () => {
    if (!docToDelete) return
    
    try {
      await api.deleteDocument(docToDelete)
      setDocuments(documents.filter(d => d.id !== docToDelete))
      setShowDeleteDocDialog(false)
      setDocToDelete(null)
    } catch (error: any) {
      console.error('Failed to delete document:', error)
      setError(error.message || 'Failed to delete document')
      setShowDeleteDocDialog(false)
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with User Info */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">DocForge</h1>
            <p className="text-lg text-gray-600">Welcome back, {user?.full_name}!</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-white rounded-md transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-700 hover:text-red-900 font-semibold"
            >
              ✕
            </button>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6 flex space-x-1 bg-white rounded-lg shadow-md p-1 max-w-3xl">
          <button
            onClick={() => setActiveTab('conversations')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'conversations'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            💬 Conversations
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'documents'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            📄 Documents
          </button>
          <button
            onClick={() => setActiveTab('briefs')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'briefs'
                ? 'bg-blue-600 text-white'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            📋 Briefs
          </button>
          <button
            onClick={() => navigate('/knowledge')}
            className="flex-1 px-4 py-2 rounded-md font-medium text-gray-700 hover:bg-gray-100 transition-colors"
          >
            📚 Knowledge
          </button>
        </div>

        {/* Create Buttons */}
        <div className="mb-8 flex space-x-4">
          <button
            onClick={createNewConversation}
            className="btn-primary text-lg px-6 py-3 shadow-lg hover:shadow-xl"
          >
            + New Conversation
          </button>
          <button
            onClick={createNewDocument}
            className="btn-secondary text-lg px-6 py-3 shadow-lg hover:shadow-xl"
          >
            + Quick Document
          </button>
          <button
            onClick={() => navigate('/briefs')}
            className="btn-secondary text-lg px-6 py-3 shadow-lg hover:shadow-xl border-2 border-blue-600"
          >
            + Document Brief
          </button>
        </div>

        {/* Content Area */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        ) : (
          <>
            {/* Conversations Tab */}
            {activeTab === 'conversations' && (
              <>
                {conversations.length === 0 ? (
                  <div className="bg-white rounded-lg shadow-md p-12 text-center">
                    <div className="text-6xl mb-4">💬</div>
                    <h2 className="text-2xl font-semibold text-gray-700 mb-2">No conversations yet</h2>
                    <p className="text-gray-500 mb-6">Start a conversation to generate documents</p>
                    <button onClick={createNewConversation} className="btn-primary">
                      Start Conversation
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {conversations.map((conv) => (
                      <div
                        key={conv.id}
                        onClick={() => navigate(`/conversation/${conv.id}`)}
                        className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-all duration-200 cursor-pointer relative group transform hover:scale-105"
                      >
                        <h3 className="text-xl font-semibold text-gray-900 mb-2 pr-8">{conv.title}</h3>
                        <p className="text-xs text-gray-400">
                          Updated {new Date(conv.updated_at).toLocaleDateString()}
                        </p>
                        <button
                          onClick={(e) => deleteConversation(conv.id, e)}
                          className="absolute top-4 right-4 text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Delete conversation"
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <>
                {documents.length === 0 ? (
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
                        className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-all duration-200 cursor-pointer relative group transform hover:scale-105"
                      >
                        <h3 className="text-xl font-semibold text-gray-900 mb-2 pr-8">{doc.title}</h3>
                        <p className="text-sm text-gray-500 mb-2">
                          {doc.metadata.document_type.replace('_', ' ')}
                        </p>
                        <p className="text-xs text-gray-400">
                          Updated {new Date(doc.updated_at).toLocaleDateString()}
                        </p>
                        <button
                          onClick={(e) => deleteDocument(doc.id, e)}
                          className="absolute top-4 right-4 text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Delete document"
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Briefs Tab */}
            {activeTab === 'briefs' && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <div className="text-6xl mb-4">📋</div>
                <h2 className="text-2xl font-semibold text-gray-700 mb-2">Document Briefs</h2>
                <p className="text-gray-500 mb-6">
                  Plan your documents with a structured wizard approach
                </p>
                <button onClick={() => navigate('/briefs')} className="btn-primary">
                  View Document Briefs
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Confirmation Dialogs */}
      <ConfirmDialog
        isOpen={showDeleteConvDialog}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={confirmDeleteConversation}
        onCancel={() => {
          setShowDeleteConvDialog(false)
          setConvToDelete(null)
        }}
      />

      <ConfirmDialog
        isOpen={showDeleteDocDialog}
        title="Delete Document"
        message="Are you sure you want to delete this document? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={confirmDeleteDocument}
        onCancel={() => {
          setShowDeleteDocDialog(false)
          setDocToDelete(null)
        }}
      />
    </div>
  )
}
