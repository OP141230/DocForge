// Knowledge base TypeScript interfaces (mirror backend Pydantic models)

export interface KnowledgeFile {
  id: string;
  user_id: string;
  conversation_id?: string | null;
  original_filename: string;
  stored_filename: string;
  file_extension: string;
  mime_type?: string | null;
  file_size_bytes: number;
  content_hash: string;
  storage_path: string;
  upload_status: 'uploaded' | 'processing' | 'completed' | 'failed';
  extraction_status: 'pending' | 'processing' | 'completed' | 'failed';
  extraction_error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExtractedContent {
  id: string;
  file_id: string;
  user_id: string;
  raw_text: string;
  page_count?: number | null;
  word_count: number;
  extraction_metadata: Record<string, any>;
  created_at: string;
}

export interface ContentChunk {
  id: string;
  file_id: string;
  user_id: string;
  chunk_index: number;
  chunk_text: string;
  chunk_size: number;
  page_number?: number | null;
  section_title?: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

export interface BriefFileAttachment {
  id: string;
  brief_id: string;
  file_id: string;
  user_id: string;
  attached_at: string;
}

// Request/Response models

export interface FileUploadResponse {
  file_id: string;
  original_filename: string;
  file_size_bytes: number;
  upload_status: string;
  extraction_status: string;
}

export interface FileListResponse {
  files: KnowledgeFile[];
  total: number;
  page: number;
  page_size: number;
}

export interface SearchResult {
  chunk_id: string;
  file_id: string;
  original_filename: string;
  chunk_text: string;
  page_number?: number | null;
  section_title?: string | null;
  relevance_score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

export interface AttachFilesRequest {
  file_ids: string[];
}

// Helper functions

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

export function getFileIcon(extension: string): string {
  const ext = extension.toLowerCase().replace('.', '');
  const icons: Record<string, string> = {
    pdf: '📕',
    docx: '📘',
    doc: '📘',
    txt: '📄',
    md: '📝',
    html: '🌐',
    csv: '📊',
  };
  return icons[ext] || '📄';
}

export const ALLOWED_FILE_TYPES = ['pdf', 'docx', 'txt', 'md', 'html', 'csv'];
export const MAX_FILE_SIZE_MB = 50;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
