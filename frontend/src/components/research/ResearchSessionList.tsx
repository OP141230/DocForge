import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import {
  ResearchSession,
  ResearchStatus,
  RESEARCH_STATUS_LABELS,
  CitationStyle,
  CITATION_STYLE_LABELS,
} from '../../types/research';

interface ResearchSessionListProps {
  documentId?: string;
  briefId?: string;
  onSessionSelect: (sessionId: string) => void;
  onCreateSession: (title: string, citationStyle: CitationStyle) => void;
  loading: boolean;
}

export default function ResearchSessionList({
  documentId,
  briefId,
  onSessionSelect,
  onCreateSession,
  loading,
}: ResearchSessionListProps) {
  const [sessions, setSessions] = useState<ResearchSession[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newCitationStyle, setNewCitationStyle] = useState<CitationStyle>(CitationStyle.APA);

  useEffect(() => {
    loadSessions();
  }, [documentId, briefId]);

  const loadSessions = async () => {
    setLoadingList(true);
    try {
      const response = await api.listResearchSessions(50, 0);
      let filtered = response.sessions;

      // Filter by document or brief if specified
      if (documentId) {
        filtered = filtered.filter((s: ResearchSession) => s.document_id === documentId);
      } else if (briefId) {
        filtered = filtered.filter((s: ResearchSession) => s.brief_id === briefId);
      }

      setSessions(filtered);
    } catch (err: any) {
      console.error('Failed to load sessions:', err);
    } finally {
      setLoadingList(false);
    }
  };

  const handleCreate = () => {
    if (!newTitle.trim()) return;
    onCreateSession(newTitle.trim(), newCitationStyle);
    setNewTitle('');
    setShowCreateModal(false);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loadingList) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-700">Research Sessions</h3>
        <button
          onClick={() => setShowCreateModal(true)}
          disabled={loading}
          className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          New Session
        </button>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Create Research Session</h3>
            </div>
            <div className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Session Title
                </label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., Climate Change Research"
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Citation Style
                </label>
                <select
                  value={newCitationStyle}
                  onChange={(e) => setNewCitationStyle(e.target.value as CitationStyle)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(CITATION_STYLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewTitle('');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!newTitle.trim()}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sessions List */}
      {sessions.length === 0 ? (
        <div className="text-center py-12">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-100 mb-3">
            <svg
              className="w-6 h-6 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <p className="text-sm text-gray-500">No research sessions yet</p>
          <p className="text-xs text-gray-400 mt-1">Create one to start researching</p>
        </div>
      ) : (
        <div className="space-y-2">
          {sessions.map((session) => (
            <button
              key={session.id}
              onClick={() => onSessionSelect(session.id)}
              className="w-full text-left p-3 border border-gray-200 rounded hover:border-blue-300 hover:bg-blue-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {session.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        session.status === ResearchStatus.COMPLETED
                          ? 'bg-green-100 text-green-800'
                          : session.status === ResearchStatus.RUNNING
                          ? 'bg-blue-100 text-blue-800'
                          : session.status === ResearchStatus.FAILED
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {RESEARCH_STATUS_LABELS[session.status]}
                    </span>
                    <span className="text-xs text-gray-500">
                      {CITATION_STYLE_LABELS[session.citation_style]}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Created {formatDate(session.created_at)}
                  </p>
                </div>
                <svg
                  className="w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
