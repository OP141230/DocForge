import { useState } from 'react';
import { Code, Book, Users } from 'lucide-react';
import type { TechnicalDocData } from './FieldRegistry';

interface TechnicalFieldsProps {
  data: TechnicalDocData;
  onChange: (data: TechnicalDocData) => void;
}

const TECH_OPTIONS = [
  'React', 'Vue', 'Angular', 'Node.js', 'Python', 'Java', 'C++', 'C#',
  'Docker', 'Kubernetes', 'AWS', 'Azure', 'PostgreSQL', 'MongoDB', 'Redis',
  'TypeScript', 'JavaScript', 'Go', 'Rust', 'Swift', 'Kotlin'
];

const LANGUAGE_OPTIONS = [
  'JavaScript', 'TypeScript', 'Python', 'Java', 'C++', 'C#', 'Go', 'Rust',
  'PHP', 'Ruby', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB'
];

export function TechnicalFields({ data, onChange }: TechnicalFieldsProps) {
  const [techInput, setTechInput] = useState('');
  const [langInput, setLangInput] = useState('');

  const updateField = (field: keyof TechnicalDocData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  const addTechnology = (tech: string) => {
    if (tech && !data.technologies.includes(tech)) {
      updateField('technologies', [...data.technologies, tech]);
    }
    setTechInput('');
  };

  const removeTechnology = (tech: string) => {
    updateField('technologies', data.technologies.filter(t => t !== tech));
  };

  const addLanguage = (lang: string) => {
    if (lang && !data.programming_languages.includes(lang)) {
      updateField('programming_languages', [...data.programming_languages, lang]);
    }
    setLangInput('');
  };

  const removeLanguage = (lang: string) => {
    updateField('programming_languages', data.programming_languages.filter(l => l !== lang));
  };

  const toggleDocPurpose = (purpose: string) => {
    const purposes = data.documentation_purpose || [];
    if (purposes.includes(purpose)) {
      updateField('documentation_purpose', purposes.filter(p => p !== purpose));
    } else {
      updateField('documentation_purpose', [...purposes, purpose]);
    }
  };

  const toggleSection = (section: string) => {
    const sections = data.include_sections || [];
    if (sections.includes(section)) {
      updateField('include_sections', sections.filter(s => s !== section));
    } else {
      updateField('include_sections', [...sections, section]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-100 rounded-lg">
          <Code className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Technical Documentation Details</h2>
          <p className="text-sm text-gray-600">Specify technical requirements and scope</p>
        </div>
      </div>

      {/* Software Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Software/Project Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.software_name}
          onChange={(e) => updateField('software_name', e.target.value)}
          placeholder="e.g., DocForge API, React Dashboard, ML Pipeline"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Project Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Project Description <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.project_description}
          onChange={(e) => updateField('project_description', e.target.value)}
          placeholder="Brief overview of what the software does and its main features"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Technologies */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Technologies <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={techInput}
              onChange={(e) => setTechInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addTechnology(techInput);
                }
              }}
              placeholder="Type or select a technology"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => addTechnology(techInput)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add
            </button>
          </div>
          
          {/* Quick select common technologies */}
          <div className="flex flex-wrap gap-2">
            {TECH_OPTIONS.map((tech) => (
              <button
                key={tech}
                type="button"
                onClick={() => addTechnology(tech)}
                disabled={data.technologies.includes(tech)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {tech}
              </button>
            ))}
          </div>

          {/* Selected technologies */}
          {data.technologies.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {data.technologies.map((tech) => (
                <span
                  key={tech}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                >
                  {tech}
                  <button
                    type="button"
                    onClick={() => removeTechnology(tech)}
                    className="hover:text-blue-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Programming Languages */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Programming Languages <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={langInput}
              onChange={(e) => setLangInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addLanguage(langInput);
                }
              }}
              placeholder="Type or select a language"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => addLanguage(langInput)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add
            </button>
          </div>
          
          {/* Quick select common languages */}
          <div className="flex flex-wrap gap-2">
            {LANGUAGE_OPTIONS.map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => addLanguage(lang)}
                disabled={data.programming_languages.includes(lang)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {lang}
              </button>
            ))}
          </div>

          {/* Selected languages */}
          {data.programming_languages.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {data.programming_languages.map((lang) => (
                <span
                  key={lang}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                >
                  {lang}
                  <button
                    type="button"
                    onClick={() => removeLanguage(lang)}
                    className="hover:text-green-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Target Technical Audience */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Users className="w-4 h-4 inline mr-1" />
          Target Technical Audience <span className="text-red-500">*</span>
        </label>
        <select
          value={data.target_technical_audience}
          onChange={(e) => updateField('target_technical_audience', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="beginners">Beginners (Little to no experience)</option>
          <option value="intermediate">Intermediate (Some experience)</option>
          <option value="advanced">Advanced (Expert developers)</option>
        </select>
      </div>

      {/* Documentation Purpose */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Book className="w-4 h-4 inline mr-1" />
          Documentation Purpose <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          {['API Documentation', 'User Guide', 'Architecture Overview', 'Setup Instructions'].map((purpose) => (
            <label key={purpose} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={data.documentation_purpose?.includes(purpose)}
                onChange={() => toggleDocPurpose(purpose)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-gray-700">{purpose}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Include Sections */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Include Sections
        </label>
        <div className="space-y-2">
          {['Installation', 'API Reference', 'Code Examples', 'Architecture', 'Troubleshooting', 'Contributing'].map((section) => (
            <label key={section} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={data.include_sections?.includes(section)}
                onChange={() => toggleSection(section)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-gray-700">{section}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Prerequisites */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Prerequisites
        </label>
        <textarea
          value={data.prerequisites || ''}
          onChange={(e) => updateField('prerequisites', e.target.value)}
          placeholder="What should users know or have installed before using this documentation?"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Known Limitations */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Known Limitations <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <textarea
          value={data.known_limitations || ''}
          onChange={(e) => updateField('known_limitations', e.target.value)}
          placeholder="Any known issues, constraints, or limitations to document"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        />
      </div>
    </div>
  );
}
