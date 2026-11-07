import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import {
  ResearchSessionDetail,
  ResearchStatus,
  RESEARCH_STATUS_LABELS,
  CitationStyle,
  CITATION_STYLE_LABELS,
  ResearchProviderInfo,
} from '../../types/research';
import ResearchSessionList from './ResearchSessionList';
import ResearchQuestionEditor from './ResearchQuestionEditor';
import ResearchResults from './ResearchResults';
import CitationManager from './CitationManager';

interface ResearchPanelProps {
  documentId?: string;
  briefId?: string;
  onCitationInsert?: (citationText: string) => void;
}

export default function ResearchPanel({ documentId, briefId, onCitationInsert }: ResearchPanelProps) {
  const [activeSession, setActiveSession] = useState<ResearchSessionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [providerInfo, setProviderInfo] = useState<ResearchProviderInfo | null>(null);
  const [activeTab, setActiveTab] = useState<'sessions' | 'questions' | 'results' | 'citations'>('sessions');

  useEffect(() => {
    loadProviderInfo();
  }, []);

  useEffect(() => {
    // Auto-refresh session status if research is running
    if (activeSession?.session.status === ResearchStatus.RUNNING) {
      const interval = setInterval(() => {
        refreshActiveSession();
      }, 3000); // Poll every 3 seconds
      return () => clearInterval(interval);
    }
  }, [activeSession?.session.status]);

  const loadProviderInfo = async () => {
    try {
      const info = await api.getResearchProviders();
      setProviderInfo(info);
    } catch (err: any) {
      console.error('Failed to load provider info:', err);
    }
  };

  const refreshActiveSession = async () => {
    if (!activeSession) return;
    try {
      const updated = await api.getResearchSession(activeSession.session.id);
      setActiveSession(updated);
    } catch (err: any) {
      console.error('Failed to refresh session:', err);
    }
  };

  const handleSessionSelect = async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const session = await api.getResearchSession(sessionId);
      setActiveSession(session);
      setActiveTab('questions'); // Move to questions tab when session selected
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (title: string, citationStyle: CitationStyle) => {
    setLoading(true);
    setError(null);
    try {
      const session = await api.createResearchSession({
        title,
        document_id: documentId,
        brief_id: briefId,
        citation_style: citationStyle,
        external_research: true,
        include_knowledge_base: true,
        urls: [],
        knowledge_file_ids: [],
      });
      setActiveSession(session);
      setActiveTab('questions');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunResearch = async () => {
    if (!activeSession) return;
    setLoading(true);
    setError(null);
    try {
      await api.runResearch(activeSession.session.id);
      // Start polling for updates
      await refreshActiveSession();
      setActiveTab('results');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Research & Citations</h2>
        {providerInfo && (
          <p className="text-xs text-gray-500 mt-1">
            {Object.values(providerInfo.provider).filter(Boolean).length} providers available
          </p>
        )}
      </div>

      {/* Tab Navigation */}
      {activeSession && (
        <div className="flex-shrink-0 flex space-x-1 px-4 py-2 border-b border-gray-200 bg-gray-50">
          <button
            onClick={() => setActiveTab('sessions')}
            className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
              activeTab === 'sessions'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Sessions
          </button>
          <button
            onClick={() => setActiveTab('questions')}
            className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
              activeTab === 'questions'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Questions
            {activeSession.questions.length > 0 && (
              <span className="ml-1 text-xs">({activeSession.questions.length})</span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('results')}
            className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
              activeTab === 'results'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            disabled={activeSession.session.status === ResearchStatus.DRAFT}
          >
            Results
            {activeSession.evidence_count > 0 && (
              <span className="ml-1 text-xs">({activeSession.evidence_count})</span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('citations')}
            className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
              activeTab === 'citations'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            disabled={!documentId}
          >
            Citations
          </button>
        </div>
      )}

      {/* Status Bar */}
      {activeSession && (
        <div className="flex-shrink-0 px-4 py-2 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">{activeSession.session.title}</p>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    activeSession.session.status === ResearchStatus.COMPLETED
                      ? 'bg-green-100 text-green-800'
                      : activeSession.session.status === ResearchStatus.RUNNING
                      ? 'bg-blue-100 text-blue-800'
                      : activeSession.session.status === ResearchStatus.FAILED
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {RESEARCH_STATUS_LABELS[activeSession.session.status]}
                </span>
                <span className="text-xs text-gray-500">
                  {CITATION_STYLE_LABELS[activeSession.session.citation_style]} style
                </span>
              </div>
            </div>
            {activeSession.session.status === ResearchStatus.DRAFT && (
              <button
                onClick={handleRunResearch}
                disabled={loading || activeSession.questions.length === 0}
                className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Run Research
              </button>
            )}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="flex-shrink-0 mx-4 mt-3 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto">
        {!activeSession ? (
          <ResearchSessionList
            documentId={documentId}
            briefId={briefId}
            onSessionSelect={handleSessionSelect}
            onCreateSession={handleCreateSession}
            loading={loading}
          />
        ) : (
          <>
            {activeTab === 'sessions' && (
              <ResearchSessionList
                documentId={documentId}
                briefId={briefId}
                onSessionSelect={handleSessionSelect}
                onCreateSession={handleCreateSession}
                loading={loading}
              />
            )}
            {activeTab === 'questions' && (
              <ResearchQuestionEditor
                session={activeSession}
                onUpdate={refreshActiveSession}
              />
            )}
            {activeTab === 'results' && (
              <ResearchResults
                session={activeSession}
                onUpdate={refreshActiveSession}
              />
            )}
            {activeTab === 'citations' && documentId && (
              <CitationManager
                documentId={documentId}
                citationStyle={activeSession.session.citation_style}
                onInsert={onCitationInsert}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
