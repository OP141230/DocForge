import { useState } from 'react';
import { Briefcase, Plus, Trash2 } from 'lucide-react';
import type { BusinessDocData } from './FieldRegistry';

interface BusinessFieldsProps {
  data: BusinessDocData;
  onChange: (data: BusinessDocData) => void;
}

export function BusinessFields({ data, onChange }: BusinessFieldsProps) {
  const [newAnalysisPoint, setNewAnalysisPoint] = useState('');
  const [newSection, setNewSection] = useState('');

  const updateField = (field: keyof BusinessDocData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  const addAnalysisPoint = () => {
    if (newAnalysisPoint.trim()) {
      updateField('key_analysis_points', [...data.key_analysis_points, newAnalysisPoint.trim()]);
      setNewAnalysisPoint('');
    }
  };

  const removeAnalysisPoint = (index: number) => {
    updateField('key_analysis_points', data.key_analysis_points.filter((_, i) => i !== index));
  };

  const addSection = () => {
    if (newSection.trim()) {
      updateField('required_sections', [...data.required_sections, newSection.trim()]);
      setNewSection('');
    }
  };

  const removeSection = (index: number) => {
    updateField('required_sections', data.required_sections.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-emerald-100 rounded-lg">
          <Briefcase className="w-6 h-6 text-emerald-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Business Document Details</h2>
          <p className="text-sm text-gray-600">Define business context and requirements</p>
        </div>
      </div>

      {/* Business Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Business/Organization Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.business_name}
          onChange={(e) => updateField('business_name', e.target.value)}
          placeholder="e.g., Acme Corporation, XYZ Startup"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        />
      </div>

      {/* Organization Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Organization Type <span className="text-red-500">*</span>
        </label>
        <select
          value={data.organization_type}
          onChange={(e) => updateField('organization_type', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        >
          <option value="startup">Startup</option>
          <option value="enterprise">Enterprise</option>
          <option value="nonprofit">Nonprofit</option>
          <option value="government">Government</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* Document Purpose */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Document Purpose <span className="text-red-500">*</span>
        </label>
        <select
          value={data.document_purpose}
          onChange={(e) => updateField('document_purpose', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
        >
          <option value="proposal">Proposal</option>
          <option value="report">Report</option>
          <option value="plan">Business Plan</option>
          <option value="analysis">Analysis</option>
          <option value="memo">Memo</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* Business Context */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Business Context <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.business_context}
          onChange={(e) => updateField('business_context', e.target.value)}
          placeholder="Provide relevant background, market conditions, and context"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Scope */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Scope <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.scope}
          onChange={(e) => updateField('scope', e.target.value)}
          placeholder="What does this document cover? What are the boundaries?"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Key Analysis Points */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Key Analysis Points <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newAnalysisPoint}
              onChange={(e) => setNewAnalysisPoint(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addAnalysisPoint();
                }
              }}
              placeholder="e.g., Market analysis, Financial projections, SWOT"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addAnalysisPoint}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>

          {/* List of analysis points */}
          {data.key_analysis_points.length > 0 ? (
            <div className="space-y-2 mt-3">
              {data.key_analysis_points.map((point, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-2 bg-emerald-50 border border-emerald-200 rounded-lg"
                >
                  <span className="flex-1 text-gray-700">{point}</span>
                  <button
                    type="button"
                    onClick={() => removeAnalysisPoint(index)}
                    className="flex-shrink-0 p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 mt-2">
              Add at least one key analysis point
            </p>
          )}
        </div>
      </div>

      {/* Recommendations */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Recommendations <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <textarea
          value={data.recommendations || ''}
          onChange={(e) => updateField('recommendations', e.target.value)}
          placeholder="Key recommendations or proposed actions"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Formality Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Formality Level <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          {[
            { value: 'formal', label: 'Formal', desc: 'Traditional business language, suitable for executives and external stakeholders' },
            { value: 'semi-formal', label: 'Semi-formal', desc: 'Professional but conversational, suitable for team communications' },
            { value: 'informal', label: 'Informal', desc: 'Casual and direct, suitable for internal memos and quick updates' },
          ].map((option) => (
            <label key={option.value} className="flex items-start gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
              <input
                type="radio"
                name="formality"
                value={option.value}
                checked={data.formality_level === option.value}
                onChange={(e) => updateField('formality_level', e.target.value)}
                className="mt-1 w-4 h-4 text-emerald-600 border-gray-300 focus:ring-emerald-500"
              />
              <div>
                <div className="font-medium text-gray-900">{option.label}</div>
                <div className="text-sm text-gray-600">{option.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Required Sections */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Required Sections
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newSection}
              onChange={(e) => setNewSection(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addSection();
                }
              }}
              placeholder="e.g., Executive Summary, Financial Analysis"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addSection}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>

          {/* List of sections */}
          {data.required_sections.length > 0 && (
            <div className="space-y-2 mt-3">
              {data.required_sections.map((section, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-2 bg-gray-50 border border-gray-200 rounded-lg"
                >
                  <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-emerald-600 text-white rounded-full text-sm">
                    {index + 1}
                  </span>
                  <span className="flex-1 text-gray-700">{section}</span>
                  <button
                    type="button"
                    onClick={() => removeSection(index)}
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
