import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Search, ArrowLeft } from 'lucide-react'
import { api } from '../api/client'
import { KnowledgeFile, ExtractedContent, FileListResponse } from '../types/knowledge'
import FileUploader from '../components/knowledge/FileUploader'
import FileList from '../components/knowledge/FileList'
import FilePreview from '../components/knowledge/FilePreview'
import ConfirmDialog from '../components/ConfirmDialog'

export default function KnowledgeBasePage() {
  const [files, setFiles] = useState<KnowledgeFile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showUploader, setShowUploader] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  
  // Preview modal state
  const [previewFile, setPreviewFile] = useState<KnowledgeFile | null>(null)
  const [previewContent, setPreviewContent] = useState<ExtractedContent | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  
  // Delete confirmation state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [fileToDelete, setFileToDelete] = useState<KnowledgeFile | null>(null)
  
  const navigate = useNavigate()

  useEffect(() => {
    loadFiles()
  }, [])

  const loadFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const response: FileListResponse = await api.getFiles()
      setFiles(response.files)
    } catch (err: any) {
      console.error('Failed to load files:', err)
      setError(err.message || 'Failed to load files')
    } finally {
      setLoading(false)
    }
  }

  const handleUploadComplete = () => {
    setShowUploader(false)
    loadFiles()
  }

  const handleViewContent = async (file: KnowledgeFile) => {
    setPreviewFile(file)
    setPreviewLoading(true)
    try {
      const content = await api.getFileContent(file.id)
      setPreviewContent(content)
    } catch (err: any) {
      console.error('Failed to load content:', err)
      setError(err.message || 'Failed to load file content')
      setPreviewFile(null)
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleClosePreview = () => {
    setPreviewFile(null)
    setPreviewContent(null)
  }

  const handleExtractAndChunk = async (file: KnowledgeFile) => {
    try {
      await api.extractAndChunk(file.id)
      // Refresh the file list to show updated status
      loadFiles()
    } catch (err: any) {
      console.error('Failed to extract and chunk:', err)
      setError(err.message || 'Failed to process file')
    }
  }

  const handleDeleteClick = (file: KnowledgeFile) => {
    setFileToDelete(file)
    setShowDeleteDialog(true)
  }

  const handleDeleteConfirm = async () => {
    if (!fileToDelete) return
    
    try {
      await api.deleteFile(fileToDelete.id)
      setFiles(files.filter(f => f.id !== fileToDelete.id))
      setShowDeleteDialog(false)
      setFileToDelete(null)
    } catch (err: any) {
      console.error('Failed to delete file:', err)
      setError(err.message || 'Failed to delete file')
      setShowDeleteDialog(false)
    }
  }

  const handleDeleteCancel = () => {
    setShowDeleteDialog(false)
    setFileToDelete(null)
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadFiles()
      return
    }
    
    try {
      const response = await api.searchContent(searchQuery)
      // For now, just show all files - we could filter based on search results
      // In a more advanced implementation, we'd show search results with highlights
      console.log('Search results:', response)
      setError('Search feature is under development. Showing all files.')
    } catch (err: any) {
      console.error('Search failed:', err)
      setError(err.message || 'Search failed')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-gray-900 transition-colors"
              aria-label="Back to dashboard"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Knowledge Base</h1>
              <p className="text-lg text-gray-600">Upload and manage your reference documents</p>
            </div>
          </div>
          <button
            onClick={() => setShowUploader(!showUploader)}
            className={`btn-primary flex items-center space-x-2 ${showUploader ? 'bg-gray-600' : ''}`}
          >
            <Upload className="w-5 h-5" />
            <span>{showUploader ? 'Hide Uploader' : 'Upload File'}</span>
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

        {/* File Uploader */}
        {showUploader && (
          <div className="mb-8">
            <FileUploader onUploadComplete={handleUploadComplete} />
          </div>
        )}

        {/* Search Bar */}
        <div className="mb-6 bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center space-x-2">
            <Search className="w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search knowledge base..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1 outline-none text-gray-700 placeholder-gray-400"
            />
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
              Search
            </button>
          </div>
        </div>

        {/* File List */}
        <FileList
          files={files}
          loading={loading}
          onViewContent={handleViewContent}
          onExtractAndChunk={handleExtractAndChunk}
          onDelete={handleDeleteClick}
        />

        {/* Stats Footer */}
        {!loading && files.length > 0 && (
          <div className="mt-6 text-center text-sm text-gray-500">
            {files.length} {files.length === 1 ? 'file' : 'files'} in knowledge base
          </div>
        )}
      </div>

      {/* File Preview Modal */}
      {previewFile && (
        <FilePreview
          file={previewFile}
          content={previewContent}
          loading={previewLoading}
          onClose={handleClosePreview}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        title="Delete File"
        message={`Are you sure you want to delete "${fileToDelete?.original_filename}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
      />
    </div>
  )
}
