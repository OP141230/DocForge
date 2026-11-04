export interface ApiError {
  detail: string;
}

export interface DocumentListResponse {
  documents: any[];
  total: number;
  limit: number;
  offset: number;
}

export interface VersionInfo {
  version_number: number;
  created_at: string;
  content_preview: string;
}
