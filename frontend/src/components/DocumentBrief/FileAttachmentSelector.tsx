import { useState, useEffect } from 'react';
import { Search, X, FileText, Check, AlertCircle, Info } from 'lucide-react';
import { api } from '../../api/client';
import { KnowledgeFile, formatFileSize, getFileIcon } from '../../types/knowledge';

interface FileAttachmentSelectorProps {
  briefId: string | null;
  onAttachmentsChange: (fileIds: string[]) => void;
}

export function FileAttachmentSelector({ briefId, onAttachmentsChange }: FileAttachmentSelectorProps) {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [attachedFiles, setAttachedFiles] = useState<KnowledgeFile[]>([]);
  const [attachedFileIds, setAttachedFileIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    loadFiles();
    if (briefId) {
      loadAttachments();
    }
  }, [briefId]);

  const loadFiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getFiles(1, 100); // Get first 100 files
      // Only show completed files
      const processedFiles = response.files.filter(
        (f: KnowledgeFile) => f.extraction_status === 'completed'
      );
      setFiles(processedFiles);
    } catch (err: any) {
      console.error('Failed to load files:', err);
      setError(err.message || 'Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  const loadAttachments = async () => {
    if (!briefId) return;
    try {
      const response = await api.getBriefAttachments(briefId);
      setAttachedFiles(response.files || []);
      const ids = new Set<string>((response.files || []).map((f: KnowledgeFile) => f.id));
      setAttachedFileIds(ids);
      onAttachmentsChange(Array.from(ids));
    } catch (err: any) {
      console.error('Failed to load attachments:', err);
      // Don't set error if brief doesn't exist yet
      if (!err.message.includes('not found')) {
        setError(err.message || 'Failed to load attachments');
      }
    }
  };

  const handleToggleAttachment = async (file: KnowledgeFile) => {
    if (!briefId) {
      // Brief not created yet, just track locally
      const newIds = new Set(attachedFileIds);
      if (newIds.has(file.id)) {
        newIds.delete(file.id);
        setAttachedFiles(attachedFiles.filter(f => f.id !== file.id));
      } else {
        newIds.add(file.id);
        setAttachedFiles([...attachedFiles, file]);
      }
      setAttachedFileIds(newIds);
      onAttachmentsChange(Array.from(newIds));
      return;
    }

    // Brief exists, use API
    try {
      if (attachedFileIds.has(file.id)) {
        await api.detachFileFromBrief(briefId, file.id);
        const newIds = new Set(attachedFileIds);
        newIds.delete(file.id);
        setAttachedFileIds(newIds);
        setAttachedFiles(attachedFiles.filter(f => f.id !== file.id));
        onAttachmentsChange(Array.from(newIds));
      } else {
        await api.attachFileToBrief(briefId, file.id);
        const newIds = new Set(attachedFileIds);
        newIds.add(file.id);
        setAttachedFileIds(newIds);
        setAttachedFiles([...attachedFiles, file]);
        onAttachmentsChange(Array.from(newIds));
      }
    } catch (err: any) {
      console.error('Failed to toggle attachment:', err);
      setError(err.message || 'Failed to update attachments');
    }
  };

  const filteredFiles = files.filter(file =>
    file.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="w-5 h-5 text-gray-700" />
          <span className="text-sm font-medium text-gray-700">Reference Files</span>
          <span className="text-sm text-gray-500">(Optional)</span>
        </div>
        <div className="border border-gray-300 rounded-lg p-4 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Loading files...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <label className="block">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="w-5 h-5 text-gray-700" />
          <span className="text-sm font-medium text-gray-700">Reference Files</span>
          <span className="text-sm text-gray-500">(Optional)</span>
          <div className="group relative">
            <Info className="w-4 h-4 text-gray-400 cursor-help" />
            <div className="invisible group-hover:visible absolute left-0 top-6 w-72 p-2 bg-gray-800 text-white text-xs rounded shadow-lg z-10">
              Attach files from your knowledge base to use as reference material when generating this document.
              The AI will use content from these files to create more accurate and contextual content.
            </div>
          </div>
        </div>
      </label>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Attached Files Display */}
      {attachedFiles.length > 0 && (
        <div className="border border-blue-200 bg-blue-50 rounded-lg p-3">
          <div className="text-sm font-medium text-blue-900 mb-2">
            Attached Files ({attachedFiles.length})
          </div>
          <div className="space-y-1">
            {attachedFiles.map(file => (
              <div
                key={file.id}
                className="flex items-center justify-between bg-white px-3 py-2 rounded border border-blue-200"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="text-lg">{getFileIcon(file.file_extension)}</span>
                  <span className="text-sm text-gray-900 truncate">{file.original_filename}</span>
                  <span className="text-xs text-gray-500">{formatFileSize(file.file_size_bytes)}</span>
                </div>
                <button
                  onClick={() => handleToggleAttachment(file)}
                  className="ml-2 p-1 text-red-600 hover:bg-red-50 rounded transition-colors flex-shrink-0"
                  title="Remove"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* File Selector Toggle */}
      <div>
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-between"
        >
          <span>
            {isExpanded ? 'Hide' : 'Show'} Available Files
            {files.length > 0 && ` (${files.length})`}
          </span>
          <span className="text-gray-400">{isExpanded ? '▲' : '▼'}</span>
        </button>
      </div>

      {/* File List */}
      {isExpanded && (
        <div className="border border-gray-300 rounded-lg overflow-hidden">
          {/* Search */}
          <div className="p-3 bg-gray-50 border-b border-gray-300">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 outline-none bg-transparent text-sm text-gray-700 placeholder-gray-400"
              />
            </div>
          </div>

          {/* Files */}
          <div className="max-h-60 overflow-y-auto">
            {filteredFiles.length === 0 ? (
              <div className="p-6 text-center">
                {files.length === 0 ? (
                  <>
                    <FileText className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">No processed files available</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Upload files to your knowledge base first
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-gray-600">No files match your search</p>
                )}
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {filteredFiles.map(file => {
                  const isAttached = attachedFileIds.has(file.id);
                  return (
                    <div
                      key={file.id}
                      className={`p-3 hover:bg-gray-50 transition-colors cursor-pointer ${
                        isAttached ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => handleToggleAttachment(file)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <span className="text-lg">{getFileIcon(file.file_extension)}</span>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm text-gray-900 truncate">
                              {file.original_filename}
                            </div>
                            <div className="text-xs text-gray-500">
                              {formatFileSize(file.file_size_bytes)} • {' '}
                              {new Date(file.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        <div
                          className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                            isAttached
                              ? 'bg-blue-600 border-blue-600'
                              : 'border-gray-300 bg-white'
                          }`}
                        >
                          {isAttached && <Check className="w-3 h-3 text-white" />}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {files.length === 0 && (
        <div className="text-sm text-gray-500 mt-2">
          No files in your knowledge base yet.{' '}
          <a href="/knowledge" className="text-blue-600 hover:underline">
            Upload files
          </a>{' '}
          to use them as references.
        </div>
      )}
    </div>
  );
}
