import { GraduationCap, BookOpen } from 'lucide-react';
import type { AcademicPaperData } from './FieldRegistry';

interface AcademicFieldsProps {
  data: AcademicPaperData;
  onChange: (data: AcademicPaperData) => void;
}

export function AcademicFields({ data, onChange }: AcademicFieldsProps) {
  const updateField = (field: keyof AcademicPaperData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-100 rounded-lg">
          <GraduationCap className="w-6 h-6 text-purple-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Academic Paper Details</h2>
          <p className="text-sm text-gray-600">Provide academic context and requirements</p>
        </div>
      </div>

      {/* Subject */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Subject <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.subject}
          onChange={(e) => updateField('subject', e.target.value)}
          placeholder="e.g., Psychology, Biology, Computer Science"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      {/* Research Question */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Research Question <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.research_question}
          onChange={(e) => updateField('research_question', e.target.value)}
          placeholder="What is the main research question or thesis statement?"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Academic Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Academic Level <span className="text-red-500">*</span>
        </label>
        <select
          value={data.academic_level}
          onChange={(e) => updateField('academic_level', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="high_school">High School</option>
          <option value="undergraduate">Undergraduate</option>
          <option value="graduate">Graduate (Master's)</option>
          <option value="doctoral">Doctoral (PhD)</option>
        </select>
      </div>

      {/* Institution and Course Code */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Institution <span className="text-gray-500 text-xs">(Optional)</span>
          </label>
          <input
            type="text"
            value={data.institution || ''}
            onChange={(e) => updateField('institution', e.target.value)}
            placeholder="e.g., Stanford University"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Course Code <span className="text-gray-500 text-xs">(Optional)</span>
          </label>
          <input
            type="text"
            value={data.course_code || ''}
            onChange={(e) => updateField('course_code', e.target.value)}
            placeholder="e.g., PSYCH 101"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Required Structure */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <BookOpen className="w-4 h-4 inline mr-1" />
          Required Structure <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.required_structure}
          onChange={(e) => updateField('required_structure', e.target.value)}
          placeholder="e.g., IMRaD, Abstract-Introduction-Body-Conclusion"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
        <p className="text-xs text-gray-500 mt-1">
          Common: IMRaD (Introduction, Methods, Results, and Discussion)
        </p>
      </div>

      {/* Word Count Target */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Word Count Target <span className="text-red-500">*</span>
        </label>
        <input
          type="number"
          value={data.word_count_target}
          onChange={(e) => updateField('word_count_target', parseInt(e.target.value) || 0)}
          min="0"
          placeholder="e.g., 3000"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      {/* Citation Style */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Citation Style <span className="text-red-500">*</span>
        </label>
        <select
          value={data.citation_style}
          onChange={(e) => updateField('citation_style', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="APA">APA (American Psychological Association)</option>
          <option value="MLA">MLA (Modern Language Association)</option>
          <option value="Chicago">Chicago/Turabian</option>
          <option value="Harvard">Harvard</option>
          <option value="IEEE">IEEE</option>
        </select>
      </div>

      {/* Methodology */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Methodology <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <textarea
          value={data.methodology || ''}
          onChange={(e) => updateField('methodology', e.target.value)}
          placeholder="Describe the research methodology, approach, or framework"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Key Findings */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Key Findings <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <textarea
          value={data.key_findings || ''}
          onChange={(e) => updateField('key_findings', e.target.value)}
          placeholder="What are the main findings or conclusions?"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Formatting Requirements */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Formatting Requirements <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <textarea
          value={data.formatting_requirements || ''}
          onChange={(e) => updateField('formatting_requirements', e.target.value)}
          placeholder="e.g., Double-spaced, Times New Roman 12pt, 1-inch margins"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
        />
      </div>
    </div>
  );
}
