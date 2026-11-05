import { Plus, X, Info } from 'lucide-react';
import { Step4_DocumentSpecific, validateStep4 } from './Step4_DocumentSpecific';
import { FileAttachmentSelector } from './FileAttachmentSelector';

interface Step4Props {
  documentType: string;
  documentSpecificData: Record<string, any>;
  requiredSections: string[];
  importantPoints: string[];
  topicsToAvoid: string[];
  additionalInstructions: string;
  citationStyle: string;
  briefId: string | null;
  onChange: (field: string, value: any) => void;
}

const CITATION_REQUIRING_TYPES = ['research_paper', 'academic_paper', 'technical_documentation'];

const CITATION_STYLES = [
  { value: '', label: 'Select citation style...' },
  { value: 'APA', label: 'APA (American Psychological Association)' },
  { value: 'MLA', label: 'MLA (Modern Language Association)' },
  { value: 'Chicago', label: 'Chicago/Turabian' },
  { value: 'Harvard', label: 'Harvard' },
  { value: 'IEEE', label: 'IEEE' },
  { value: 'Vancouver', label: 'Vancouver' },
];

export function Step4_DocumentSpecificAndAdditional({
  documentType,
  documentSpecificData,
  requiredSections,
  importantPoints,
  topicsToAvoid,
  additionalInstructions,
  citationStyle,
  briefId,
  onChange,
}: Step4Props) {
  const needsCitations = CITATION_REQUIRING_TYPES.includes(documentType);

  const handleAddSection = () => {
    onChange('required_sections', [...requiredSections, '']);
  };

  const handleUpdateSection = (index: number, value: string) => {
    const updated = [...requiredSections];
    updated[index] = value;
    onChange('required_sections', updated);
  };

  const handleRemoveSection = (index: number) => {
    const updated = requiredSections.filter((_, i) => i !== index);
    onChange('required_sections', updated);
  };

  const handleAddPoint = () => {
    onChange('important_points', [...importantPoints, '']);
  };

  const handleUpdatePoint = (index: number, value: string) => {
    const updated = [...importantPoints];
    updated[index] = value;
    onChange('important_points', updated);
  };

  const handleRemovePoint = (index: number) => {
    const updated = importantPoints.filter((_, i) => i !== index);
    onChange('important_points', updated);
  };

  const handleAddTopic = () => {
    onChange('topics_to_avoid', [...topicsToAvoid, '']);
  };

  const handleUpdateTopic = (index: number, value: string) => {
    const updated = [...topicsToAvoid];
    updated[index] = value;
    onChange('topics_to_avoid', updated);
  };

  const handleRemoveTopic = (index: number) => {
    const updated = topicsToAvoid.filter((_, i) => i !== index);
    onChange('topics_to_avoid', updated);
  };

  return (
    <div className="space-y-8 max-h-[500px] overflow-y-auto pr-2">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Document-Specific Details & Instructions</h2>
        <p className="text-gray-600">
          Provide type-specific information, attach reference files, and add additional guidance for your document.
        </p>
      </div>

      {/* Document-Specific Fields */}
      <div className="border-b border-gray-200 pb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Type-Specific Fields</h3>
        <Step4_DocumentSpecific
          documentType={documentType}
          documentSpecificData={documentSpecificData}
          onChange={onChange}
        />
      </div>

      {/* File Attachments */}
      <div className="border-b border-gray-200 pb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Reference Files</h3>
        <FileAttachmentSelector
          briefId={briefId}
          onAttachmentsChange={(fileIds) => onChange('attached_file_ids', fileIds)}
        />
      </div>

      {/* Required Sections */}
      <div className="space-y-3">
        <label className="block">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-gray-700">Required Sections</span>
            <div className="group relative">
              <Info className="w-4 h-4 text-gray-400 cursor-help" />
              <div className="invisible group-hover:visible absolute left-0 top-6 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg z-10">
                Specify sections that must be included in the document outline
              </div>
            </div>
          </div>
        </label>

        <div className="space-y-2">
          {requiredSections.map((section, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                type="text"
                value={section}
                onChange={(e) => handleUpdateSection(index, e.target.value)}
                placeholder="e.g., Introduction, Methodology, Conclusion"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => handleRemoveSection(index)}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Remove section"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={handleAddSection}
          className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Section
        </button>
      </div>

      {/* Important Points */}
      <div className="space-y-3">
        <label className="block">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-gray-700">Important Points to Include</span>
            <div className="group relative">
              <Info className="w-4 h-4 text-gray-400 cursor-help" />
              <div className="invisible group-hover:visible absolute left-0 top-6 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg z-10">
                Key facts, concepts, or ideas that should be covered in the document
              </div>
            </div>
          </div>
        </label>

        <div className="space-y-2">
          {importantPoints.map((point, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                type="text"
                value={point}
                onChange={(e) => handleUpdatePoint(index, e.target.value)}
                placeholder="e.g., Focus on practical applications"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => handleRemovePoint(index)}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Remove point"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={handleAddPoint}
          className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Point
        </button>
      </div>

      {/* Topics to Avoid */}
      <div className="space-y-3">
        <label className="block">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-gray-700">Topics to Avoid</span>
            <div className="group relative">
              <Info className="w-4 h-4 text-gray-400 cursor-help" />
              <div className="invisible group-hover:visible absolute left-0 top-6 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg z-10">
                Topics or areas that should not be included or discussed
              </div>
            </div>
          </div>
        </label>

        <div className="space-y-2">
          {topicsToAvoid.map((topic, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                type="text"
                value={topic}
                onChange={(e) => handleUpdateTopic(index, e.target.value)}
                placeholder="e.g., Political opinions, Unverified claims"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => handleRemoveTopic(index)}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                title="Remove topic"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={handleAddTopic}
          className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Topic
        </button>
      </div>

      {/* Citation Preferences - Conditional */}
      {needsCitations && (
        <div className="space-y-3">
          <label className="block">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-gray-700">
                Citation Style <span className="text-red-500">*</span>
              </span>
              <div className="group relative">
                <Info className="w-4 h-4 text-gray-400 cursor-help" />
                <div className="invisible group-hover:visible absolute left-0 top-6 w-64 p-2 bg-gray-800 text-white text-xs rounded shadow-lg z-10">
                  Select the citation format for references in your document
                </div>
              </div>
            </div>
          </label>

          <select
            value={citationStyle}
            onChange={(e) => onChange('citation_style', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {CITATION_STYLES.map((style) => (
              <option key={style.value} value={style.value}>
                {style.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Additional Instructions */}
      <div className="space-y-3">
        <label className="block">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-gray-700">Additional Instructions</span>
            <span className="text-sm text-gray-500">(Optional)</span>
          </div>
          <p className="text-sm text-gray-500 mb-2">
            Any other specific requirements, preferences, or context that will help generate a better document.
          </p>
        </label>

        <textarea
          value={additionalInstructions}
          onChange={(e) => onChange('additional_instructions', e.target.value)}
          placeholder="e.g., Use simple language, include practical examples, avoid jargon..."
          rows={5}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        />
      </div>
    </div>
  );
}

// Export the validation function
export { validateStep4 };
