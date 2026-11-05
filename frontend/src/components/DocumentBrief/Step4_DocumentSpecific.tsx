import { AlertCircle } from 'lucide-react';
import { TechnicalFields } from './DocumentSpecificFields/TechnicalFields';
import { AcademicFields } from './DocumentSpecificFields/AcademicFields';
import { EssayArticleFields } from './DocumentSpecificFields/EssayArticleFields';
import { ProjectReportFields } from './DocumentSpecificFields/ProjectReportFields';
import { BusinessFields } from './DocumentSpecificFields/BusinessFields';
import { ResumeFields } from './DocumentSpecificFields/ResumeFields';
import { ResearchPaperFields } from './DocumentSpecificFields/ResearchPaperFields';
import { UserGuideFields } from './DocumentSpecificFields/UserGuideFields';
import { GeneralFields } from './DocumentSpecificFields/GeneralFields';
import { DOCUMENT_TYPE_FIELDS, getDefaultValue, hasDocumentSpecificFields } from './DocumentSpecificFields/FieldRegistry';
import type {
  TechnicalDocData,
  AcademicPaperData,
  EssayArticleData,
  ProjectReportData,
  BusinessDocData,
  ResumeData,
  ResearchPaperData,
  UserGuideData,
  GeneralDocData,
} from './DocumentSpecificFields/FieldRegistry';

interface Step4Props {
  documentType: string;
  documentSpecificData: Record<string, any>;
  onChange: (field: string, value: any) => void;
}

export function Step4_DocumentSpecific({ documentType, documentSpecificData, onChange }: Step4Props) {
  const fieldType = DOCUMENT_TYPE_FIELDS[documentType] || 'general';

  // Initialize with default values if empty
  const data = Object.keys(documentSpecificData).length === 0
    ? getDefaultValue(documentType)
    : documentSpecificData;

  const handleChange = (newData: any) => {
    onChange('document_specific_data', newData);
  };

  // For GENERAL document type, show a simplified message
  if (!hasDocumentSpecificFields(documentType)) {
    return (
      <div className="space-y-6">
        <GeneralFields
          data={data as GeneralDocData}
          onChange={handleChange}
        />
      </div>
    );
  }

  // Render the appropriate field component based on document type
  const renderFields = () => {
    switch (fieldType) {
      case 'technical':
        return (
          <TechnicalFields
            data={data as TechnicalDocData}
            onChange={handleChange}
          />
        );

      case 'academic':
        return (
          <AcademicFields
            data={data as AcademicPaperData}
            onChange={handleChange}
          />
        );

      case 'essay':
        return (
          <EssayArticleFields
            data={data as EssayArticleData}
            onChange={handleChange}
          />
        );

      case 'project':
        return (
          <ProjectReportFields
            data={data as ProjectReportData}
            onChange={handleChange}
          />
        );

      case 'business':
        return (
          <BusinessFields
            data={data as BusinessDocData}
            onChange={handleChange}
          />
        );

      case 'resume':
        return (
          <ResumeFields
            data={data as ResumeData}
            onChange={handleChange}
          />
        );

      case 'research':
        return (
          <ResearchPaperFields
            data={data as ResearchPaperData}
            onChange={handleChange}
          />
        );

      case 'user_guide':
        return (
          <UserGuideFields
            data={data as UserGuideData}
            onChange={handleChange}
          />
        );

      case 'general':
        return (
          <GeneralFields
            data={data as GeneralDocData}
            onChange={handleChange}
          />
        );

      default:
        return (
          <div className="text-center py-12">
            <div className="inline-flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800">
              <AlertCircle className="w-5 h-5" />
              <p>No specific fields configured for this document type yet.</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {renderFields()}
    </div>
  );
}

// Validation function to check if required fields are filled
export function validateStep4(documentType: string, documentSpecificData: Record<string, any>): boolean {
  const fieldType = DOCUMENT_TYPE_FIELDS[documentType] || 'general';

  // If no data provided, it's invalid
  if (!documentSpecificData || Object.keys(documentSpecificData).length === 0) {
    return false;
  }

  // Validate based on document type
  switch (fieldType) {
    case 'technical':
      const techData = documentSpecificData as TechnicalDocData;
      return !!(
        techData.software_name?.trim() &&
        techData.project_description?.trim() &&
        techData.technologies?.length > 0 &&
        techData.programming_languages?.length > 0 &&
        techData.target_technical_audience &&
        techData.documentation_purpose?.length > 0
      );

    case 'academic':
      const academicData = documentSpecificData as AcademicPaperData;
      return !!(
        academicData.subject?.trim() &&
        academicData.research_question?.trim() &&
        academicData.academic_level &&
        academicData.required_structure?.trim() &&
        academicData.word_count_target > 0 &&
        academicData.citation_style
      );

    case 'essay':
      const essayData = documentSpecificData as EssayArticleData;
      return !!(
        essayData.central_argument?.trim() &&
        essayData.main_arguments?.length > 0 &&
        essayData.required_structure?.trim() &&
        essayData.word_count_target > 0 &&
        essayData.publication_type
      );

    case 'project':
      const projectData = documentSpecificData as ProjectReportData;
      return !!(
        projectData.project_name?.trim() &&
        projectData.project_objective?.trim() &&
        projectData.problem_statement?.trim() &&
        projectData.technologies_used?.length > 0 &&
        projectData.team_size > 0 &&
        projectData.team_roles?.trim() &&
        projectData.methodology?.trim() &&
        projectData.implementation_details?.trim() &&
        projectData.results_summary?.trim()
      );

    case 'business':
      const businessData = documentSpecificData as BusinessDocData;
      return !!(
        businessData.business_name?.trim() &&
        businessData.organization_type &&
        businessData.document_purpose &&
        businessData.business_context?.trim() &&
        businessData.scope?.trim() &&
        businessData.key_analysis_points?.length > 0 &&
        businessData.formality_level
      );

    case 'resume':
      const resumeData = documentSpecificData as ResumeData;
      return !!(
        resumeData.personal_info?.name?.trim() &&
        resumeData.personal_info?.email?.trim() &&
        resumeData.personal_info?.phone?.trim() &&
        resumeData.personal_info?.location?.trim() &&
        resumeData.target_role?.trim() &&
        resumeData.professional_summary?.trim()
      );

    case 'research':
      const researchData = documentSpecificData as ResearchPaperData;
      return !!(
        researchData.research_topic?.trim() &&
        researchData.research_question?.trim() &&
        researchData.hypothesis?.trim() &&
        researchData.research_methodology &&
        researchData.data_collection_methods?.length > 0 &&
        researchData.sample_size?.trim() &&
        researchData.key_findings?.trim() &&
        researchData.limitations?.trim() &&
        researchData.implications?.trim() &&
        researchData.citation_style &&
        researchData.keywords?.length > 0
      );

    case 'user_guide':
      const guideData = documentSpecificData as UserGuideData;
      return !!(
        guideData.product_name?.trim() &&
        guideData.product_type &&
        guideData.user_level &&
        guideData.guide_purpose &&
        guideData.platform?.trim() &&
        guideData.prerequisites?.trim()
      );

    case 'general':
      const generalData = documentSpecificData as GeneralDocData;
      return !!(
        generalData.flexible_structure?.trim() &&
        generalData.key_topics?.length > 0
      );

    default:
      return true; // Allow proceeding if no validation rules defined
  }
}
