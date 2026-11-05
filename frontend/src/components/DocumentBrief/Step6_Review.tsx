import { Edit2, Loader2, FileText } from 'lucide-react';
import { useState } from 'react';

interface Step6Props {
  formData: {
    document_type: string;
    title: string;
    topic: string;
    purpose: string;
    audience: string;
    language: string;
    desired_length: string;
    tone: string;
    writing_style: string;
    document_specific_data: Record<string, any>;
    required_sections: string[];
    important_points: string[];
    topics_to_avoid: string[];
    additional_instructions: string;
    citation_style: string;
  };
  briefId: string | null;
  onEdit: (step: number) => void;
  onGenerateOutline: () => Promise<void>;
  onViewOutline: () => void;
  hasOutline: boolean;
}

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

export function Step6_Review({
  formData,
  briefId,
  onEdit,
  onGenerateOutline,
  onViewOutline,
  hasOutline,
}: Step6Props) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateOutline = async () => {
    if (!briefId) {
      setError('No brief ID available. Please go back and ensure all fields are saved.');
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);
      await onGenerateOutline();
    } catch (err) {
      console.error('Failed to generate outline:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate outline');
    } finally {
      setIsGenerating(false);
    }
  };

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
    <div className="space-y-6 max-h-[500px] overflow-y-auto pr-2">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Review Your Document Brief</h2>
        <p className="text-gray-600">
          Please review all information before generating the outline.
        </p>
      </div>

      {/* Document Type */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Document Type</h3>
          <button
            onClick={() => onEdit(1)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            <Edit2 className="w-4 h-4" />
            Edit
          </button>
        </div>
        <p className="text-gray-700">
          {DOCUMENT_TYPE_LABELS[formData.document_type] || formData.document_type}
        </p>
      </div>

      {/* Basic Information */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Basic Information</h3>
          <button
            onClick={() => onEdit(2)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            <Edit2 className="w-4 h-4" />
            Edit
          </button>
        </div>
        <dl className="space-y-2">
          <div>
            <dt className="text-sm font-medium text-gray-600">Title</dt>
            <dd className="text-gray-900">{renderValue(formData.title)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Topic</dt>
            <dd className="text-gray-900">{renderValue(formData.topic)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Purpose</dt>
            <dd className="text-gray-900">{renderValue(formData.purpose)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Audience</dt>
            <dd className="text-gray-900">{renderValue(formData.audience)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Language</dt>
            <dd className="text-gray-900">
              {LANGUAGE_LABELS[formData.language] || formData.language}
            </dd>
          </div>
        </dl>
      </div>

      {/* Preferences */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Preferences</h3>
          <button
            onClick={() => onEdit(3)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            <Edit2 className="w-4 h-4" />
            Edit
          </button>
        </div>
        <dl className="space-y-2">
          <div>
            <dt className="text-sm font-medium text-gray-600">Desired Length</dt>
            <dd className="text-gray-900">{renderValue(formData.desired_length)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Tone</dt>
            <dd className="text-gray-900">{renderValue(formData.tone)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Writing Style</dt>
            <dd className="text-gray-900">{renderValue(formData.writing_style)}</dd>
          </div>
        </dl>
      </div>

      {/* Document-Specific Details */}
      {Object.keys(formData.document_specific_data).length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-start justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Document-Specific Details</h3>
            <button
              onClick={() => onEdit(4)}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
            >
              <Edit2 className="w-4 h-4" />
              Edit
            </button>
          </div>
          <div className="text-sm text-gray-700 max-h-40 overflow-y-auto">
            <pre className="whitespace-pre-wrap font-sans">
              {JSON.stringify(formData.document_specific_data, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Additional Instructions */}
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Additional Instructions</h3>
          <button
            onClick={() => onEdit(5)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
          >
            <Edit2 className="w-4 h-4" />
            Edit
          </button>
        </div>
        <dl className="space-y-2">
          <div>
            <dt className="text-sm font-medium text-gray-600">Required Sections</dt>
            <dd className="text-gray-900">{renderValue(formData.required_sections)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Important Points</dt>
            <dd className="text-gray-900">{renderValue(formData.important_points)}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-600">Topics to Avoid</dt>
            <dd className="text-gray-900">{renderValue(formData.topics_to_avoid)}</dd>
          </div>
          {formData.citation_style && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Citation Style</dt>
              <dd className="text-gray-900">{renderValue(formData.citation_style)}</dd>
            </div>
          )}
          {formData.additional_instructions && (
            <div>
              <dt className="text-sm font-medium text-gray-600">Additional Notes</dt>
              <dd className="text-gray-900 whitespace-pre-wrap">
                {renderValue(formData.additional_instructions)}
              </dd>
            </div>
          )}
        </dl>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t">
        {hasOutline ? (
          <button
            onClick={onViewOutline}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <FileText className="w-5 h-5" />
            View Outline
          </button>
        ) : (
          <button
            onClick={handleGenerateOutline}
            disabled={isGenerating || !briefId}
            className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating Outline...
              </>
            ) : (
              <>
                <FileText className="w-5 h-5" />
                Generate Outline
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
