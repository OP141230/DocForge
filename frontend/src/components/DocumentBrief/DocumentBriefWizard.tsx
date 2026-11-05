import { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { ProgressIndicator } from './ProgressIndicator';
import { Step1_DocumentType } from './Step1_DocumentType';
import { Step2_BasicInfo } from './Step2_BasicInfo';
import { Step3_Preferences } from './Step3_Preferences';
import { Step4_DocumentSpecificAndAdditional, validateStep4 } from './Step4_DocumentSpecificAndAdditional';
import { Step5_Review_New } from './Step5_Review_New';
import { Step6_OutlineApproval_New } from './Step6_OutlineApproval_New';
import { api } from '../../api/client';
import type { DocumentBrief, CreateBriefRequest, UpdateBriefRequest, OutlineItem } from '../../types/document_brief';

interface DocumentBriefWizardProps {
  onComplete: (brief: DocumentBrief) => void;
  onCancel: () => void;
  existingBriefId?: string;
}

interface BriefFormData {
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
}

const initialFormData: BriefFormData = {
  document_type: '',
  title: '',
  topic: '',
  purpose: '',
  audience: '',
  language: 'en',
  desired_length: '',
  tone: '',
  writing_style: '',
  document_specific_data: {},
  required_sections: [],
  important_points: [],
  topics_to_avoid: [],
  additional_instructions: '',
  citation_style: '',
};

export function DocumentBriefWizard({
  onComplete,
  onCancel,
  existingBriefId,
}: DocumentBriefWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<BriefFormData>(initialFormData);
  const [briefId, setBriefId] = useState<string | null>(existingBriefId || null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(!!existingBriefId);
  const [outline, setOutline] = useState<OutlineItem[]>([]);
  const [isApproved, setIsApproved] = useState(false);

  // Load existing brief if resuming
  useEffect(() => {
    if (existingBriefId) {
      loadExistingBrief(existingBriefId);
    }
  }, [existingBriefId]);

  const loadExistingBrief = async (id: string) => {
    try {
      setIsLoading(true);
      const brief: DocumentBrief = await api.getBrief(id);
      
      setFormData({
        document_type: brief.document_type,
        title: brief.title,
        topic: brief.topic,
        purpose: brief.purpose || '',
        audience: brief.audience || '',
        language: brief.language,
        desired_length: brief.desired_length || '',
        tone: brief.tone || '',
        writing_style: brief.writing_style || '',
        document_specific_data: brief.document_specific_data,
        required_sections: brief.required_sections,
        important_points: brief.important_points,
        topics_to_avoid: brief.topics_to_avoid,
        additional_instructions: brief.additional_instructions || '',
        citation_style: brief.citation_style || '',
      });
      
      setBriefId(id);
      
      // Load outline if exists
      if (brief.outline && brief.outline.length > 0) {
        setOutline(brief.outline);
        setIsApproved(brief.outline_approved);
      }
    } catch (error) {
      console.error('Failed to load brief:', error);
      setSaveError('Failed to load existing brief');
    } finally {
      setIsLoading(false);
    }
  };

  // Debounced auto-save
  const autoSave = useCallback(
    async (data: BriefFormData) => {
      // Only save if we have minimum required data
      if (!data.document_type) return;

      try {
        setIsSaving(true);
        setSaveError(null);

        if (briefId) {
          // Update existing brief
          const updateData: UpdateBriefRequest = {
            document_type: data.document_type || undefined,
            title: data.title || undefined,
            topic: data.topic || undefined,
            purpose: data.purpose || undefined,
            audience: data.audience || undefined,
            language: data.language || undefined,
            desired_length: data.desired_length || undefined,
            tone: data.tone || undefined,
            writing_style: data.writing_style || undefined,
            document_specific_data: data.document_specific_data,
            required_sections: data.required_sections,
            important_points: data.important_points,
            topics_to_avoid: data.topics_to_avoid,
            additional_instructions: data.additional_instructions || undefined,
            citation_style: data.citation_style || undefined,
          };
          await api.updateBrief(briefId, updateData);
        } else {
          // Create new brief
          const createData: CreateBriefRequest = {
            document_type: data.document_type,
            title: data.title || 'Untitled Document',
            topic: data.topic || '',
            purpose: data.purpose || undefined,
            audience: data.audience || undefined,
            language: data.language,
            desired_length: data.desired_length || undefined,
            tone: data.tone || undefined,
            writing_style: data.writing_style || undefined,
            document_specific_data: data.document_specific_data,
            required_sections: data.required_sections,
            important_points: data.important_points,
            topics_to_avoid: data.topics_to_avoid,
            additional_instructions: data.additional_instructions || undefined,
            citation_style: data.citation_style || undefined,
          };
          const newBrief: DocumentBrief = await api.createBrief(createData);
          setBriefId(newBrief.id);
        }
      } catch (error) {
        console.error('Auto-save failed:', error);
        setSaveError('Failed to save draft');
      } finally {
        setIsSaving(false);
      }
    },
    [briefId]
  );

  // Debounce auto-save
  useEffect(() => {
    const timer = setTimeout(() => {
      autoSave(formData);
    }, 1500);

    return () => clearTimeout(timer);
  }, [formData, autoSave]);

  const updateField = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const validateCurrentStep = (): boolean => {
    switch (currentStep) {
      case 1:
        return !!formData.document_type;
      case 2:
        return !!(
          formData.title.trim() &&
          formData.topic.trim() &&
          formData.purpose.trim() &&
          formData.audience
        );
      case 3:
        return !!(formData.desired_length && formData.tone);
      case 4:
        return validateStep4(formData.document_type, formData.document_specific_data);
      case 5:
        // Step 5 is review, always valid
        return true;
      case 6:
        // Step 6 is outline approval, always valid
        return true;
      default:
        return false;
    }
  };

  const handleEditFromReview = (step: number) => {
    setCurrentStep(step);
  };

  const handleOutlineGenerated = (generatedOutline: OutlineItem[]) => {
    setOutline(generatedOutline);
    setIsApproved(false);
  };

  const handleOutlineUpdated = (updatedOutline: OutlineItem[]) => {
    setOutline(updatedOutline);
  };

  const handleApproved = () => {
    setIsApproved(true);
  };

  const handleDocumentGenerated = async () => {
    if (!briefId) return;
    try {
      const brief: DocumentBrief = await api.getBrief(briefId);
      onComplete(brief);
    } catch (error) {
      console.error('Failed to complete:', error);
      setSaveError('Failed to complete document generation');
    }
  };

  const handleNext = () => {
    if (validateCurrentStep() && currentStep < 6) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleStepClick = (step: number) => {
    if (step < currentStep) {
      setCurrentStep(step);
    }
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading brief...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full mx-4 my-8">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Create Document Brief</h1>
            <p className="text-sm text-gray-500 mt-1">
              {isSaving ? 'Saving draft...' : 'Draft saved automatically'}
            </p>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
            title="Close"
            aria-label="Close wizard"
          >
            <X className="w-6 h-6 text-gray-600 hover:text-gray-900" />
          </button>
        </div>

        {/* Progress Indicator */}
        <div className="px-6">
          <ProgressIndicator
            currentStep={currentStep}
            totalSteps={6}
            onStepClick={handleStepClick}
          />
        </div>

        {/* Step Content */}
        <div className="p-6 min-h-[400px]">
          {currentStep === 1 && (
            <Step1_DocumentType
              selectedType={formData.document_type}
              onChange={(type) => updateField('document_type', type)}
            />
          )}

          {currentStep === 2 && (
            <Step2_BasicInfo
              title={formData.title}
              topic={formData.topic}
              purpose={formData.purpose}
              audience={formData.audience}
              language={formData.language}
              onChange={updateField}
            />
          )}

          {currentStep === 3 && (
            <Step3_Preferences
              desiredLength={formData.desired_length}
              tone={formData.tone}
              writingStyle={formData.writing_style}
              onChange={updateField}
            />
          )}

          {currentStep === 4 && (
            <Step4_DocumentSpecificAndAdditional
              documentType={formData.document_type}
              documentSpecificData={formData.document_specific_data}
              requiredSections={formData.required_sections}
              importantPoints={formData.important_points}
              topicsToAvoid={formData.topics_to_avoid}
              additionalInstructions={formData.additional_instructions}
              citationStyle={formData.citation_style}
              briefId={briefId}
              onChange={updateField}
            />
          )}

          {currentStep === 5 && (
            <Step5_Review_New formData={formData} onEdit={handleEditFromReview} />
          )}

          {currentStep === 6 && (
            <Step6_OutlineApproval_New
              briefId={briefId}
              initialOutline={outline}
              isApproved={isApproved}
              onOutlineGenerated={handleOutlineGenerated}
              onOutlineUpdated={handleOutlineUpdated}
              onApproved={handleApproved}
              onDocumentGenerated={handleDocumentGenerated}
            />
          )}

          {saveError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {saveError}
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div className="flex items-center gap-3">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
              Previous
            </button>
            <button
              onClick={onCancel}
              className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>

          <div className="text-sm text-gray-600">Step {currentStep} of 6</div>

          {currentStep < 6 ? (
            <button
              onClick={handleNext}
              disabled={!validateCurrentStep()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <ChevronRight className="w-5 h-5" />
            </button>
          ) : (
            <div className="w-24">{/* Spacer for layout */}</div>
          )}
        </div>
      </div>
    </div>
  );
}
