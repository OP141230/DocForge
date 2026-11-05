// Document IR TypeScript interfaces (mirror backend Pydantic models)

export interface DocumentMetadata {
  author?: string | null;
  document_type: string;
  audience?: string | null;
  tone?: string | null;
  language: string;
  custom_fields?: Record<string, any>;
}

export interface InlineContent {
  text: string;
  bold?: boolean;
  italic?: boolean;
  underline?: boolean;
  link?: string | null;
}

export interface Block {
  id: string;
  type: string;
}

export interface Paragraph extends Block {
  type: 'paragraph';
  content: InlineContent[];
}

export interface Heading extends Block {
  type: 'heading';
  level: number;
  content: InlineContent[];
}

export interface ListBlock extends Block {
  type: 'list';
  ordered: boolean;
  items: InlineContent[][];
}

export interface Quote extends Block {
  type: 'quote';
  content: InlineContent[];
  attribution?: string | null;
}

export interface CodeBlock extends Block {
  type: 'code_block';
  language?: string | null;
  code: string;
}

export interface Table extends Block {
  type: 'table';
  headers?: string[] | null;
  rows: string[][];
}

export type BlockType = Paragraph | Heading | ListBlock | Quote | CodeBlock | Table;

export interface Section {
  id: string;
  type: 'section';
  level: number;
  title: string;
  blocks: BlockType[];
}

export interface DocumentIR {
  id: string;
  title: string;
  content: Section[];
  metadata: DocumentMetadata;
  created_at: string;
  updated_at: string;
  schema_version: string;
}

export interface DocumentRequirements {
  document_type: string;
  topic: string;
  title: string;
  audience?: string;
  tone?: string;
  language?: string;
  length?: string;
  additional_instructions?: string;
}

export interface OutlineItem {
  level: number;
  title: string;
}

// Document configuration enums and helpers
export enum DocumentType {
  TECHNICAL_DOCUMENTATION = 'technical_documentation',
  ACADEMIC_DOCUMENT = 'academic_document',
  PROJECT_REPORT = 'project_report',
  BUSINESS_DOCUMENT = 'business_document',
  ARTICLE = 'article',
  RESUME = 'resume',
  GENERAL = 'general',
  ESSAY = 'essay',
  RESEARCH_PAPER = 'research_paper',
  USER_GUIDE = 'user_guide',
}

export enum DocumentTone {
  PROFESSIONAL = 'professional',
  CASUAL = 'casual',
  FORMAL = 'formal',
  FRIENDLY = 'friendly',
  TECHNICAL = 'technical',
}

export enum DocumentLength {
  SHORT = 'short',
  MEDIUM = 'medium',
  LONG = 'long',
  VERY_LONG = 'very_long',
}

export enum DocumentAudience {
  GENERAL = 'general',
  TECHNICAL = 'technical',
  ACADEMIC = 'academic',
  BUSINESS = 'business',
  STUDENTS = 'students',
}

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  [DocumentType.TECHNICAL_DOCUMENTATION]: 'Technical Documentation',
  [DocumentType.ACADEMIC_DOCUMENT]: 'Academic Document',
  [DocumentType.PROJECT_REPORT]: 'Project Report',
  [DocumentType.BUSINESS_DOCUMENT]: 'Business Document',
  [DocumentType.ARTICLE]: 'Article',
  [DocumentType.RESUME]: 'Resume',
  [DocumentType.GENERAL]: 'General',
  [DocumentType.ESSAY]: 'Essay',
  [DocumentType.RESEARCH_PAPER]: 'Research Paper',
  [DocumentType.USER_GUIDE]: 'User Guide',
}

export const DOCUMENT_TONE_LABELS: Record<DocumentTone, string> = {
  [DocumentTone.PROFESSIONAL]: 'Professional',
  [DocumentTone.CASUAL]: 'Casual',
  [DocumentTone.FORMAL]: 'Formal',
  [DocumentTone.FRIENDLY]: 'Friendly',
  [DocumentTone.TECHNICAL]: 'Technical',
}

export const DOCUMENT_LENGTH_LABELS: Record<DocumentLength, string> = {
  [DocumentLength.SHORT]: 'Short (1-2 pages)',
  [DocumentLength.MEDIUM]: 'Medium (3-5 pages)',
  [DocumentLength.LONG]: 'Long (6-10 pages)',
  [DocumentLength.VERY_LONG]: 'Very Long (10+ pages)',
}

export const DOCUMENT_AUDIENCE_LABELS: Record<DocumentAudience, string> = {
  [DocumentAudience.GENERAL]: 'General Audience',
  [DocumentAudience.TECHNICAL]: 'Technical Audience',
  [DocumentAudience.ACADEMIC]: 'Academic Audience',
  [DocumentAudience.BUSINESS]: 'Business Audience',
  [DocumentAudience.STUDENTS]: 'Students',
}

export function getDefaultRequirements(): DocumentRequirements {
  return {
    document_type: DocumentType.GENERAL,
    topic: '',
    title: '',
    audience: DocumentAudience.GENERAL,
    tone: DocumentTone.PROFESSIONAL,
    language: 'en',
    length: DocumentLength.MEDIUM,
    additional_instructions: '',
  }
}
