// Document Brief types (mirror backend models)

export interface OutlineItem {
  level: number;
  title: string;
}

export interface DocumentBrief {
  id: string;
  user_id: string;
  conversation_id?: string | null;
  
  // Core document definition
  document_type: string;
  title: string;
  topic: string;
  purpose?: string | null;
  audience?: string | null;
  language: string;
  desired_length?: string | null;
  tone?: string | null;
  writing_style?: string | null;
  
  // Additional requirements
  document_specific_data: Record<string, any>;
  required_sections: string[];
  important_points: string[];
  topics_to_avoid: string[];
  additional_instructions?: string | null;
  citation_style?: string | null;
  
  // Outline and approval
  outline?: OutlineItem[] | null;
  outline_approved: boolean;
  outline_approved_at?: string | null;
  
  // Link to generated document
  document_id?: string | null;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface CreateBriefRequest {
  conversation_id?: string | null;
  document_type: string;
  title: string;
  topic: string;
  purpose?: string | null;
  audience?: string | null;
  language?: string;
  desired_length?: string | null;
  tone?: string | null;
  writing_style?: string | null;
  document_specific_data?: Record<string, any>;
  required_sections?: string[];
  important_points?: string[];
  topics_to_avoid?: string[];
  additional_instructions?: string | null;
  citation_style?: string | null;
}

export interface UpdateBriefRequest {
  conversation_id?: string | null;
  document_type?: string | null;
  title?: string | null;
  topic?: string | null;
  purpose?: string | null;
  audience?: string | null;
  language?: string | null;
  desired_length?: string | null;
  tone?: string | null;
  writing_style?: string | null;
  document_specific_data?: Record<string, any> | null;
  required_sections?: string[] | null;
  important_points?: string[] | null;
  topics_to_avoid?: string[] | null;
  additional_instructions?: string | null;
  citation_style?: string | null;
}

export type DocumentSpecificData = Record<string, any>;
