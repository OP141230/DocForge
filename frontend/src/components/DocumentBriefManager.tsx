import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Trash2, Eye, Plus, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import { DocumentBrief } from '../types/document_brief';
import { DocumentBriefWizard } from './DocumentBrief/DocumentBriefWizard';
import ConfirmDialog from './ConfirmDialog';
import {
  DOCUMENT_TYPE_LABELS,
  DocumentType,
} from '../types/document';

export default function DocumentBriefManager() {
  const [briefs, setBriefs] = useState<DocumentBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const [editingBriefId, setEditingBriefId] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [briefToDelete, setBriefToDelete] = useState<string | null>(null);
  const [generatingBriefId, setGeneratingBriefId] = useState<string | null>(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    loadBriefs();
  }, []);

  const loadBriefs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listBriefs();
      setBriefs(data.briefs || []);
    } catch (err: any) {
      console.error('Failed to load briefs:', err);
      setError(err.message || 'Failed to load document briefs');
    } finally {
      setLoading(false);
    }
  };

  const handleNewBrief = () => {
    setEditingBriefId(null);
    setShowWizard(true);
  };

  const handleViewEdit = (briefId: string) => {
    setEditingBriefId(briefId);
    setShowWizard(true);
  };

  const handleDeleteClick = (briefId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setBriefToDelete(briefId);
    setShowDeleteDialog(true);
  };

  const confirmDelete = async () => {
    if (!briefToDelete) return;
    
    try {
      await api.deleteBrief(briefToDelete);
      setBriefs(briefs.filter(b => b.id !== briefToDelete));
      setShowDeleteDialog(false);
      setBriefToDelete(null);
    } catch (err: any) {
      console.error('Failed to delete brief:', err);
      setError(err.message || 'Failed to delete brief');
      setShowDeleteDialog(false);
    }
  };

  const handleGenerateDocument = async (briefId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    try {
      setGeneratingBriefId(briefId);
      const result = await api.generateFromBrief(briefId);
      
      // Navigate to the generated document
      if (result.document_id) {
        navigate(`/document/${result.document_id}`);
      }
    } catch (err: any) {
      console.error('Failed to generate document:', err);
      setError(err.message || 'Failed to generate document');
    } finally {
      setGeneratingBriefId(null);
    }
  };

  const handleWizardComplete = async (brief: DocumentBrief) => {
    setShowWizard(false);
    setEditingBriefId(null);
    
    // If the brief has a generated document, navigate to it
    if (brief.document_id) {
      navigate(`/document/${brief.document_id}`);
    } else {
      // Otherwise, reload briefs to show the updated list
      await loadBriefs();
    }
  };

  const handleWizardCancel = () => {
    setShowWizard(false);
    setEditingBriefId(null);
  };

  const getStatusBadge = (brief: DocumentBrief) => {
    if (brief.document_id) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          Generated
        </span>
      );
    }
    if (brief.outline_approved) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          Outline Approved
        </span>
      );
    }
    if (brief.outline && brief.outline.length > 0) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          Outline Ready
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        Draft
      </span>
    );
  };

  const canGenerate = (brief: DocumentBrief): boolean => {
    return brief.outline_approved && !brief.document_id;
  };

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Document Briefs</h1>
              <p className="text-lg text-gray-600">Plan and manage your document generation</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-white rounded-md transition-colors"
              >
                ← Back to Dashboard
              </button>
              <button
                onClick={handleNewBrief}
                className="btn-primary text-lg px-6 py-3 shadow-lg hover:shadow-xl flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
                New Document Brief
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="text-red-700 hover:text-red-900 font-semibold"
              >
                ✕
              </button>
            </div>
          )}

          {/* Content */}
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading briefs...</p>
            </div>
          ) : briefs.length === 0 ? (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <div className="text-6xl mb-4">📋</div>
              <h2 className="text-2xl font-semibold text-gray-700 mb-2">No document briefs yet</h2>
              <p className="text-gray-500 mb-6">
                Create a document brief to plan your document with a structured wizard
              </p>
              <button onClick={handleNewBrief} className="btn-primary">
                Create Your First Brief
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {briefs.map((brief) => (
                <div
                  key={brief.id}
                  className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-all duration-200 relative group"
                >
                  {/* Status Badge */}
                  <div className="absolute top-4 right-4">
                    {getStatusBadge(brief)}
                  </div>

                  {/* Content */}
                  <div className="mb-4 pr-24">
                    <h3 className="text-xl font-semibold text-gray-900 mb-2 line-clamp-2">
                      {brief.title}
                    </h3>
                    <p className="text-sm text-gray-500 mb-2">
                      {DOCUMENT_TYPE_LABELS[brief.document_type as DocumentType] || brief.document_type}
                    </p>
                    <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                      {brief.topic}
                    </p>
                    <p className="text-xs text-gray-400">
                      Created {new Date(brief.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => handleViewEdit(brief.id)}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-700 hover:bg-blue-50 rounded-md transition-colors"
                      title="View/Edit Brief"
                    >
                      <Eye className="w-4 h-4" />
                      View/Edit
                    </button>

                    {canGenerate(brief) && (
                      <button
                        onClick={(e) => handleGenerateDocument(brief.id, e)}
                        disabled={generatingBriefId === brief.id}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Generate Document"
                      >
                        {generatingBriefId === brief.id ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <FileText className="w-4 h-4" />
                            Generate
                          </>
                        )}
                      </button>
                    )}

                    {brief.document_id && (
                      <button
                        onClick={() => navigate(`/document/${brief.document_id}`)}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
                        title="View Generated Document"
                      >
                        <FileText className="w-4 h-4" />
                        View Doc
                      </button>
                    )}

                    <button
                      onClick={(e) => handleDeleteClick(brief.id, e)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      title="Delete Brief"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Wizard Modal */}
      {showWizard && (
        <DocumentBriefWizard
          onComplete={handleWizardComplete}
          onCancel={handleWizardCancel}
          existingBriefId={editingBriefId || undefined}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        title="Delete Document Brief"
        message="Are you sure you want to delete this document brief? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={confirmDelete}
        onCancel={() => {
          setShowDeleteDialog(false);
          setBriefToDelete(null);
        }}
      />
    </>
  );
}
