import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { DocumentBrief } from '../types/document_brief';
import { DocumentBriefWizard } from './DocumentBrief/DocumentBriefWizard';
import ConfirmDialog from './ConfirmDialog';
import { ChevronLeft, FileText, Calendar, CheckCircle, Clock, Trash2, Eye, Play } from 'lucide-react';

export default function DocumentBriefManager() {
  const [briefs, setBriefs] = useState<DocumentBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const [editingBriefId, setEditingBriefId] = useState<string | null>(null);
  const [deletingBriefId, setDeletingBriefId] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [generatingBriefId, setGeneratingBriefId] = useState<string | null>(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    loadBriefs();
  }, []);

  const loadBriefs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.listBriefs(100, 0);
      setBriefs(response.briefs || []);
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

  const handleEditBrief = (briefId: string) => {
    setEditingBriefId(briefId);
    setShowWizard(true);
  };

  const handleWizardComplete = async (brief: DocumentBrief) => {
    setShowWizard(false);
    setEditingBriefId(null);
    
    // If document was generated, navigate to it
    if (brief.document_id) {
      navigate(`/document/${brief.document_id}`);
    } else {
      // Otherwise reload the list
      await loadBriefs();
    }
  };

  const handleWizardCancel = () => {
    setShowWizard(false);
    setEditingBriefId(null);
  };

  const handleDeleteBrief = (briefId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingBriefId(briefId);
    setShowDeleteDialog(true);
  };

  const confirmDelete = async () => {
    if (!deletingBriefId) return;

    try {
      await api.deleteBrief(deletingBriefId);
      setBriefs(briefs.filter(b => b.id !== deletingBriefId));
      setShowDeleteDialog(false);
      setDeletingBriefId(null);
    } catch (err: any) {
      console.error('Failed to delete brief:', err);
      setError(err.message || 'Failed to delete brief');
      setShowDeleteDialog(false);
    }
  };

  const handleGenerateDocument = async (briefId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    const brief = briefs.find(b => b.id === briefId);
    if (!brief?.outline_approved) {
      setError('Please complete and approve the outline before generating the document');
      return;
    }

    try {
      setGeneratingBriefId(briefId);
      setError(null);
      const result = await api.generateFromBrief(briefId);
      
      // Navigate to the generated document
      if (result.document_id) {
        navigate(`/document/${result.document_id}`);
      } else {
        setError('Document generated but no document ID returned');
      }
    } catch (err: any) {
      console.error('Failed to generate document:', err);
      setError(err.message || 'Failed to generate document from brief');
    } finally {
      setGeneratingBriefId(null);
    }
  };

  const handleViewDocument = (documentId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/document/${documentId}`);
  };

  const getBriefStatus = (brief: DocumentBrief): { label: string; color: string; icon: React.ReactNode } => {
    if (brief.document_id) {
      return {
        label: 'Generated',
        color: 'bg-green-100 text-green-800',
        icon: <CheckCircle className="w-4 h-4" />
      };
    }
    if (brief.outline_approved) {
      return {
        label: 'Outline Approved',
        color: 'bg-blue-100 text-blue-800',
        icon: <CheckCircle className="w-4 h-4" />
      };
    }
    if (brief.outline && brief.outline.length > 0) {
      return {
        label: 'Outline Created',
        color: 'bg-yellow-100 text-yellow-800',
        icon: <Clock className="w-4 h-4" />
      };
    }
    return {
      label: 'Draft',
      color: 'bg-gray-100 text-gray-800',
      icon: <Clock className="w-4 h-4" />
    };
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
            Back to Dashboard
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">Document Briefs</h1>
              <p className="text-lg text-gray-600">
                Plan and create documents with a structured approach
              </p>
            </div>
            <button
              onClick={handleNewBrief}
              className="btn-primary text-lg px-6 py-3 shadow-lg hover:shadow-xl"
            >
              + New Document Brief
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
              Create your first document brief to start planning structured documents
            </p>
            <button onClick={handleNewBrief} className="btn-primary">
              Create Your First Brief
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {briefs.map((brief) => {
              const status = getBriefStatus(brief);
              const isGenerating = generatingBriefId === brief.id;
              
              return (
                <div
                  key={brief.id}
                  className="bg-white rounded-lg shadow-md hover:shadow-xl transition-all duration-200 overflow-hidden group"
                >
                  {/* Card Header */}
                  <div className="p-6 border-b border-gray-100">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-gray-400" />
                        <span className="text-sm text-gray-500 capitalize">
                          {brief.document_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
                        {status.icon}
                        {status.label}
                      </div>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      {brief.title}
                    </h3>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {brief.topic}
                    </p>
                  </div>

                  {/* Card Body */}
                  <div className="p-6 bg-gray-50">
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                      <Calendar className="w-4 h-4" />
                      <span>Updated {formatDate(brief.updated_at)}</span>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2">
                      {brief.document_id ? (
                        <button
                          onClick={(e) => handleViewDocument(brief.document_id!, e)}
                          className="w-full btn-primary text-sm py-2"
                        >
                          <Eye className="w-4 h-4 inline mr-2" />
                          View Generated Document
                        </button>
                      ) : brief.outline_approved ? (
                        <button
                          onClick={(e) => handleGenerateDocument(brief.id, e)}
                          disabled={isGenerating}
                          className="w-full btn-primary text-sm py-2 disabled:opacity-50"
                        >
                          {isGenerating ? (
                            <>
                              <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Generating...
                            </>
                          ) : (
                            <>
                              <Play className="w-4 h-4 inline mr-2" />
                              Generate Document
                            </>
                          )}
                        </button>
                      ) : (
                        <button
                          onClick={() => handleEditBrief(brief.id)}
                          className="w-full btn-primary text-sm py-2"
                        >
                          <Eye className="w-4 h-4 inline mr-2" />
                          Continue Brief
                        </button>
                      )}
                      
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditBrief(brief.id)}
                          className="flex-1 btn-secondary text-sm py-2"
                        >
                          View/Edit
                        </button>
                        <button
                          onClick={(e) => handleDeleteBrief(brief.id, e)}
                          className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-red-200"
                          title="Delete brief"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
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
        message="Are you sure you want to delete this document brief? This action cannot be undone. If a document was generated from this brief, it will not be affected."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        onConfirm={confirmDelete}
        onCancel={() => {
          setShowDeleteDialog(false);
          setDeletingBriefId(null);
        }}
      />
    </div>
  );
}
