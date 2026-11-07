import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import {
  ResearchSessionDetail,
  ResearchSource,
  EvidenceRecord,
  SOURCE_TYPE_LABELS,
  EVIDENCE_TYPE_LABELS,
  SourceType,
} from '../../types/research';

interface ResearchResultsProps {
  session: ResearchSessionDetail;
  onUpdate: () => void;
}

export default function ResearchResults({ session, onUpdate }: ResearchResultsProps) {
  const [sources, setSources] = useState<ResearchSource[]>([]);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'sources' | 'evidence'>('sources');

  useEffect(() => {
    loadResults();
  }, [session.session.id]);

  const loadResults = async () => {
    setLoading(true);
    try {
      const [sourcesResponse, evidenceResponse] = await Promise.all([
        api.listResearchSources(session.session.id),
        api.listResearchEvidence(session.session.id),
      ]);
      setSources(sourcesResponse.sources);
      setEvidence(evidenceResponse.evidence);
    } catch (err: any) {
      console.error('Failed to load results:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSourceSelection = async (source: ResearchSource) => {
    try {
      await api.updateResearchSource(source.id, { selected: !source.selected });
      await loadResults();
      onUpdate();
    } catch (err: any) {
      console.error('Failed to toggle source:', err);
    }
  };

  const handleToggleEvidenceSelection = async (evidenceItem: EvidenceRecord) => {
    try {
      await api.updateResearchEvidence(evidenceItem.id, { selected: !evidenceItem.selected });
      await loadResults();
      onUpdate();
    } catch (err: any) {
      console.error('Failed to toggle evidence:', err);
    }
  };

  const getSourceIcon = (sourceType: SourceType) => {
    const icons: Record<SourceType, string> = {
      [SourceType.WIKIPEDIA]: '📖',
      [SourceType.ARXIV]: '📄',
      [SourceType.PUBMED]: '🏥',
      [SourceType.GOOGLE_SCHOLAR]: '🎓',
      [SourceType.WEB_SEARCH]: '🌐',
      [SourceType.USER_PROVIDED_URL]: '🔗',
      [SourceType.KNOWLEDGE_BASE]: '📚',
    };
    return icons[sourceType] || '📄';
  };

  if (loading && sources.length === 0 && evidence.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Tab Navigation */}
      <div className="flex-shrink-0 flex space-x-1 px-4 py-2 border-b border-gray-200 bg-gray-50">
        <button
          onClick={() => setActiveTab('sources')}
          className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
            activeTab === 'sources'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Sources ({sources.length})
        </button>
        <button
          onClick={() => setActiveTab('evidence')}
          className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
            activeTab === 'evidence'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Evidence ({evidence.length})
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'sources' && (
          <>
            {sources.length === 0 ? (
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
                      d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                    />
                  </svg>
                </div>
                <p className="text-sm text-gray-500">No sources found yet</p>
                <p className="text-xs text-gray-400 mt-1">Run research to discover sources</p>
              </div>
            ) : (
              <div className="space-y-3">
                {sources.map((source) => (
                  <div
                    key={source.id}
                    className={`p-4 border rounded transition-colors ${
                      source.selected
                        ? 'border-blue-300 bg-blue-50'
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 text-2xl">
                        {getSourceIcon(source.source_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="text-sm font-medium text-gray-900 line-clamp-2">
                              {source.title}
                            </h4>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                                {SOURCE_TYPE_LABELS[source.source_type]}
                              </span>
                              {source.selected && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                  ✓ Selected
                                </span>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => handleToggleSourceSelection(source)}
                            className={`ml-3 px-3 py-1 text-xs font-medium rounded transition-colors ${
                              source.selected
                                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                            }`}
                          >
                            {source.selected ? 'Exclude' : 'Include'}
                          </button>
                        </div>

                        {source.authors && source.authors.length > 0 && (
                          <p className="text-xs text-gray-600 mt-2">
                            <span className="font-medium">Authors:</span> {source.authors.join(', ')}
                          </p>
                        )}

                        {source.publication_date && (
                          <p className="text-xs text-gray-600 mt-1">
                            <span className="font-medium">Published:</span>{' '}
                            {new Date(source.publication_date).toLocaleDateString()}
                          </p>
                        )}

                        {source.abstract_or_summary && (
                          <p className="text-xs text-gray-700 mt-2 line-clamp-3">
                            {source.abstract_or_summary}
                          </p>
                        )}

                        {source.url && (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline mt-2 inline-flex items-center gap-1"
                          >
                            View source
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                              />
                            </svg>
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'evidence' && (
          <>
            {evidence.length === 0 ? (
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
                <p className="text-sm text-gray-500">No evidence collected yet</p>
                <p className="text-xs text-gray-400 mt-1">Evidence will appear after research completes</p>
              </div>
            ) : (
              <div className="space-y-3">
                {evidence.map((item) => (
                  <div
                    key={item.id}
                    className={`p-4 border rounded transition-colors ${
                      item.selected
                        ? 'border-blue-300 bg-blue-50'
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700">
                          {EVIDENCE_TYPE_LABELS[item.evidence_type]}
                        </span>
                        {item.selected && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                            ✓ Selected
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => handleToggleEvidenceSelection(item)}
                        className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                          item.selected
                            ? 'bg-red-100 text-red-700 hover:bg-red-200'
                            : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                        }`}
                      >
                        {item.selected ? 'Exclude' : 'Include'}
                      </button>
                    </div>

                    <p className="text-sm font-medium text-gray-900 mb-2">
                      {item.claim_or_finding}
                    </p>

                    <blockquote className="text-xs text-gray-700 italic border-l-4 border-gray-300 pl-3 py-1 my-2">
                      "{item.passage}"
                    </blockquote>

                    {item.page_number && (
                      <p className="text-xs text-gray-600 mt-2">
                        <span className="font-medium">Page:</span> {item.page_number}
                      </p>
                    )}

                    {item.section_title && (
                      <p className="text-xs text-gray-600 mt-1">
                        <span className="font-medium">Section:</span> {item.section_title}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
