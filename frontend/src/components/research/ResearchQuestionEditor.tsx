import { useState } from 'react';
import { api } from '../../api/client';
import { ResearchSessionDetail, ResearchQuestion } from '../../types/research';

interface ResearchQuestionEditorProps {
  session: ResearchSessionDetail;
  onUpdate: () => void;
}

export default function ResearchQuestionEditor({ session, onUpdate }: ResearchQuestionEditorProps) {
  const [questions, setQuestions] = useState<ResearchQuestion[]>(session.questions);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateQuestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.planResearchQuestions(session.session.id);
      setQuestions(response.questions);
      setIsEditing(true);
      onUpdate();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQuestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const questionsData = questions.map((q) => ({
        question_text: q.question_text,
      }));
      await api.updateResearchQuestions(session.session.id, questionsData);
      setIsEditing(false);
      onUpdate();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddQuestion = () => {
    const newQuestion: ResearchQuestion = {
      id: `temp-${Date.now()}`,
      session_id: session.session.id,
      user_id: '',
      question_text: '',
      order_index: questions.length,
      created_at: new Date().toISOString(),
    };
    setQuestions([...questions, newQuestion]);
  };

  const handleUpdateQuestion = (index: number, text: string) => {
    const updated = [...questions];
    updated[index] = { ...updated[index], question_text: text };
    setQuestions(updated);
  };

  const handleDeleteQuestion = (index: number) => {
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const updated = [...questions];
    [updated[index - 1], updated[index]] = [updated[index], updated[index - 1]];
    updated.forEach((q, i) => (q.order_index = i));
    setQuestions(updated);
  };

  const handleMoveDown = (index: number) => {
    if (index === questions.length - 1) return;
    const updated = [...questions];
    [updated[index], updated[index + 1]] = [updated[index + 1], updated[index]];
    updated.forEach((q, i) => (q.order_index = i));
    setQuestions(updated);
  };

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium text-gray-700">Research Questions</h3>
          <p className="text-xs text-gray-500 mt-1">
            Define questions to guide the research process
          </p>
        </div>
        <div className="flex gap-2">
          {!isEditing && questions.length === 0 && session.session.brief_id && (
            <button
              onClick={handleGenerateQuestions}
              disabled={loading}
              className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              Generate from Brief
            </button>
          )}
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              disabled={loading}
              className="px-3 py-1.5 bg-gray-600 text-white text-sm font-medium rounded hover:bg-gray-700 disabled:opacity-50 transition-colors"
            >
              Edit Questions
            </button>
          )}
          {isEditing && (
            <>
              <button
                onClick={() => {
                  setQuestions(session.questions);
                  setIsEditing(false);
                  setError(null);
                }}
                disabled={loading}
                className="px-3 py-1.5 text-gray-700 text-sm font-medium rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveQuestions}
                disabled={loading || questions.length === 0 || questions.some((q) => !q.question_text.trim())}
                className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                Save
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {!loading && questions.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded border-2 border-dashed border-gray-300">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-white border border-gray-200 mb-3">
            <svg
              className="w-6 h-6 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p className="text-sm text-gray-500">No research questions yet</p>
          <p className="text-xs text-gray-400 mt-1">
            {session.session.brief_id
              ? 'Generate questions from your brief or add them manually'
              : 'Click "Edit Questions" to add questions manually'}
          </p>
        </div>
      )}

      {!loading && questions.length > 0 && (
        <div className="space-y-3">
          {questions.map((question, index) => (
            <div
              key={question.id}
              className="p-3 bg-white border border-gray-200 rounded"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  {isEditing ? (
                    <textarea
                      value={question.question_text}
                      onChange={(e) => handleUpdateQuestion(index, e.target.value)}
                      placeholder="Enter research question..."
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  ) : (
                    <p className="text-sm text-gray-900">{question.question_text}</p>
                  )}
                </div>
                {isEditing && (
                  <div className="flex-shrink-0 flex flex-col gap-1">
                    <button
                      onClick={() => handleMoveUp(index)}
                      disabled={index === 0}
                      className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                      title="Move up"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleMoveDown(index)}
                      disabled={index === questions.length - 1}
                      className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                      title="Move down"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleDeleteQuestion(index)}
                      className="p-1 text-red-400 hover:text-red-600"
                      title="Delete"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isEditing && (
            <button
              onClick={handleAddQuestion}
              className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded text-sm text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
            >
              + Add Question
            </button>
          )}
        </div>
      )}
    </div>
  );
}
