import { useState } from 'react';
import { FileText, Plus, Trash2 } from 'lucide-react';
import type { GeneralDocData } from './FieldRegistry';

interface GeneralFieldsProps {
  data: GeneralDocData;
  onChange: (data: GeneralDocData) => void;
}

export function GeneralFields({ data, onChange }: GeneralFieldsProps) {
  const [newTopic, setNewTopic] = useState('');

  const updateField = (field: keyof GeneralDocData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  const addTopic = () => {
    if (newTopic.trim()) {
      updateField('key_topics', [...data.key_topics, newTopic.trim()]);
      setNewTopic('');
    }
  };

  const removeTopic = (index: number) => {
    updateField('key_topics', data.key_topics.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gray-100 rounded-lg">
          <FileText className="w-6 h-6 text-gray-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">General Document Details</h2>
          <p className="text-sm text-gray-600">Define structure and key topics</p>
        </div>
      </div>

      {/* Flexible Structure */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Document Structure <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.flexible_structure}
          onChange={(e) => updateField('flexible_structure', e.target.value)}
          placeholder="Describe the desired structure of your document (e.g., Introduction, Main Content, Conclusion)"
          rows={5}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent resize-none"
        />
        <p className="text-xs text-gray-500 mt-1">
          Provide a clear outline of how you want your document organized
        </p>
      </div>

      {/* Key Topics */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Key Topics to Cover <span className="text-red-500">*</span>
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addTopic();
                }
              }}
              placeholder="Add a topic or theme to include"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addTopic}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>

          {/* List of topics */}
          {data.key_topics.length > 0 ? (
            <div className="space-y-2 mt-3">
              {data.key_topics.map((topic, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 p-3 bg-gray-50 border border-gray-200 rounded-lg"
                >
                  <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-gray-600 text-white rounded-full text-sm">
                    {index + 1}
                  </span>
                  <p className="flex-1 text-gray-700">{topic}</p>
                  <button
                    type="button"
                    onClick={() => removeTopic(index)}
                    className="flex-shrink-0 p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 mt-2">
              Add at least one key topic to cover in your document
            </p>
          )}
        </div>
      </div>

      {/* Special Formatting Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Special Formatting Notes <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <textarea
          value={data.special_formatting_notes || ''}
          onChange={(e) => updateField('special_formatting_notes', e.target.value)}
          placeholder="Any specific formatting requirements or stylistic preferences (e.g., use of headers, bullet points, tables)"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-500 focus:border-transparent resize-none"
        />
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> The General document type offers maximum flexibility. You can use the 
          basic information fields (title, topic, purpose) along with these fields to create any type 
          of document that doesn't fit the specialized categories.
        </p>
      </div>
    </div>
  );
}
