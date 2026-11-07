import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import {
  Citation,
  ReferenceListResponse,
  CitationStyle,
  CITATION_STYLE_LABELS,
} from '../../types/research';

interface CitationManagerProps {
  documentId: string;
  citationStyle: CitationStyle;
  onInsert?: (citationText: string) => void;
}

export default function CitationManager({
  documentId,
  citationStyle,
  onInsert,
}: CitationManagerProps) {
  const [references, setReferences] = useState<ReferenceListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [changingStyle, setChangingStyle] = useState(false);

  useEffect(() => {
    loadCitations();
  }, [documentId, citationStyle]);

  const loadCitations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getDocumentCitations(documentId, citationStyle);
      setReferences(response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStyleChange = async (newStyle: CitationStyle) => {
    setChangingStyle(true);
    setError(null);
    try {
      await api.changeCitationStyle(documentId, newStyle);
      await loadCitations();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setChangingStyle(false);
    }
  };

  const handleInsertCitation = (citation: Citation) => {
    if (onInsert) {
      onInsert(citation.in_text_format);
    }
  };

  const handleDeleteCitation = async (citationId: string) => {
    if (!confirm('Remove this citation? The source will remain in the research session.')) return;
    try {
      await api.deleteCitation(citationId);
      await loadCitations();
    } catch (err: any) {
      alert(`Failed to delete citation: ${err.message}`);
    }
  };

  if (loading && !references) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-4">
      {/* Citation Style Selector */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Citation Style
        </label>
        <select
          value={references?.citation_style || citationStyle}
          onChange={(e) => handleStyleChange(e.target.value as CitationStyle)}
          disabled={changingStyle}
          className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {Object.entries(CITATION_STYLE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        {changingStyle && (
          <p className="text-xs text-gray-500 mt-1">Updating citations...</p>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Integrity Findings */}
      {references && references.integrity_findings.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <h4 className="text-sm font-medium text-yellow-900 mb-2">
            Citation Issues Found
          </h4>
          <ul className="space-y-1">
            {references.integrity_findings.map((finding, index) => (
              <li key={index} className="text-xs text-yellow-800">
                • {finding.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Citations List */}
      {references && references.citations.length > 0 ? (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              In-Text Citations ({references.citations.length})
            </h3>
            <div className="space-y-2">
              {references.citations.map((citation) => (
                <div
                  key={citation.id}
                  className="p-3 bg-gray-50 border border-gray-200 rounded"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <code className="text-sm text-gray-900 font-mono">
                        {citation.in_text_format}
                      </code>
                      <p className="text-xs text-gray-600 mt-1">
                        Key: <span className="font-medium">{citation.citation_key}</span>
                      </p>
                    </div>
                    <div className="flex gap-1 ml-3">
                      {onInsert && (
                        <button
                          onClick={() => handleInsertCitation(citation)}
                          className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded hover:bg-blue-200 transition-colors"
                          title="Insert into document"
                        >
                          Insert
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteCitation(citation.id)}
                        className="px-2 py-1 text-xs font-medium text-red-700 bg-red-100 rounded hover:bg-red-200 transition-colors"
                        title="Remove citation"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              Reference List
            </h3>
            <div className="p-4 bg-gray-50 border border-gray-200 rounded">
              {references.reference_list.length === 0 ? (
                <p className="text-sm text-gray-500 italic">
                  No references yet. Citations will appear here once sources are linked.
                </p>
              ) : (
                <div className="space-y-3">
                  {references.reference_list.map((reference, index) => (
                    <div
                      key={index}
                      className="pb-3 border-b border-gray-200 last:border-0 last:pb-0"
                    >
                      <p className="text-sm text-gray-900 leading-relaxed">
                        {reference}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded border-2 border-dashed border-gray-300">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-white border border-gray-200 mb-3">
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
          <p className="text-sm text-gray-500">No citations yet</p>
          <p className="text-xs text-gray-400 mt-1">
            Complete research and link sources to generate citations
          </p>
        </div>
      )}
    </div>
  );
}
