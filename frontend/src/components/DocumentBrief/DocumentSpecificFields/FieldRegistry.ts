// Field Registry: Maps document types to their specific field schemas and validation rules

export type FieldType = 'text' | 'textarea' | 'number' | 'select' | 'multi-select' | 'checkbox' | 'radio' | 'dynamic-list' | 'array';

export interface FieldDefinition {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  defaultValue?: any;
  validation?: (value: any) => string | null;
  helpText?: string;
}

// Technical Documentation Fields
export interface TechnicalDocData {
  software_name: string;
  project_description: string;
  technologies: string[];
  programming_languages: string[];
  target_technical_audience: 'beginners' | 'intermediate' | 'advanced';
  documentation_purpose: string[];
  include_sections: string[];
  prerequisites?: string;
  known_limitations?: string;
}

// Academic Paper Fields
export interface AcademicPaperData {
  subject: string;
  research_question: string;
  academic_level: 'high_school' | 'undergraduate' | 'graduate' | 'doctoral';
  institution?: string;
  course_code?: string;
  required_structure: string;
  word_count_target: number;
  citation_style: 'APA' | 'MLA' | 'Chicago' | 'Harvard' | 'IEEE';
  methodology?: string;
  key_findings?: string;
  formatting_requirements?: string;
}

// Essay/Article Fields
export interface EssayArticleData {
  central_argument: string;
  target_publication?: string;
  main_arguments: string[];
  examples_to_include: string[];
  required_structure: string;
  word_count_target: number;
  publication_type: 'blog' | 'magazine' | 'journal' | 'website' | 'other';
}

// Project Report Fields
export interface ProjectReportData {
  project_name: string;
  project_objective: string;
  problem_statement: string;
  technologies_used: string[];
  team_size: number;
  team_roles: string;
  methodology: string;
  implementation_details: string;
  results_summary: string;
  limitations?: string;
  future_scope?: string;
  required_chapters: string[];
}

// Business Document Fields
export interface BusinessDocData {
  business_name: string;
  organization_type: 'startup' | 'enterprise' | 'nonprofit' | 'government' | 'other';
  document_purpose: 'proposal' | 'report' | 'plan' | 'analysis' | 'memo' | 'other';
  business_context: string;
  scope: string;
  key_analysis_points: string[];
  recommendations?: string;
  formality_level: 'formal' | 'semi-formal' | 'informal';
  required_sections: string[];
}

// Resume/CV Fields
export interface ResumeData {
  personal_info: {
    name: string;
    email: string;
    phone: string;
    location: string;
    linkedin?: string;
    portfolio?: string;
    github?: string;
  };
  target_role: string;
  professional_summary: string;
  education: Array<{
    degree: string;
    institution: string;
    year: string;
    gpa?: string;
    achievements?: string;
  }>;
  work_experience: Array<{
    title: string;
    company: string;
    duration: string;
    responsibilities: string[];
    achievements: string[];
  }>;
  technical_skills: string[];
  soft_skills: string[];
  projects: Array<{
    name: string;
    description: string;
    technologies: string[];
    link?: string;
  }>;
  certifications: string[];
  achievements: string[];
  extracurriculars?: string[];
}

// Research Paper Fields
export interface ResearchPaperData {
  research_topic: string;
  research_question: string;
  hypothesis: string;
  research_methodology: 'qualitative' | 'quantitative' | 'mixed';
  data_collection_methods: string[];
  sample_size: string;
  key_findings: string;
  limitations: string;
  implications: string;
  citation_style: 'APA' | 'MLA' | 'Chicago' | 'IEEE' | 'Nature';
  keywords: string[];
}

// User Guide Fields
export interface UserGuideData {
  product_name: string;
  product_type: 'software' | 'hardware' | 'service' | 'other';
  user_level: 'beginner' | 'intermediate' | 'advanced' | 'all';
  guide_purpose: 'quick_start' | 'complete_manual' | 'troubleshooting' | 'reference';
  include_screenshots: boolean;
  include_troubleshooting: boolean;
  include_faq: boolean;
  platform: string;
  prerequisites: string;
  support_contact?: string;
}

// General Document Fields
export interface GeneralDocData {
  flexible_structure: string;
  key_topics: string[];
  special_formatting_notes?: string;
}

// Document type mapping
export const DOCUMENT_TYPE_FIELDS: Record<string, string> = {
  TECHNICAL_DOC: 'technical',
  ACADEMIC_PAPER: 'academic',
  ESSAY_ARTICLE: 'essay',
  PROJECT_REPORT: 'project',
  BUSINESS_DOC: 'business',
  RESUME_CV: 'resume',
  RESEARCH_PAPER: 'research',
  USER_GUIDE: 'user_guide',
  GENERAL: 'general',
};

// Default values by document type
export const DEFAULT_VALUES: Record<string, any> = {
  technical: {
    software_name: '',
    project_description: '',
    technologies: [],
    programming_languages: [],
    target_technical_audience: 'intermediate',
    documentation_purpose: [],
    include_sections: [],
    prerequisites: '',
    known_limitations: '',
  },
  academic: {
    subject: '',
    research_question: '',
    academic_level: 'undergraduate',
    institution: '',
    course_code: '',
    required_structure: 'IMRaD (Introduction, Methods, Results, and Discussion)',
    word_count_target: 3000,
    citation_style: 'APA',
    methodology: '',
    key_findings: '',
    formatting_requirements: '',
  },
  essay: {
    central_argument: '',
    target_publication: '',
    main_arguments: [],
    examples_to_include: [],
    required_structure: 'Introduction, Body Paragraphs, Conclusion',
    word_count_target: 1500,
    publication_type: 'blog',
  },
  project: {
    project_name: '',
    project_objective: '',
    problem_statement: '',
    technologies_used: [],
    team_size: 1,
    team_roles: '',
    methodology: '',
    implementation_details: '',
    results_summary: '',
    limitations: '',
    future_scope: '',
    required_chapters: [],
  },
  business: {
    business_name: '',
    organization_type: 'startup',
    document_purpose: 'report',
    business_context: '',
    scope: '',
    key_analysis_points: [],
    recommendations: '',
    formality_level: 'formal',
    required_sections: [],
  },
  resume: {
    personal_info: {
      name: '',
      email: '',
      phone: '',
      location: '',
      linkedin: '',
      portfolio: '',
      github: '',
    },
    target_role: '',
    professional_summary: '',
    education: [],
    work_experience: [],
    technical_skills: [],
    soft_skills: [],
    projects: [],
    certifications: [],
    achievements: [],
    extracurriculars: [],
  },
  research: {
    research_topic: '',
    research_question: '',
    hypothesis: '',
    research_methodology: 'mixed',
    data_collection_methods: [],
    sample_size: '',
    key_findings: '',
    limitations: '',
    implications: '',
    citation_style: 'APA',
    keywords: [],
  },
  user_guide: {
    product_name: '',
    product_type: 'software',
    user_level: 'all',
    guide_purpose: 'complete_manual',
    include_screenshots: true,
    include_troubleshooting: true,
    include_faq: true,
    platform: '',
    prerequisites: '',
    support_contact: '',
  },
  general: {
    flexible_structure: '',
    key_topics: [],
    special_formatting_notes: '',
  },
};

// Validation functions
export function validateRequired(value: any): string | null {
  if (value === null || value === undefined || value === '') {
    return 'This field is required';
  }
  if (Array.isArray(value) && value.length === 0) {
    return 'At least one item is required';
  }
  return null;
}

export function validateNumber(value: any): string | null {
  if (isNaN(value) || value < 0) {
    return 'Please enter a valid positive number';
  }
  return null;
}

export function validateEmail(value: string): string | null {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value)) {
    return 'Please enter a valid email address';
  }
  return null;
}

export function getDefaultValue(documentType: string): any {
  const fieldType = DOCUMENT_TYPE_FIELDS[documentType] || 'general';
  return DEFAULT_VALUES[fieldType] || {};
}

export function hasDocumentSpecificFields(documentType: string): boolean {
  return documentType !== 'GENERAL';
}
