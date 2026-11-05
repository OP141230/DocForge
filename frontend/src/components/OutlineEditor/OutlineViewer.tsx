import { Edit2, RefreshCw, CheckCircle, FileText, AlertCircle } from 'lucide-react';
import type { OutlineItem } from '../../types/document_brief';

interface OutlineViewerProps {
  outline: OutlineItem[];
  isApproved: boolean;
  onEdit: () => void;
  onApprove: () => void;
  onRegenerate: () => void;
  onGenerateDocument?: () => void;
  isLoading?: boolean;
}

export function OutlineViewer({
  outline,
  isApproved,
  onEdit,
  onApprove,
  onRegenerate,
  onGenerateDocument,
  isLoading = false,
}: OutlineViewerProps) {
  // Group outline items by level for hierarchical display
  const renderOutlineHierarchy = () => {
    if (!outline || outline.length === 0) {
      return (
        <div className="text-center py-8 text-gray-500">
          <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p>No outline generated yet</p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {outline.map((item, index) => {
          const levelIndent = (item.level - 1) * 24;
          const levelClass = item.level === 1
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Document Outline</h2>
          <p className="text-sm text-gray-600 mt-1">
            {isApproved ? 'Outline approved and ready for document generation' : 'Review and approve the outline'}
          </p>
        </div>

        {isApproved && (
          <div className="flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg text-green-700">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Approved</span>
          </div>
        )}
      </div>

      {/* Outline Display */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        {renderOutlineHierarchy()}
      </div>

      {/* Status Message */}
      {!isApproved && outline && outline.length > 0 && (
        <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-800">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Please review and approve the outline before generating your document</p>
            <p className="text-sm mt-1">You can edit the outline or regenerate it if needed.</p>
          </div>
        </div>
      )}

      {isApproved && (
        <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
          <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Outline approved successfully!</p>
            <p className="text-sm mt-1">You can now generate the complete document based on this outline.</p>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between gap-3 pt-4 border-t">
        <div className="flex items-center gap-3">
          <button
            onClick={onEdit}
            disabled={isLoading || isApproved}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Edit2 className="w-4 h-4" />
            Edit Outline
          </button>

          <button
            onClick={onRegenerate}
            disabled={isLoading || isApproved}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className="w-4 h-4" />
            Regenerate
          </button>
        </div>

        <div className="flex items-center gap-3">
          {!isApproved ? (
            <button
              onClick={onApprove}
              disabled={isLoading || !outline || outline.length === 0}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <CheckCircle className="w-5 h-5" />
              Approve Outline
            </button>
          ) : (
            onGenerateDocument && (
              <button
                onClick={onGenerateDocument}
                disabled={isLoading}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                <FileText className="w-5 h-5" />
                Generate Document
              </button>
            )
          )}
        </div>
      </div>
    </div>
  );
}
