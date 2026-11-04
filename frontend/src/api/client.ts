// API client functions
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export const api = {
  // Health
  async health() {
    const res = await fetch('/health');
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  // Documents
  async createDocument(document: any) {
    const res = await fetch(`${API_BASE}/documents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(document),
    });
    if (!res.ok) throw new Error('Failed to create document');
    return res.json();
  },

  async listDocuments(limit = 20, offset = 0) {
    const res = await fetch(`${API_BASE}/documents?limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error('Failed to list documents');
    return res.json();
  },

  async getDocument(id: string) {
    const res = await fetch(`${API_BASE}/documents/${id}`);
    if (!res.ok) throw new Error('Document not found');
    return res.json();
  },

  async updateDocument(id: string, document: any) {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(document),
    });
    if (!res.ok) throw new Error('Failed to update document');
    return res.json();
  },

  async deleteDocument(id: string) {
    const res = await fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete document');
  },

  // Generation
  async generateOutline(requirements: any) {
    const res = await fetch(`${API_BASE}/generate/outline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requirements),
    });
    if (!res.ok) throw new Error('Failed to generate outline');
    return res.json();
  },

  async generateContent(outline: any, requirements: any) {
    const res = await fetch(`${API_BASE}/generate/content`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ outline, requirements }),
    });
    if (!res.ok) throw new Error('Failed to generate content');
    return res.json();
  },

  async generateSection(section_title: string, context: any, instruction: string) {
    const res = await fetch(`${API_BASE}/generate/section`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ section_title, context, instruction }),
    });
    if (!res.ok) throw new Error('Failed to generate section');
    return res.json();
  },

  // Versions
  async createVersion(documentId: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/versions`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to create version');
    return res.json();
  },

  async listVersions(documentId: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/versions`);
    if (!res.ok) throw new Error('Failed to list versions');
    return res.json();
  },

  async restoreVersion(documentId: string, versionNumber: number) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/versions/${versionNumber}/restore`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to restore version');
    return res.json();
  },

  // Export
  async exportDocument(documentId: string, format: string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/export?format=${format}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to export document');
    const blob = await res.blob();
    const contentDisposition = res.headers.get('Content-Disposition');
    const filename = contentDisposition?.match(/filename="?([^"]+)"?/)?.[1] || `document.${format}`;
    return { blob, filename };
  },
};
