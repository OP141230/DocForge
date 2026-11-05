import { Trash2, Eye, Zap, FileText } from 'lucide-react'
import { KnowledgeFile, formatFileSize, getFileIcon } from '../../types/knowledge'

interface FileListProps {
  files: KnowledgeFile[];
  loading: boolean;
  onViewContent: (file: KnowledgeFile) => void;
  onExtractAndChunk: (file: KnowledgeFile) => void;
  onDelete: (file: KnowledgeFile) => void;
}

export default function FileList({ 
  files, 
  loading, 
  onViewContent, 
  onExtractAndChunk, 
  onDelete 
}: FileListProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading files...</p>
        </div>
      </div>
    )
  }

  if (files.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-12 text-center">
          <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No files uploaded yet</h3>
          <p className="text-gray-500">Upload your first file to build your knowledge base</p>
        </div>
      </div>
    )
  }

  const getStatusBadge = (file: KnowledgeFile) => {
    if (file.extraction_status === 'completed') {
      return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded">Processed</span>
    }
    if (file.extraction_status === 'processing') {
      return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-700 rounded">Processing...</span>
    }
    if (file.extraction_status === 'failed') {
      return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded">Failed</span>
    }
    return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded">Pending</span>
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                File
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Upload Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {files.map((file) => (
              <tr key={file.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">{getFileIcon(file.file_extension)}</span>
                    <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                      {file.original_filename}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-500 uppercase">
                    {file.file_extension.replace('.', '')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatFileSize(file.file_size_bytes)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(file.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(file)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex items-center justify-end space-x-2">
                    {file.extraction_status === 'completed' && (
                      <button
                        onClick={() => onViewContent(file)}
                        className="text-blue-600 hover:text-blue-800 p-2 rounded hover:bg-blue-50 transition-colors"
                        title="View content"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    )}
                    {file.extraction_status === 'pending' && (
                      <button
                        onClick={() => onExtractAndChunk(file)}
                        className="text-green-600 hover:text-green-800 p-2 rounded hover:bg-green-50 transition-colors"
                        title="Extract & chunk"
                      >
                        <Zap className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => onDelete(file)}
                      className="text-red-600 hover:text-red-800 p-2 rounded hover:bg-red-50 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
