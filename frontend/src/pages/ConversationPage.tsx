import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Conversation, Message } from '../types/conversation'
import { DocumentRequirements } from '../types/document'
import DocumentConfigModal from '../components/DocumentConfigModal'

export default function ConversationPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editedTitle, setEditedTitle] = useState('')
  const [showConfigModal, setShowConfigModal] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (id) {
      loadConversation()
    }
  }, [id])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadConversation = async () => {
    if (!id) return
    try {
      const conv = await api.getConversation(id)
      setConversation(conv)
      setEditedTitle(conv.title)
      
      // Get messages
      const messagesData = await api.listMessages(id)
      setMessages(messagesData.messages || [])
    } catch (error: any) {
      console.error('Failed to load conversation:', error)
      setError(error.message || 'Failed to load conversation')
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || !id || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)
    setError(null)

    try {
      // Create user message
      const newUserMsg = await api.createMessage(id, 'user', userMessage)
      setMessages(prev => [...prev, newUserMsg])

      // Generate response using the generation API
      const outlineResponse = await api.generateOutline({
        document_type: 'general_report',
        topic: userMessage,
        title: userMessage.split('.')[0] || userMessage.substring(0, 50),
        tone: 'professional',
        language: 'en',
        length: 'medium',
      })

      // Create a simple text response from the outline
      const responseText = `I understand you want to create a document about: "${userMessage}"\n\nI've prepared an outline:\n\n` +
        outlineResponse.outline.map((item: any, i: number) => 
          `${'  '.repeat(item.level - 1)}${i + 1}. ${item.title}`
        ).join('\n') +
        '\n\nWould you like me to generate the full document based on this outline?'

      // Create assistant message
      const assistantMsg = await api.createMessage(id, 'assistant', responseText)
      setMessages(prev => [...prev, assistantMsg])

    } catch (error: any) {
      console.error('Failed to send message:', error)
      setError(error.message || 'Failed to send message')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleUpdateTitle = async () => {
    if (!id || !editedTitle.trim() || editedTitle === conversation?.title) {
      setIsEditingTitle(false)
      return
    }

    try {
      const updated = await api.updateConversation(id, editedTitle.trim())
      setConversation(updated)
      setIsEditingTitle(false)
    } catch (error) {
      console.error('Failed to update title:', error)
      setError('Failed to update title')
    }
  }

  const handleGenerateDocument = async (requirements: DocumentRequirements) => {
    if (!id) return
    
    setLoading(true)
    setError(null)
    setShowConfigModal(false)

    try {
      // Generate outline and content
      const outlineResponse = await api.generateOutline(requirements)

      const doc = await api.generateContent(
        outlineResponse.outline,
        requirements
      )

      const created = await api.createDocument(doc)
      
      // Navigate to the document
      navigate(`/document/${created.id}`)
    } catch (error: any) {
      console.error('Failed to generate document:', error)
      setError(error.message || 'Failed to generate document')
    } finally {
      setLoading(false)
    }
  }

  const openGenerateDocumentModal = () => {
    // Modal will auto-populate from initialConfig prop
    setShowConfigModal(true)
  }

  if (error && !conversation) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md">
          <h2 className="text-xl font-semibold text-red-600 mb-4">Error</h2>
          <p className="text-gray-700 mb-6">{error}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1">
              <button
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                ← Back
              </button>
              
              {isEditingTitle ? (
                <input
                  type="text"
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  onBlur={handleUpdateTitle}
                  onKeyPress={(e) => e.key === 'Enter' && handleUpdateTitle()}
                  className="text-xl font-semibold text-gray-900 border-b-2 border-blue-500 focus:outline-none px-2"
                  autoFocus
                />
              ) : (
                <h1
                  className="text-xl font-semibold text-gray-900 cursor-pointer hover:text-blue-600 transition-colors"
                  onClick={() => setIsEditingTitle(true)}
                >
                  {conversation?.title || 'Loading...'}
                </h1>
              )}
            </div>

            <button
              onClick={openGenerateDocumentModal}
              disabled={loading || messages.length === 0}
              className="btn-primary text-sm"
            >
              📄 Generate Document
            </button>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">💬</div>
              <h2 className="text-2xl font-semibold text-gray-700 mb-2">
                Start a Conversation
              </h2>
              <p className="text-gray-500">
                Ask me anything to get started
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-900 shadow-md border border-gray-200'
                  }`}
                >
                  <div className="text-xs font-semibold mb-1 opacity-75">
                    {message.role === 'user' ? 'You' : 'Assistant'}
                  </div>
                  <div className="whitespace-pre-wrap break-words">
                    {message.content}
                  </div>
                  <div className="text-xs mt-2 opacity-60">
                    {new Date(message.created_at).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-900 shadow-md border border-gray-200 rounded-lg px-4 py-3">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
          <div className="max-w-4xl mx-auto">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-4">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
              className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              disabled={loading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!input.trim() || loading}
              className="btn-primary px-6 py-3 whitespace-nowrap"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send • Shift + Enter for new line
          </p>
        </div>
      </div>

      {/* Document Configuration Modal */}
      <DocumentConfigModal
        isOpen={showConfigModal}
        initialConfig={{
          topic: [...messages].reverse().find(m => m.role === 'user')?.content || '',
          title: [...messages].reverse().find(m => m.role === 'user')?.content.split('.')[0] || 'Untitled Document',
        }}
        onConfirm={handleGenerateDocument}
        onCancel={() => setShowConfigModal(false)}
      />
    </div>
  )
}
