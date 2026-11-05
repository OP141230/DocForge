import { useState } from 'react';
import { Loader2, Edit2, RefreshCw, CheckCircle, FileText, AlertCircle, Plus, X, ChevronUp, ChevronDown, Save, XCircle } from 'lucide-react';
import type { OutlineItem } from '../../types/document_brief';
import { api } from '../../api/client';

interface Step6Props {
  briefId: string | null;
  initialOutline: OutlineItem[];
  isApproved: boolean;
  onOutlineGenerated: (outline: OutlineItem[]) => void;
  onOutlineUpdated: (outline: OutlineItem[]) => void;
  onApproved: () => void;
  onDocumentGenerated: () => void;
}

export function Step6_OutlineApproval_New({
  briefId,
  initialOutline,
  isApproved,
  onOutlineGenerated,
  onOutlineUpdated,
  onApproved,
  onDocumentGenerated,
}: Step6Props) {
  const [outline, setOutline] = useState<OutlineItem[]>(initialOutline);
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isGeneratingDoc, setIsGeneratingDoc] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedOutline, setEditedOutline] = useState<OutlineItem[]>([...initialOutline]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSection, setNewSection] = useState({ title: '', level: 1 });

  const hasOutline = outline.length > 0;

  // Generate Outline
  const handleGenerateOutline = async () => {
    if (!briefId) {
      setError('No brief ID available. Please go back and save your brief first.');
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);
      const updatedBrief = await api.generateBriefOutline(briefId);
      const generatedOutline = updatedBrief.outline || [];
      setOutline(generatedOutline);
      setEditedOutline([...generatedOutline]);
      onOutlineGenerated(generatedOutline);
    } catch (err) {
      console.error('Failed to generate outline:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate outline');
    } finally {
      setIsGenerating(false);
    }
  };

  // Regenerate Outline
  const handleRegenerateOutline = async () => {
    if (isApproved) return;
    await handleGenerateOutline();
  };

  // Edit Mode Handlers
  const handleEnterEditMode = () => {
    setEditMode(true);
    setEditedOutline([...outline]);
  };

  const handleCancelEdit = () => {
    setEditMode(false);
    setEditedOutline([...outline]);
    setShowAddForm(false);
    setNewSection({ title: '', level: 1 });
    setError(null);
  };

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

  const handleSaveOutline = async () => {
    if (!briefId) {
      setError('No brief ID available');
      return;
    }

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
      setIsLoading(true);
      setError(null);
      const updatedBrief = await api.updateBriefOutline(briefId, editedOutline);
      const savedOutline = updatedBrief.outline || [];
      setOutline(savedOutline);
      setEditedOutline([...savedOutline]);
      setEditMode(false);
      onOutlineUpdated(savedOutline);
    } catch (err) {
      console.error('Failed to save outline:', err);
      setError(err instanceof Error ? err.message : 'Failed to save outline');
    } finally {
      setIsLoading(false);
    }
  };

  // Approve Outline
  const handleApproveOutline = async () => {
    if (!briefId || !hasOutline) return;

    try {
      setIsApproving(true);
      setError(null);
      await api.approveBriefOutline(briefId);
      onApproved();
    } catch (err) {
      console.error('Failed to approve outline:', err);
      setError(err instanceof Error ? err.message : 'Failed to approve outline');
    } finally {
      setIsApproving(false);
    }
  };

  // Generate Document
  const handleGenerateDocument = async () => {
    if (!briefId || !isApproved) return;

    try {
      setIsGeneratingDoc(true);
      setError(null);
      await api.generateFromBrief(briefId);
      onDocumentGenerated();
    } catch (err) {
      console.error('Failed to generate document:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate document');
    } finally {
      setIsGeneratingDoc(false);
    }
  };

  const renderOutlineDisplay = () => {
    if (!hasOutline) {
      return (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600 text-lg font-medium mb-2">No outline generated yet</p>
          <p className="text-gray-500 text-sm">Click "Generate Outline" to create your document structure</p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {outline.map((item, index) => {
          const levelIndent = (item.level - 1) * 24;
          const levelClass =
            item.level === 1
              ? 'text-lg font-semibold text-gray-900'
              : item.level === 2
              ? 'text-base font-medium text-gray-800'
              : 'text-sm text-gray-700';

          return (
            <div
              key={index}
              className="flex items-start gap-3 py-2 px-3 hover:bg-gray-50 rounded-lg transition-colors"
              style={{ marginLeft: `${levelIndent}px` }}
            >
              <span className="text-gray-400 font-mono text-sm mt-1 flex-shrink-0">
                {index + 1}.
              </span>
              <div className="flex-1">
                <h4 className={levelClass}>{item.title}</h4>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const renderOutlineEditor = () => {
    return (
      <div className="space-y-4">
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
                <span className="text-gray-400 font-mono text-sm mt-3 flex-shrink-0">
                  {index + 1}.
                </span>

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
                </div>

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

        {showAddForm ? (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">Add New Section</h3>
            <div className="space-y-3">
              <input
                type="text"
                value={newSection.title}
                onChange={(e) => setNewSection({ ...newSection, title: e.target.value })}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSection();
                  } else if (e.key === 'Escape') {
                    setShowAddForm(false);
                    setNewSection({ title: '', level: 1 });
                  }
                }}
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
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {editMode ? 'Edit Outline' : 'Document Outline'}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            {editMode
              ? 'Modify sections, reorder, or add new items to your outline'
              : isApproved
              ? 'Outline approved and ready for document generation'
              : hasOutline
              ? 'Review and approve the outline to proceed'
              : 'Generate an outline from your document brief'}
          </p>
        </div>

        {isApproved && !editMode && (
          <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-green-700">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Approved</span>
          </div>
        )}
      </div>

      {/* Outline Display or Editor */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 max-h-[400px] overflow-y-auto">
        {editMode ? renderOutlineEditor() : renderOutlineDisplay()}
      </div>

      {/* Status Messages */}
      {!editMode && !isApproved && hasOutline && (
        <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-800">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Please review and approve the outline before generating your document</p>
            <p className="text-sm mt-1">You can edit the outline or regenerate it if needed.</p>
          </div>
        </div>
      )}

      {isApproved && !editMode && (
        <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
          <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Outline approved successfully!</p>
            <p className="text-sm mt-1">You can now generate the complete document based on this outline.</p>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between gap-3 pt-4 border-t">
        {editMode ? (
          <>
            <button
              onClick={handleCancelEdit}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <XCircle className="w-4 h-4" />
              Cancel
            </button>

            <button
              onClick={handleSaveOutline}
              disabled={isLoading || editedOutline.length === 0}
              className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Save Changes
                </>
              )}
            </button>
          </>
        ) : (
          <>
            <div className="flex items-center gap-3">
              {!hasOutline ? (
                <button
                  onClick={handleGenerateOutline}
                  disabled={isGenerating || !briefId}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Generating Outline...
                    </>
                  ) : (
                    <>
                      <FileText className="w-5 h-5" />
                      Generate Outline
                    </>
                  )}
                </button>
              ) : (
                <>
                  <button
                    onClick={handleEnterEditMode}
                    disabled={isApproved}
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit Outline
                  </button>

                  <button
                    onClick={handleRegenerateOutline}
                    disabled={isGenerating || isApproved}
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
                    Regenerate
                  </button>
                </>
              )}
            </div>

            <div className="flex items-center gap-3">
              {!isApproved && hasOutline ? (
                <button
                  onClick={handleApproveOutline}
                  disabled={isApproving}
                  className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isApproving ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Approving...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      Approve Outline
                    </>
                  )}
                </button>
              ) : isApproved ? (
                <button
                  onClick={handleGenerateDocument}
                  disabled={isGeneratingDoc}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isGeneratingDoc ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Generating Document...
                    </>
                  ) : (
                    <>
                      <FileText className="w-5 h-5" />
                      Generate Document
                    </>
                  )}
                </button>
              ) : null}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
