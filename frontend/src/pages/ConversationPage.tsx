import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Image, X } from 'lucide-react'
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
  const [attachedImages, setAttachedImages] = useState<File[]>([])
  const [imagePreviewUrls, setImagePreviewUrls] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
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
    if ((!input.trim() && attachedImages.length === 0) || !id || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)
    setError(null)

    try {
      // Convert images to base64 data URLs
      const imageAttachments = await Promise.all(
        attachedImages.map(async (file) => {
          return new Promise<{ filename: string; mime_type: string; size_bytes: number; data_url: string }>((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => {
              resolve({
                filename: file.name,
                mime_type: file.type,
                size_bytes: file.size,
                data_url: reader.result as string,
              })
            }
            reader.onerror = reject
            reader.readAsDataURL(file)
          })
        })
      )

      // Clear attached images after reading
      setAttachedImages([])
      imagePreviewUrls.forEach(url => URL.revokeObjectURL(url))
      setImagePreviewUrls([])

      // Create user message with attachments
      const newUserMsg = await api.createMessage(id, 'user', userMessage || '(image)', imageAttachments)
      setMessages(prev => [...prev, newUserMsg])

      // Check if OCR extracted text from images
      const hasOcrText = newUserMsg.content.includes('**Extracted text from images:**')
      
      // Generate response based on whether images are present
      let responseText = ''
      
      if (imageAttachments.length > 0) {
        // User sent images
        const imageCount = imageAttachments.length
        const imageWord = imageCount === 1 ? 'image' : 'images'
        
        if (hasOcrText) {
          // OCR successfully extracted text
          responseText = `✅ I've extracted text from your ${imageWord}!\n\n` +
            `I can see the content now. You can:\n\n` +
            `1. Ask me questions about the content\n` +
            `2. Click **"📄 Generate Document"** to create a study guide, report, or document based on this content\n` +
            `3. Add more details or context if needed\n\n` +
            `💡 The extracted text is included in our conversation, so I can help you with it!`
        } else {
          // OCR didn't find text (maybe blank image, or non-text image)
          responseText = `I received your ${imageWord}, but couldn't extract any text from it. This might be because:\n\n` +
            `• The image is a photo/diagram without text\n` +
            `• The text is handwritten or stylized\n` +
            `• The image quality is too low\n\n` +
            `You can:\n` +
            `1. Describe what's in the ${imageWord}\n` +
            `2. Upload a clearer image if available\n` +
            `3. Type the key points you want to document`
        }
      } else {
        // Text-only message - generate outline as before
        const outlineResponse = await api.generateOutline({
          document_type: 'general_report',
          topic: userMessage,
          title: userMessage.split('.')[0] || userMessage.substring(0, 50),
          tone: 'professional',
          language: 'en',
          length: 'medium',
        })

        responseText = `I understand you want to create a document about: "${userMessage}"\n\nI've prepared an outline:\n\n` +
          outlineResponse.outline.map((item: any, i: number) => 
            `${'  '.repeat(item.level - 1)}${i + 1}. ${item.title}`
          ).join('\n') +
          '\n\nWould you like me to generate the full document based on this outline?'
      }

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

  // Image handling functions
  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items
    if (!items) return

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        e.preventDefault()
        const file = items[i].getAsFile()
        if (file) {
          addImageFile(file)
        }
      }
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    Array.from(files).forEach(file => {
      if (file.type.startsWith('image/')) {
        addImageFile(file)
      }
    })

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const addImageFile = (file: File) => {
    // Create preview URL
    const previewUrl = URL.createObjectURL(file)
    
    setAttachedImages(prev => [...prev, file])
    setImagePreviewUrls(prev => [...prev, previewUrl])
  }

  const removeImage = (index: number) => {
    // Revoke object URL to prevent memory leak
    URL.revokeObjectURL(imagePreviewUrls[index])
    
    setAttachedImages(prev => prev.filter((_, i) => i !== index))
    setImagePreviewUrls(prev => prev.filter((_, i) => i !== index))
  }

  // Cleanup preview URLs on unmount
  useEffect(() => {
    return () => {
      imagePreviewUrls.forEach(url => URL.revokeObjectURL(url))
    }
  }, [])

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
      // Collect all images from conversation messages
      const allImages: string[] = []
      messages.forEach(msg => {
        if (msg.attachments && msg.attachments.length > 0) {
          msg.attachments.forEach(att => {
            allImages.push(att.data_url)
          })
        }
      })

      // Extract all text from conversation for context
      const conversationText = messages
        .filter(m => m.role === 'user' && m.content && m.content !== '(image)')
        .map(m => m.content)
        .join('\n')

      // Enhance requirements with conversation context and images
      const enhancedRequirements = {
        ...requirements,
        // Append conversation context to topic
        topic: conversationText 
          ? `${requirements.topic}\n\nAdditional context from conversation:\n${conversationText}` 
          : requirements.topic,
        // Add note about images if present
        additional_instructions: allImages.length > 0
          ? `${requirements.additional_instructions || ''}\n\nIMPORTANT: The user has provided ${allImages.length} image(s) in the conversation. Please analyze and incorporate the information from these images into the document content.`
          : requirements.additional_instructions
      }

      // Generate outline and content
      const outlineResponse = await api.generateOutline(enhancedRequirements)

      const doc = await api.generateContent(
        outlineResponse.outline,
        enhancedRequirements
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
    // Images from conversation will be included automatically via handleGenerateDocument
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
                  
                  {/* Message text */}
                  {message.content && (
                    <div className="whitespace-pre-wrap break-words">
                      {message.content}
                    </div>
                  )}

                  {/* Image attachments */}
                  {message.attachments && message.attachments.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {message.attachments.map((attachment, idx) => (
                        <div key={attachment.id || idx} className="mt-2">
                          <img
                            src={attachment.data_url}
                            alt={attachment.filename}
                            className="rounded-lg max-w-full h-auto border border-gray-300"
                            style={{ maxHeight: '300px' }}
                          />
                          <div className="text-xs mt-1 opacity-60">
                            {attachment.filename} ({(attachment.size_bytes / 1024).toFixed(1)} KB)
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

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
          {/* Image Previews */}
          {attachedImages.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {imagePreviewUrls.map((url, index) => (
                <div key={index} className="relative group">
                  <img
                    src={url}
                    alt={`Preview ${index + 1}`}
                    className="h-20 w-20 object-cover rounded-lg border border-gray-300"
                  />
                  <button
                    onClick={() => removeImage(index)}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Remove image"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-end space-x-2">
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />

            {/* Image attachment button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              title="Attach image"
              disabled={loading}
            >
              <Image className="w-5 h-5" />
            </button>

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              onPaste={handlePaste}
              placeholder="Type your message or paste an image... (Press Enter to send, Shift+Enter for new line)"
              className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              disabled={loading}
            />
            <button
              onClick={handleSendMessage}
              disabled={(!input.trim() && attachedImages.length === 0) || loading}
              className="btn-primary px-6 py-3 whitespace-nowrap"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send • Shift + Enter for new line • Paste images directly (Ctrl+V)
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
