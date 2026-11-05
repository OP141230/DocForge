import { useState } from 'react';
import { Plus, X, Save, XCircle, ChevronUp, ChevronDown, AlertCircle } from 'lucide-react';
import type { OutlineItem } from '../../types/document_brief';

interface OutlineEditorProps {
  outline: OutlineItem[];
  onSave: (updatedOutline: OutlineItem[]) => Promise<void>;
  onCancel: () => void;
}

export function OutlineEditor({ outline, onSave, onCancel }: OutlineEditorProps) {
  const [editedOutline, setEditedOutline] = useState<OutlineItem[]>([...outline]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSection, setNewSection] = useState({ title: '', level: 1 });

  const handleUpdateTitle = (index: number, title: string) => {
    const updated = [...editedOutline];
    updated[index] = { ...updated[index], title };
    setEditedOutline(updated);
  };

  const handleUpdateLevel = (index: number, level: number) => {
    const updated = [...editedOutline];
    updated[index] = { ...updated[index], level };
    setEditedOutline(updated);
  };

  const handleRemoveSection = (index: number) => {
    const updated = editedOutline.filter((_, i) => i !== index);
    setEditedOutline(updated);
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const updated = [...editedOutline];
    [updated[index - 1], updated[index]] = [updated[index], updated[index - 1]];
    setEditedOutline(updated);
  };

  const handleMoveDown = (index: number) => {
    if (index === editedOutline.length - 1) return;
    const updated = [...editedOutline];
    [updated[index], updated[index + 1]] = [updated[index + 1], updated[index]];
    setEditedOutline(updated);
  };

  const handleAddSection = () => {
    if (!newSection.title.trim()) {
      setError('Section title cannot be empty');
      return;
    }

    const newItem: OutlineItem = {
      title: newSection.title.trim(),
      level: newSection.level,
    };

    setEditedOutline([...editedOutline, newItem]);
    setNewSection({ title: '', level: 1 });
    setShowAddForm(false);
    setError(null);
  };

  const handleSave = async () => {
    // Validation
    if (editedOutline.length === 0) {
      setError('Outline must have at least one section');
      return;
    }

    const hasEmptyTitles = editedOutline.some((item) => !item.title.trim());
    if (hasEmptyTitles) {
      setError('All sections must have a title');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      await onSave(editedOutline);
    } catch (err) {
      console.error('Failed to save outline:', err);
      setError(err instanceof Error ? err.message : 'Failed to save outline');
    } finally {
      setIsSaving(false);
    }
  };

  const renderLevelBadge = (level: number) => {
    const colors = {
      1: 'bg-blue-100 text-blue-700',
      2: 'bg-green-100 text-green-700',
      3: 'bg-purple-100 text-purple-700',
    };
    const color = colors[level as keyof typeof colors] || 'bg-gray-100 text-gray-700';
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${color}`}>
        Level {level}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Edit Outline</h2>
          <p className="text-sm text-gray-600 mt-1">
            Modify sections, reorder, or add new items to your outline
          </p>
        </div>
      </div>

      {/* Outline Items */}
      <div className="space-y-3">
        {editedOutline.length === 0 ? (
          <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
            <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p className="text-gray-600">No sections yet. Add your first section below.</p>
          </div>
        ) : (
          editedOutline.map((item, index) => (
            <div
              key={index}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start gap-3">
                {/* Section Number */}
                <span className="text-gray-400 font-mono text-sm mt-3 flex-shrink-0">
                  {index + 1}.
                </span>

                {/* Content */}
                <div className="flex-1 space-y-3">
                  <div className="flex items-start gap-3">
                    <input
                      type="text"
                      value={item.title}
                      onChange={(e) => handleUpdateTitle(index, e.target.value)}
                      placeholder="Section title"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />

                    <select
                      value={item.level}
                      onChange={(e) => handleUpdateLevel(index, parseInt(e.target.value))}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value={1}>Level 1</option>
                      <option value={2}>Level 2</option>
                      <option value={3}>Level 3</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-2">
                    {renderLevelBadge(item.level)}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-1">
                  <button
                    onClick={() => handleMoveUp(index)}
                    disabled={index === 0}
                    className="p-1 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Move up"
                  >
                    <ChevronUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleMoveDown(index)}
                    disabled={index === editedOutline.length - 1}
                    className="p-1 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-30 disabled:cursor-not-allowed"
                    title="Move down"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleRemoveSection(index)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded"
                    title="Remove section"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add Section Form */}
      {showAddForm ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-3">Add New Section</h3>
          <div className="space-y-3">
            <input
              type="text"
              value={newSection.title}
              onChange={(e) => setNewSection({ ...newSection, title: e.target.value })}
              placeholder="Section title"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
            />
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-gray-700">Level:</label>
              <select
                value={newSection.level}
                onChange={(e) => setNewSection({ ...newSection, level: parseInt(e.target.value) })}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={1}>Level 1 (Main section)</option>
                <option value={2}>Level 2 (Subsection)</option>
                <option value={3}>Level 3 (Sub-subsection)</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleAddSection}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add Section
              </button>
              <button
                onClick={() => {
                  setShowAddForm(false);
                  setNewSection({ title: '', level: 1 });
                  setError(null);
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 border-2 border-dashed border-gray-300 text-gray-600 rounded-lg hover:border-blue-400 hover:text-blue-600 transition-colors w-full justify-center"
        >
          <Plus className="w-5 h-5" />
          Add Section
        </button>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Save/Cancel Buttons */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t">
        <button
          onClick={onCancel}
          disabled={isSaving}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <XCircle className="w-4 h-4" />
          Cancel
        </button>

        <button
          onClick={handleSave}
          disabled={isSaving || editedOutline.length === 0}
          className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-5 h-5" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}
