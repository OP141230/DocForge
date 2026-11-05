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
  async createMessage(conversationId: string, role: 'user' | 'assistant', content: string) {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ role, content }),
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
};
