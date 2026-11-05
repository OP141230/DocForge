import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Edit2, 
  Trash2, 
  FileText, 
  ArrowLeft, 
  Loader2, 
  AlertCircle,
  CheckCircle 
} from 'lucide-react';
import { api } from '../api/client';
import { OutlineViewer } from '../components/OutlineEditor/OutlineViewer';
import { OutlineEditor } from '../components/OutlineEditor/OutlineEditor';
import { DocumentBriefWizard } from '../components/DocumentBrief/DocumentBriefWizard';
import type { DocumentBrief, OutlineItem } from '../types/document_brief';

const LANGUAGE_LABELS: Record<string, string> = {
  en: 'English',
  es: 'Spanish',
  fr: 'French',
  de: 'German',
  zh: 'Chinese',
  ja: 'Japanese',
  ar: 'Arabic',
};

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  technical_documentation: 'Technical Documentation',
  academic_paper: 'Academic Paper',
  essay_article: 'Essay/Article',
  project_report: 'Project Report',
  business_document: 'Business Document',
  resume_cv: 'Resume/CV',
  research_paper: 'Research Paper',
  user_guide: 'User Guide',
  general: 'General Document',
};

export function BriefDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [brief, setBrief] = useState<DocumentBrief | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditingBrief, setIsEditingBrief] = useState(false);
  const [isEditingOutline, setIsEditingOutline] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isGeneratingDocument, setIsGeneratingDocument] = useState(false);

  useEffect(() => {
    if (id) {
      loadBrief(id);
    }
  }, [id]);

  const loadBrief = async (briefId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const data: DocumentBrief = await api.getBrief(briefId);
      setBrief(data);
    } catch (err) {
      console.error('Failed to load brief:', err);
      setError(err instanceof Error ? err.message : 'Failed to load brief');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;

    try {
      setIsDeleting(true);
      await api.deleteBrief(id);
      navigate('/dashboard');
    } catch (err) {
      console.error('Failed to delete brief:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete brief');
      setShowDeleteConfirm(false);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleEditBrief = () => {
    setIsEditingBrief(true);
  };

  const handleBriefUpdateComplete = (updatedBrief: DocumentBrief) => {
    setBrief(updatedBrief);
    setIsEditingBrief(false);
  };

  const handleEditOutline = () => {
    setIsEditingOutline(true);
  };

  const handleSaveOutline = async (updatedOutline: OutlineItem[]) => {
    if (!id) {
      throw new Error('No brief ID available');
    }

    try {
      const updatedBrief: DocumentBrief = await api.updateBriefOutline(id, updatedOutline);
      setBrief(updatedBrief);
      setIsEditingOutline(false);
    } catch (error) {
      console.error('Failed to save outline:', error);
      throw error;
    }
  };

  const handleCancelEditOutline = () => {
    setIsEditingOutline(false);
  };

  const handleApproveOutline = async () => {
    if (!id) return;

    try {
      const updatedBrief: DocumentBrief = await api.approveBriefOutline(id);
      setBrief(updatedBrief);
    } catch (err) {
      console.error('Failed to approve outline:', err);
      setError('Failed to approve outline');
    }
  };

  const handleRegenerateOutline = async () => {
    if (!id) return;

    try {
      const updatedBrief: DocumentBrief = await api.generateBriefOutline(id);
      setBrief(updatedBrief);
    } catch (err) {
      console.error('Failed to regenerate outline:', err);
      setError('Failed to regenerate outline');
    }
  };

  const handleGenerateDocument = async () => {
    if (!id) return;

    try {
      setIsGeneratingDocument(true);
      setError(null);
      const document = await api.generateFromBrief(id);
      // Navigate to the generated document
      navigate(`/document/${document.id}`);
    } catch (err) {
      console.error('Failed to generate document:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate document');
    } finally {
      setIsGeneratingDocument(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading brief...</p>
        </div>
      </div>
    );
  }

  if (error && !brief) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to Load Brief</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!brief) {
    return null;
  }

  if (isEditingBrief) {
    return (
      <DocumentBriefWizard
        existingBriefId={brief.id}
        onComplete={handleBriefUpdateComplete}
        onCancel={() => setIsEditingBrief(false)}
      />
    );
  }

  const renderValue = (value: any): string => {
    if (Array.isArray(value)) {
      return value.length > 0 ? value.filter(v => v?.trim()).join(', ') : 'None specified';
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return value?.toString().trim() || 'Not specified';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{brief.title}</h1>
                <p className="text-sm text-gray-500">
                  {DOCUMENT_TYPE_LABELS[brief.document_type] || brief.document_type}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleEditBrief}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Edit2 className="w-4 h-4" />
                Edit Brief
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Brief Information */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Brief Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">Topic</h3>
              <p className="text-gray-900">{renderValue(brief.topic)}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">Audience</h3>
              <p className="text-gray-900">{renderValue(brief.audience)}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">Purpose</h3>
              <p className="text-gray-900">{renderValue(brief.purpose)}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">Language</h3>
              <p className="text-gray-900">
                {LANGUAGE_LABELS[brief.language] || brief.language}
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">Desired Length</h3>
              <p className="text-gray-900">{renderValue(brief.desired_length)}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">Tone</h3>
              <p className="text-gray-900">{renderValue(brief.tone)}</p>
            </div>
          </div>
        </div>

        {/* Outline Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Document Outline</h2>

          {brief.outline && brief.outline.length > 0 ? (
            isEditingOutline ? (
              <OutlineEditor
                outline={brief.outline}
                onSave={handleSaveOutline}
                onCancel={handleCancelEditOutline}
              />
            ) : (
              <OutlineViewer
                outline={brief.outline}
                isApproved={brief.outline_approved}
                onEdit={handleEditOutline}
                onApprove={handleApproveOutline}
                onRegenerate={handleRegenerateOutline}
                onGenerateDocument={handleGenerateDocument}
                isLoading={isGeneratingDocument}
              />
            )
          ) : (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p className="mb-4">No outline generated yet</p>
              <button
                onClick={handleRegenerateOutline}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Generate Outline
              </button>
            </div>
          )}
        </div>

        {/* Document Link */}
        {brief.document_id && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <div>
                  <h3 className="font-medium text-green-900">Document Generated</h3>
                  <p className="text-sm text-green-700">
                    Your document has been successfully generated
                  </p>
                </div>
              </div>
              <button
                onClick={() => navigate(`/document/${brief.document_id}`)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <FileText className="w-4 h-4" />
                View Document
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Delete Brief</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this brief? This action cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
