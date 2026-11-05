import { useState } from 'react';
import { Beaker, Plus } from 'lucide-react';
import type { ResearchPaperData } from './FieldRegistry';

interface ResearchPaperFieldsProps {
  data: ResearchPaperData;
  onChange: (data: ResearchPaperData) => void;
}

const DATA_COLLECTION_METHODS = [
  'Surveys', 'Interviews', 'Experiments', 'Observations', 'Case Studies',
  'Literature Review', 'Focus Groups', 'Content Analysis', 'Statistical Analysis'
];

export function ResearchPaperFields({ data, onChange }: ResearchPaperFieldsProps) {
  const [methodInput, setMethodInput] = useState('');
  const [newKeyword, setNewKeyword] = useState('');

  const updateField = (field: keyof ResearchPaperData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  const addDataCollectionMethod = (method: string) => {
    if (method && !data.data_collection_methods.includes(method)) {
      updateField('data_collection_methods', [...data.data_collection_methods, method]);
    }
    setMethodInput('');
  };

  const removeDataCollectionMethod = (method: string) => {
    updateField('data_collection_methods', data.data_collection_methods.filter(m => m !== method));
  };

  const addKeyword = () => {
    if (newKeyword.trim() && !data.keywords.includes(newKeyword.trim())) {
      updateField('keywords', [...data.keywords, newKeyword.trim()]);
      setNewKeyword('');
    }
  };

  const removeKeyword = (index: number) => {
    updateField('keywords', data.keywords.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-rose-100 rounded-lg">
          <Beaker className="w-6 h-6 text-rose-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Research Paper Details</h2>
          <p className="text-sm text-gray-600">Define your research methodology and findings</p>
        </div>
      </div>

      {/* Research Topic */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Research Topic <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.research_topic}
          onChange={(e) => updateField('research_topic', e.target.value)}
          placeholder="e.g., Impact of AI on Healthcare"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
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
          placeholder="What is the main research question you are investigating?"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Hypothesis */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Hypothesis <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.hypothesis}
          onChange={(e) => updateField('hypothesis', e.target.value)}
          placeholder="State your research hypothesis or expected outcome"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Research Methodology */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Research Methodology <span className="text-red-500">*</span>
        </label>
        <select
          value={data.research_methodology}
          onChange={(e) => updateField('research_methodology', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
        >
          <option value="qualitative">Qualitative</option>
          <option value="quantitative">Quantitative</option>
          <option value="mixed">Mixed Methods</option>
        </select>
      </div>

      {/* Data Collection Methods */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Data Collection Methods <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={methodInput}
              onChange={(e) => setMethodInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addDataCollectionMethod(methodInput);
                }
              }}
              placeholder="Type or select a method"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => addDataCollectionMethod(methodInput)}
              className="px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors"
            >
              Add
            </button>
          </div>
          
          {/* Quick select common methods */}
          <div className="flex flex-wrap gap-2">
            {DATA_COLLECTION_METHODS.map((method) => (
              <button
                key={method}
                type="button"
                onClick={() => addDataCollectionMethod(method)}
                disabled={data.data_collection_methods.includes(method)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {method}
              </button>
            ))}
          </div>

          {/* Selected methods */}
          {data.data_collection_methods.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {data.data_collection_methods.map((method) => (
                <span
                  key={method}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-rose-100 text-rose-700 rounded-full text-sm"
                >
                  {method}
                  <button
                    type="button"
                    onClick={() => removeDataCollectionMethod(method)}
                    className="hover:text-rose-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Sample Size */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Sample Size <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.sample_size}
          onChange={(e) => updateField('sample_size', e.target.value)}
          placeholder="e.g., 100 participants, N=250"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
        />
      </div>

      {/* Key Findings */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Key Findings <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.key_findings}
          onChange={(e) => updateField('key_findings', e.target.value)}
          placeholder="Summarize the main findings of your research"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Limitations */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Limitations <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.limitations}
          onChange={(e) => updateField('limitations', e.target.value)}
          placeholder="Describe any limitations or constraints of your research"
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Implications */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Implications <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.implications}
          onChange={(e) => updateField('implications', e.target.value)}
          placeholder="What are the implications of your findings?"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent resize-none"
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
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
        >
          <option value="APA">APA (American Psychological Association)</option>
          <option value="MLA">MLA (Modern Language Association)</option>
          <option value="Chicago">Chicago/Turabian</option>
          <option value="IEEE">IEEE</option>
          <option value="Nature">Nature</option>
        </select>
      </div>

      {/* Keywords */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Keywords <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addKeyword();
                }
              }}
              placeholder="Add a keyword"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addKeyword}
              className="px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>

          {/* List of keywords */}
          {data.keywords.length > 0 ? (
            <div className="flex flex-wrap gap-2 mt-3">
              {data.keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-rose-100 text-rose-700 rounded-full text-sm"
                >
                  {keyword}
                  <button
                    type="button"
                    onClick={() => removeKeyword(index)}
                    className="hover:text-rose-900"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 mt-2">
              Add at least one keyword for your research
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
