import { useState, useEffect } from 'react';
import { api } from '../../api/client';
import {
  VerificationReport,
  VerificationStatus,
  VERIFICATION_STATUS_LABELS,
  VERIFICATION_STATUS_COLORS,
} from '../../types/research';

interface VerificationPanelProps {
  documentId: string;
  sessionId?: string;
}

export default function VerificationPanel({ documentId, sessionId }: VerificationPanelProps) {
  const [report, setReport] = useState<VerificationReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<VerificationStatus | ''>('');

  useEffect(() => {
    loadVerifications();
  }, [documentId, statusFilter]);

  const loadVerifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getDocumentVerifications(
        documentId,
        statusFilter || undefined
      );
      setReport(response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyDocument = async () => {
    setVerifying(true);
    setError(null);
    try {
      const response = await api.verifyDocument(documentId, {
        research_session_id: sessionId || null,
      });
      setReport(response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setVerifying(false);
    }
  };

  const handleFlagForReview = async (verificationId: string, flagged: boolean) => {
    try {
      await api.updateVerification(verificationId, { flagged_for_review: flagged });
      await loadVerifications();
    } catch (err: any) {
      alert(`Failed to update: ${err.message}`);
    }
  };

  const handleMarkReviewed = async (verificationId: string, notes: string) => {
    try {
      await api.updateVerification(verificationId, {
        reviewed: true,
        reviewer_notes: notes || null,
      });
      await loadVerifications();
    } catch (err: any) {
      alert(`Failed to mark as reviewed: ${err.message}`);
    }
  };

  const handleRecheck = async (verificationId: string) => {
    try {
      await api.recheckVerification(verificationId);
      await loadVerifications();
    } catch (err: any) {
      alert(`Failed to recheck: ${err.message}`);
    }
  };

  const getStatusIcon = (status: VerificationStatus) => {
    const icons = {
      [VerificationStatus.SUPPORTED]: '✓',
      [VerificationStatus.CONTRADICTED]: '✗',
      [VerificationStatus.INSUFFICIENT_EVIDENCE]: '?',
      [VerificationStatus.NOT_CHECKED]: '○',
    };
    return icons[status];
  };

  const getSummaryStats = () => {
    if (!report) return null;
    return [
      { label: 'Total Claims', value: report.total_claims, color: 'text-gray-600' },
      { label: 'Supported', value: report.supported, color: 'text-green-600' },
      { label: 'Contradicted', value: report.contradicted, color: 'text-red-600' },
      { label: 'Insufficient', value: report.insufficient_evidence, color: 'text-yellow-600' },
      { label: 'Not Checked', value: report.not_checked, color: 'text-gray-400' },
    ];
  };

  if (loading && !report) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium text-gray-700">Factual Verification</h3>
          <p className="text-xs text-gray-500 mt-1">
            Check claims against research evidence
          </p>
        </div>
        <button
          onClick={handleVerifyDocument}
          disabled={verifying}
          className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {verifying ? 'Verifying...' : 'Verify Document'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Summary Stats */}
      {report && (
        <div className="mb-4 grid grid-cols-5 gap-2">
          {getSummaryStats()?.map((stat) => (
            <div key={stat.label} className="p-3 bg-gray-50 border border-gray-200 rounded text-center">
              <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
              <div className="text-xs text-gray-600 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Status Filter */}
      {report && report.verifications.length > 0 && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as VerificationStatus | '')}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            {Object.entries(VERIFICATION_STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Verifications List */}
      {report && report.verifications.length > 0 ? (
        <div className="space-y-3">
          {report.verifications.map((verification) => (
            <div
              key={verification.id}
              className={`p-4 border-2 rounded ${
                verification.flagged_for_review
                  ? 'border-orange-300 bg-orange-50'
                  : verification.reviewed
                  ? 'border-green-300 bg-green-50'
                  : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded text-sm font-medium border ${
                      VERIFICATION_STATUS_COLORS[verification.verification_status]
                    }`}
                  >
                    {getStatusIcon(verification.verification_status)}{' '}
                    {VERIFICATION_STATUS_LABELS[verification.verification_status]}
                  </span>
                  {verification.flagged_for_review && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                      🚩 Flagged
                    </span>
                  )}
                  {verification.reviewed && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      ✓ Reviewed
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  Confidence: {Math.round(verification.confidence_score * 100)}%
                </span>
              </div>

              <blockquote className="text-sm text-gray-900 font-medium mb-2 border-l-4 border-gray-300 pl-3">
                "{verification.claim_text}"
              </blockquote>

              <p className="text-xs text-gray-700 mb-3">
                {verification.explanation}
              </p>

              {verification.reviewer_notes && (
                <div className="mb-3 p-2 bg-white border border-gray-200 rounded">
                  <p className="text-xs font-medium text-gray-700 mb-1">Reviewer Notes:</p>
                  <p className="text-xs text-gray-600">{verification.reviewer_notes}</p>
                </div>
              )}

              <div className="flex gap-2">
                {!verification.flagged_for_review && (
                  <button
                    onClick={() => handleFlagForReview(verification.id, true)}
                    className="px-2 py-1 text-xs font-medium text-orange-700 bg-orange-100 rounded hover:bg-orange-200 transition-colors"
                  >
                    🚩 Flag for Review
                  </button>
                )}
                {verification.flagged_for_review && !verification.reviewed && (
                  <button
                    onClick={() => {
                      const notes = prompt('Add review notes (optional):');
                      if (notes !== null) {
                        handleMarkReviewed(verification.id, notes);
                      }
                    }}
                    className="px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded hover:bg-green-200 transition-colors"
                  >
                    ✓ Mark Reviewed
                  </button>
                )}
                <button
                  onClick={() => handleRecheck(verification.id)}
                  className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded hover:bg-blue-200 transition-colors"
                >
                  ↻ Recheck
                </button>
                {verification.flagged_for_review && (
                  <button
                    onClick={() => handleFlagForReview(verification.id, false)}
                    className="px-2 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
                  >
                    Unflag
                  </button>
                )}
              </div>
            </div>
          ))}
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
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p className="text-sm text-gray-500">No verifications yet</p>
          <p className="text-xs text-gray-400 mt-1">
            Click "Verify Document" to check factual claims
          </p>
        </div>
      )}
    </div>
  );
}
