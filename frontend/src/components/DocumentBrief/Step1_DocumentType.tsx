import { FileText, BookOpen, FolderOpen, Code, Briefcase, Newspaper, User, FileEdit, GraduationCap, BookMarked } from 'lucide-react';

interface Step1Props {
  selectedType: string;
  onChange: (type: string) => void;
}

interface DocumentTypeCard {
  type: string;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const documentTypes: DocumentTypeCard[] = [
  {
    type: 'general',
    label: 'General',
    description: 'General purpose document',
    icon: <FileText className="w-8 h-8" />,
  },
  {
    type: 'essay',
    label: 'Essay',
    description: 'Academic or personal essay',
    icon: <FileEdit className="w-8 h-8" />,
  },
  {
    type: 'research_paper',
    label: 'Research Paper',
    description: 'Academic research paper with citations',
    icon: <GraduationCap className="w-8 h-8" />,
  },
  {
    type: 'technical_documentation',
    label: 'Technical Documentation',
    description: 'Software or technical guides',
    icon: <Code className="w-8 h-8" />,
  },
  {
    type: 'user_guide',
    label: 'User Guide',
    description: 'Product or service instructions',
    icon: <BookMarked className="w-8 h-8" />,
  },
  {
    type: 'academic_document',
    label: 'Academic Document',
    description: 'Scholarly or educational content',
    icon: <BookOpen className="w-8 h-8" />,
  },
  {
    type: 'project_report',
    label: 'Project Report',
    description: 'Project status and results',
    icon: <FolderOpen className="w-8 h-8" />,
  },
  {
    type: 'business_document',
    label: 'Business Document',
    description: 'Business plans, proposals, memos',
    icon: <Briefcase className="w-8 h-8" />,
  },
  {
    type: 'article',
    label: 'Article',
    description: 'Blog post or publication article',
    icon: <Newspaper className="w-8 h-8" />,
  },
  {
    type: 'resume',
    label: 'Resume',
    description: 'Professional resume or CV',
    icon: <User className="w-8 h-8" />,
  },
];

export function Step1_DocumentType({ selectedType, onChange }: Step1Props) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Document Type</h2>
        <p className="text-gray-600">Select the type of document you want to create</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {documentTypes.map((docType) => {
          const isSelected = selectedType === docType.type;

          return (
            <button
              key={docType.type}
              onClick={() => onChange(docType.type)}
              className={`
                p-6 rounded-lg border-2 transition-all duration-200
                hover:shadow-lg hover:scale-105
                ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-blue-300'
                }
              `}
            >
              <div
                className={`
                  mb-3 flex justify-center
                  ${isSelected ? 'text-blue-600' : 'text-gray-400'}
                `}
              >
                {docType.icon}
              </div>
              <h3
                className={`
                  font-semibold text-center mb-1
                  ${isSelected ? 'text-blue-600' : 'text-gray-900'}
                `}
              >
                {docType.label}
              </h3>
              <p className="text-xs text-gray-500 text-center">{docType.description}</p>
            </button>
          );
        })}
      </div>

      {!selectedType && (
        <p className="text-sm text-red-600 mt-2">Please select a document type to continue</p>
      )}
    </div>
  );
}
