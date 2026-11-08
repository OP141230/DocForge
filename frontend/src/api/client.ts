// API client functions
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export const api = {
  // Health
  async health() {
    const res = await fetch('/health');
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  // Auth
  async register(data: { full_name: string; email: string; password: string; confirm_password: string }) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Important for cookies
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Registration failed');
    }
    return res.json();
  },

  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // Important for cookies
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Login failed');
    }
    return res.json();
  },

  async logout() {
    const res = await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Logout failed');
    return res.json();
  },

  async getCurrentUser() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      credentials: 'include',
    });
    if (!res.ok) {
      if (res.status === 401) return null;
      throw new Error('Failed to get current user');
    }
    return res.json();
  },

  // Documents
  async createDocument(document: any) {
    const res = await fetch(`${API_BASE}/documents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(document),
    });
    if (!res.ok) throw new Error('Failed to create document');
    return res.json();
  },

  async listDocuments(limit = 20, offset = 0) {
    const res = await fetch(`${API_BASE}/documents?limit=${limit}&offset=${offset}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to list documents');
    return res.json();
  },

  async getDocument(id: string) {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Document not found');
    return res.json();
  },

  async updateDocument(id: string, document: any) {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(document),
    });
    if (!res.ok) throw new Error('Failed to update document');
    return res.json();
  },

  async deleteDocument(id: string) {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to delete document');
  },

  // Generation
  async generateOutline(requirements: any) {
    const res = await fetch(`${API_BASE}/generate/outline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(requirements),
    });
    if (!res.ok) throw new Error('Failed to generate outline');
    return res.json();
  },

  async generateContent(outline: any, requirements: any) {
    const res = await fetch(`${API_BASE}/generate/content`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ outline, requirements }),
    });
    if (!res.ok) throw new Error('Failed to generate content');
    return res.json();
  },

  async generateSection(section_title: string, context: any, instruction: string) {
    const res = await fetch(`${API_BASE}/generate/section`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ section_title, context, instruction }),
    });
    if (!res.ok) throw new Error('Failed to generate section');
    return res.json();
  },

  // Versions
  async createVersion(documentId: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/versions`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to create version');
    return res.json();
  },

  async listVersions(documentId: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/versions`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to list versions');
    return res.json();
  },

  async restoreVersion(documentId: string, versionNumber: number) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/versions/${versionNumber}/restore`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to restore version');
    return res.json();
  },

  // Export
  async exportDocument(documentId: string, format: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/export?format=${format}`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to export document');
    const blob = await res.blob();
    const contentDisposition = res.headers.get('Content-Disposition');
    const filename = contentDisposition?.match(/filename="?([^"]+)"?/)?.[1] || `document.${format}`;
    return { blob, filename };
  },

  // Conversations
  async createConversation(title: string) {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error('Failed to create conversation');
    return res.json();
  },

  async listConversations(limit = 20, offset = 0) {
    const res = await fetch(`${API_BASE}/conversations?limit=${limit}&offset=${offset}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to list conversations');
    return res.json();
  },

  async getConversation(id: string) {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      credentials: 'include',
    });
    if (!res.ok) {
      if (res.status === 404) throw new Error('Conversation not found');
      throw new Error('Failed to get conversation');
    }
    return res.json();
  },

  async updateConversation(id: string, title: string) {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error('Failed to update conversation');
    return res.json();
  },

  async deleteConversation(id: string) {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to delete conversation');
  },

  // Messages
  async createMessage(
    conversationId: string, 
    role: 'user' | 'assistant', 
    content: string,
    attachments: { filename: string; mime_type: string; size_bytes: number; data_url: string }[] = []
  ) {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ 
        role, 
        content,
        attachments: attachments.map(att => ({
          id: crypto.randomUUID(),
          ...att
        }))
      }),
    });
    if (!res.ok) throw new Error('Failed to create message');
    return res.json();
  },

  async listMessages(conversationId: string, limit = 100, offset = 0) {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages?limit=${limit}&offset=${offset}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to list messages');
    return res.json();
  },

  // Document Briefs
  async createBrief(data: any) {
    const res = await fetch(`${API_BASE}/document-briefs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to create brief');
    }
    return res.json();
  },

  async listBriefs(limit = 20, offset = 0) {
    const res = await fetch(`${API_BASE}/document-briefs?limit=${limit}&offset=${offset}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to list briefs');
    return res.json();
  },

  async getBrief(id: string) {
    const res = await fetch(`${API_BASE}/document-briefs/${id}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Brief not found');
    return res.json();
  },

  async updateBrief(id: string, data: any) {
    const res = await fetch(`${API_BASE}/document-briefs/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update brief');
    return res.json();
  },

  async deleteBrief(id: string) {
    const res = await fetch(`${API_BASE}/document-briefs/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to delete brief');
  },

  async generateBriefOutline(id: string) {
    const res = await fetch(`${API_BASE}/document-briefs/${id}/outline`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to generate outline');
    return res.json();
  },

  async updateBriefOutline(id: string, outline: any[]) {
    const res = await fetch(`${API_BASE}/document-briefs/${id}/outline`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ outline }),
    });
    if (!res.ok) throw new Error('Failed to update outline');
    return res.json();
  },

  async approveBriefOutline(id: string) {
    const res = await fetch(`${API_BASE}/document-briefs/${id}/outline/approve`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to approve outline');
    return res.json();
  },

  async generateFromBrief(id: string) {
    const res = await fetch(`${API_BASE}/document-briefs/${id}/generate`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to generate document from brief');
    return res.json();
  },

  // Knowledge Base
  async uploadFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    const res = await fetch(`${API_BASE}/knowledge/upload`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to upload file');
    }
    return res.json();
  },

  async getFiles(page = 1, page_size = 20) {
    const res = await fetch(`${API_BASE}/knowledge/files?page=${page}&page_size=${page_size}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to get files');
    return res.json();
  },

  async getFile(id: string) {
    const res = await fetch(`${API_BASE}/knowledge/files/${id}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('File not found');
    return res.json();
  },

  async deleteFile(id: string) {
    const res = await fetch(`${API_BASE}/knowledge/files/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to delete file');
  },

  async extractAndChunk(fileId: string) {
    const res = await fetch(`${API_BASE}/knowledge/files/${fileId}/extract`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to extract and chunk file');
    return res.json();
  },

  async searchContent(query: string, limit = 10) {
    const res = await fetch(`${API_BASE}/knowledge/search?query=${encodeURIComponent(query)}&limit=${limit}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to search content');
    return res.json();
  },

  async getFileContent(fileId: string) {
    const res = await fetch(`${API_BASE}/knowledge/files/${fileId}/content`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to get file content');
    return res.json();
  },

  // Brief attachments
  async attachFileToBrief(briefId: string, fileId: string) {
    const res = await fetch(`${API_BASE}/knowledge/document-briefs/${briefId}/attachments?file_id=${fileId}`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to attach file to brief');
    }
    return res.json();
  },

  async getBriefAttachments(briefId: string) {
    const res = await fetch(`${API_BASE}/knowledge/document-briefs/${briefId}/attachments`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to get brief attachments');
    return res.json();
  },

  async detachFileFromBrief(briefId: string, fileId: string) {
    const res = await fetch(`${API_BASE}/knowledge/document-briefs/${briefId}/attachments/${fileId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to detach file from brief');
  },

  // ============================================================
  // Phase 5: Research, Citations, and Verification
  // ============================================================

  // Research Provider Status
  async getResearchProviders() {
    const res = await fetch(`${API_BASE}/research/providers`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to get research provider status');
    return res.json();
  },

  // Research Sessions
  async createResearchSession(data: any) {
    const res = await fetch(`${API_BASE}/research/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to create research session');
    }
    return res.json();
  },

  async listResearchSessions(limit = 20, offset = 0) {
    const res = await fetch(`${API_BASE}/research/sessions?limit=${limit}&offset=${offset}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to list research sessions');
    return res.json();
  },

  async getResearchSession(sessionId: string) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Research session not found');
    return res.json();
  },

  async updateResearchSession(sessionId: string, data: any) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update research session');
    return res.json();
  },

  async deleteResearchSession(sessionId: string) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to delete research session');
  },

  async linkDocumentToSession(sessionId: string, documentId: string) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}/document/${documentId}`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to link document to session');
    return res.json();
  },

  // Research Questions
  async planResearchQuestions(sessionId: string) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}/plan`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to plan research questions');
    return res.json();
  },

  async updateResearchQuestions(sessionId: string, questions: Array<{ question_text: string }>) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}/questions`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ questions }),
    });
    if (!res.ok) throw new Error('Failed to update research questions');
    return res.json();
  },

  // Run Research
  async runResearch(sessionId: string, wait = false) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}/run?wait=${wait}`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to run research');
    return res.json();
  },

  // Research Sources
  async listResearchSources(sessionId: string, selectedOnly = false) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}/sources?selected_only=${selectedOnly}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to list research sources');
    return res.json();
  },

  async getResearchSource(sourceId: string) {
    const res = await fetch(`${API_BASE}/research/sources/${sourceId}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Source not found');
    return res.json();
  },

  async updateResearchSource(sourceId: string, data: { selected: boolean }) {
    const res = await fetch(`${API_BASE}/research/sources/${sourceId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update source');
    return res.json();
  },

  // Research Evidence
  async listResearchEvidence(sessionId: string, selectedOnly = false) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}/evidence?selected_only=${selectedOnly}`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to list research evidence');
    return res.json();
  },

  async createResearchEvidence(sessionId: string, data: any) {
    const res = await fetch(`${API_BASE}/research/sessions/${sessionId}/evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to create evidence');
    }
    return res.json();
  },

  async updateResearchEvidence(evidenceId: string, data: any) {
    const res = await fetch(`${API_BASE}/research/evidence/${evidenceId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update evidence');
    return res.json();
  },

  async deleteResearchEvidence(evidenceId: string) {
    const res = await fetch(`${API_BASE}/research/evidence/${evidenceId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to delete evidence');
  },

  // Citations
  async getDocumentCitations(documentId: string, style?: string) {
    const url = style
      ? `${API_BASE}/documents/${documentId}/citations?style=${style}`
      : `${API_BASE}/documents/${documentId}/citations`;
    const res = await fetch(url, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to get citations');
    return res.json();
  },

  async changeCitationStyle(documentId: string, style: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/citation-style`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ style }),
    });
    if (!res.ok) throw new Error('Failed to change citation style');
    return res.json();
  },

  async deleteCitation(citationId: string) {
    const res = await fetch(`${API_BASE}/citations/${citationId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to delete citation');
  },

  // Verification
  async verifyDocument(documentId: string, data?: any) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data || {}),
    });
    if (!res.ok) throw new Error('Failed to verify document');
    return res.json();
  },

  async getDocumentVerifications(documentId: string, statusFilter?: string) {
    const url = statusFilter
      ? `${API_BASE}/documents/${documentId}/verifications?status=${statusFilter}`
      : `${API_BASE}/documents/${documentId}/verifications`;
    const res = await fetch(url, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to get verifications');
    return res.json();
  },

  async updateVerification(verificationId: string, data: any) {
    const res = await fetch(`${API_BASE}/verifications/${verificationId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update verification');
    return res.json();
  },

  async recheckVerification(verificationId: string) {
    const res = await fetch(`${API_BASE}/verifications/${verificationId}/recheck`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to recheck verification');
    return res.json();
  },

  async getVerificationStatusLabels() {
    const res = await fetch(`${API_BASE}/research/status-labels`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to get status labels');
    return res.json();
  },

  // ---------------------------------------------------------------------
  // Phase 6: review, editing, compliance, versions
  // ---------------------------------------------------------------------

  async startReview(documentId: string, data: { mode: string; categories?: string[]; scope?: string; section_id?: string; use_ai?: boolean }) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to start review');
    }
    return res.json();
  },

  async getLatestReview(documentId: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/reviews/latest`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to load review');
    return res.json();
  },

  async getReview(reviewId: string) {
    const res = await fetch(`${API_BASE}/reviews/${reviewId}`, { credentials: 'include' });
    if (!res.ok) throw new Error('Failed to load review');
    return res.json();
  },

  async updateFinding(findingId: string, status: string) {
    const res = await fetch(`${API_BASE}/findings/${findingId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ status }),
    });
    if (!res.ok) throw new Error('Failed to update finding');
    return res.json();
  },

  async proposeEdit(documentId: string, data: { operation: string; target_type?: string; section_id?: string; block_id?: string; instruction?: string }) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/edit-proposals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to generate suggestion');
    }
    return res.json();
  },

  async applyProposal(proposalId: string, expectedFingerprint?: string) {
    const res = await fetch(`${API_BASE}/edit-proposals/${proposalId}/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ expected_fingerprint: expectedFingerprint ?? null }),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      const failure = new Error(error.detail || 'Failed to apply edit') as Error & { status?: number };
      failure.status = res.status;
      throw failure;
    }
    return res.json();
  },

  async rejectProposal(proposalId: string) {
    const res = await fetch(`${API_BASE}/edit-proposals/${proposalId}/reject`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to reject edit');
    return res.json();
  },

  async checkCompliance(documentId: string, useAi = true) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/compliance?use_ai=${useAi}`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to check compliance');
    return res.json();
  },

  async getLatestCompliance(documentId: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/compliance`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to load compliance');
    return res.json();
  },

  async getVersionHistory(documentId: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/version-history`, {
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to load version history');
    return res.json();
  },

  async compareVersions(documentId: string, fromVersion: number, toVersion: number) {
    const res = await fetch(
      `${API_BASE}/documents/${documentId}/version-compare?from_version=${fromVersion}&to_version=${toVersion}`,
      { credentials: 'include' },
    );
    if (!res.ok) throw new Error('Failed to compare versions');
    return res.json();
  },

  // Phase 6 restore: snapshots the current text as a new version first, so the
  // restore itself can be undone. The older `restoreVersion` above targets a
  // different endpoint that overwrites the document without saving it; keep
  // using this one for anything user-facing.
  async restoreVersionSnapshot(documentId: string, versionNumber: number) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/version-restore/${versionNumber}`, {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to restore version');
    return res.json();
  },
};
