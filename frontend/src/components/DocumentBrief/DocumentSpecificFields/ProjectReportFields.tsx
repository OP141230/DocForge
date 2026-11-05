import { useState } from 'react';
import { FolderKanban, Plus, Trash2 } from 'lucide-react';
import type { ProjectReportData } from './FieldRegistry';

interface ProjectReportFieldsProps {
  data: ProjectReportData;
  onChange: (data: ProjectReportData) => void;
}

const TECH_OPTIONS = [
  'React', 'Vue', 'Angular', 'Node.js', 'Python', 'Java', 'C++', 'C#',
  'Docker', 'Kubernetes', 'AWS', 'Azure', 'PostgreSQL', 'MongoDB', 'Redis',
  'TypeScript', 'JavaScript', 'Go', 'Rust', 'Swift', 'Kotlin'
];

export function ProjectReportFields({ data, onChange }: ProjectReportFieldsProps) {
  const [techInput, setTechInput] = useState('');
  const [newChapter, setNewChapter] = useState('');

  const updateField = (field: keyof ProjectReportData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  const addTechnology = (tech: string) => {
    if (tech && !data.technologies_used.includes(tech)) {
      updateField('technologies_used', [...data.technologies_used, tech]);
    }
    setTechInput('');
  };

  const removeTechnology = (tech: string) => {
    updateField('technologies_used', data.technologies_used.filter(t => t !== tech));
  };

  const addChapter = () => {
    if (newChapter.trim()) {
      updateField('required_chapters', [...data.required_chapters, newChapter.trim()]);
      setNewChapter('');
    }
  };

  const removeChapter = (index: number) => {
    updateField('required_chapters', data.required_chapters.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-indigo-100 rounded-lg">
          <FolderKanban className="w-6 h-6 text-indigo-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Project Report Details</h2>
          <p className="text-sm text-gray-600">Document your project comprehensively</p>
        </div>
      </div>

      {/* Project Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Project Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.project_name}
          onChange={(e) => updateField('project_name', e.target.value)}
          placeholder="e.g., E-Commerce Platform, ML Image Classifier"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
      </div>

      {/* Project Objective */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Project Objective <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.project_objective}
          onChange={(e) => updateField('project_objective', e.target.value)}
          placeholder="What is the goal of this project?"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Problem Statement */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Problem Statement <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.problem_statement}
          onChange={(e) => updateField('problem_statement', e.target.value)}
          placeholder="What problem does this project solve?"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Technologies Used */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Technologies Used <span className="text-red-500">*</span>
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
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => addTechnology(techInput)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
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
                disabled={data.technologies_used.includes(tech)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {tech}
              </button>
            ))}
          </div>

          {/* Selected technologies */}
          {data.technologies_used.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {data.technologies_used.map((tech) => (
                <span
                  key={tech}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm"
                >
                  {tech}
                  <button
                    type="button"
                    onClick={() => removeTechnology(tech)}
                    className="hover:text-indigo-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Team Size and Roles */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Team Size <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={data.team_size}
            onChange={(e) => updateField('team_size', parseInt(e.target.value) || 1)}
            min="1"
            placeholder="e.g., 4"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Team Roles <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={data.team_roles}
            onChange={(e) => updateField('team_roles', e.target.value)}
            placeholder="e.g., Frontend Dev, Backend Dev, Designer"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Methodology */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Methodology <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.methodology}
          onChange={(e) => updateField('methodology', e.target.value)}
          placeholder="Describe the development methodology used (e.g., Agile, Waterfall, Scrum)"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Implementation Details */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Implementation Details <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.implementation_details}
          onChange={(e) => updateField('implementation_details', e.target.value)}
          placeholder="How was the project implemented? What were the key technical decisions?"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Results Summary */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Results Summary <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.results_summary}
          onChange={(e) => updateField('results_summary', e.target.value)}
          placeholder="What were the outcomes and achievements?"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Limitations */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Limitations <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <textarea
          value={data.limitations || ''}
          onChange={(e) => updateField('limitations', e.target.value)}
          placeholder="Any constraints or limitations encountered"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Future Scope */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Future Scope <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <textarea
          value={data.future_scope || ''}
          onChange={(e) => updateField('future_scope', e.target.value)}
          placeholder="Potential improvements and future enhancements"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Required Chapters */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Required Chapters
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newChapter}
              onChange={(e) => setNewChapter(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addChapter();
                }
              }}
              placeholder="e.g., Literature Review, System Architecture"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addChapter}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>

          {/* List of chapters */}
          {data.required_chapters.length > 0 && (
            <div className="space-y-2 mt-3">
              {data.required_chapters.map((chapter, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-2 bg-indigo-50 border border-indigo-200 rounded-lg"
                >
                  <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-indigo-600 text-white rounded-full text-sm">
                    {index + 1}
                  </span>
                  <p className="flex-1 text-gray-700">{chapter}</p>
                  <button
                    type="button"
                    onClick={() => removeChapter(index)}
                    className="flex-shrink-0 p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
