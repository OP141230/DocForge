import { useState } from 'react';
import { PenTool, Plus, Trash2 } from 'lucide-react';
import type { EssayArticleData } from './FieldRegistry';

interface EssayArticleFieldsProps {
  data: EssayArticleData;
  onChange: (data: EssayArticleData) => void;
}

export function EssayArticleFields({ data, onChange }: EssayArticleFieldsProps) {
  const [newArgument, setNewArgument] = useState('');
  const [newExample, setNewExample] = useState('');

  const updateField = (field: keyof EssayArticleData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  const addArgument = () => {
    if (newArgument.trim()) {
      updateField('main_arguments', [...data.main_arguments, newArgument.trim()]);
      setNewArgument('');
    }
  };

  const removeArgument = (index: number) => {
    updateField('main_arguments', data.main_arguments.filter((_, i) => i !== index));
  };

  const addExample = () => {
    if (newExample.trim()) {
      updateField('examples_to_include', [...data.examples_to_include, newExample.trim()]);
      setNewExample('');
    }
  };

  const removeExample = (index: number) => {
    updateField('examples_to_include', data.examples_to_include.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-amber-100 rounded-lg">
          <PenTool className="w-6 h-6 text-amber-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Essay/Article Details</h2>
          <p className="text-sm text-gray-600">Define your argument and supporting points</p>
        </div>
      </div>

      {/* Central Argument */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Central Argument/Thesis <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.central_argument}
          onChange={(e) => updateField('central_argument', e.target.value)}
          placeholder="What is the main point or argument you want to make?"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Target Publication */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Publication <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <input
          type="text"
          value={data.target_publication || ''}
          onChange={(e) => updateField('target_publication', e.target.value)}
          placeholder="e.g., Medium, The Atlantic, Personal Blog"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
        />
      </div>

      {/* Publication Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Publication Type <span className="text-red-500">*</span>
        </label>
        <select
          value={data.publication_type}
          onChange={(e) => updateField('publication_type', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
        >
          <option value="blog">Blog Post</option>
          <option value="magazine">Magazine Article</option>
          <option value="journal">Journal Article</option>
          <option value="website">Website Content</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* Main Arguments */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Main Arguments/Supporting Points <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newArgument}
              onChange={(e) => setNewArgument(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addArgument();
                }
              }}
              placeholder="Add a supporting argument or key point"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addArgument}
              className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>

          {/* List of arguments */}
          {data.main_arguments.length > 0 ? (
            <div className="space-y-2 mt-3">
              {data.main_arguments.map((arg, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg"
                >
                  <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-amber-600 text-white rounded-full text-sm">
                    {index + 1}
                  </span>
                  <p className="flex-1 text-gray-700">{arg}</p>
                  <button
                    type="button"
                    onClick={() => removeArgument(index)}
                    className="flex-shrink-0 p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 mt-2">
              Add at least one main argument or supporting point
            </p>
          )}
        </div>
      </div>

      {/* Examples to Include */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Examples to Include
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newExample}
              onChange={(e) => setNewExample(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addExample();
                }
              }}
              placeholder="Add an example, case study, or illustration"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addExample}
              className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>

          {/* List of examples */}
          {data.examples_to_include.length > 0 && (
            <div className="space-y-2 mt-3">
              {data.examples_to_include.map((example, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-2 bg-gray-50 border border-gray-200 rounded-lg"
                >
                  <p className="flex-1 text-gray-700">{example}</p>
                  <button
                    type="button"
                    onClick={() => removeExample(index)}
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

      {/* Required Structure */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Required Structure <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.required_structure}
          onChange={(e) => updateField('required_structure', e.target.value)}
          placeholder="e.g., Introduction, Body Paragraphs, Conclusion"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
        />
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
          placeholder="e.g., 1500"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
        />
      </div>
    </div>
  );
}
