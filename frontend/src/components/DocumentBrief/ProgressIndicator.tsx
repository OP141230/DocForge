import { Check } from 'lucide-react';

interface ProgressIndicatorProps {
  currentStep: number;
  totalSteps?: number;
  stepLabels?: string[];
  onStepClick?: (step: number) => void;
}

const defaultStepLabels = [
  'Type',
  'Basic Info',
  'Preferences',
  'Details',
  'Instructions',
  'Review',
];

export function ProgressIndicator({
  currentStep,
  totalSteps = 6,
  stepLabels = defaultStepLabels,
  onStepClick,
}: ProgressIndicatorProps) {
  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between">
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step, idx) => {
          const isActive = step === currentStep;
          const isCompleted = step < currentStep;
          const isClickable = isCompleted && onStepClick;

          return (
            <div key={step} className="flex items-center flex-1">
              {/* Step Circle */}
              <div className="flex flex-col items-center relative">
                <button
                  onClick={() => isClickable && onStepClick(step)}
                  disabled={!isClickable}
                  className={`
                    w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold
                    transition-all duration-200 border-2
                    ${
                      isCompleted
                        ? 'bg-blue-600 border-blue-600 text-white hover:bg-blue-700 cursor-pointer'
                        : isActive
                        ? 'bg-white border-blue-600 text-blue-600'
                        : 'bg-white border-gray-300 text-gray-400'
                    }
                    ${isClickable ? 'hover:scale-110' : 'cursor-default'}
                  `}
                >
                  {isCompleted ? <Check className="w-5 h-5" /> : step}
                </button>
                {/* Step Label */}
                <span
                  className={`
                    absolute top-12 text-xs font-medium whitespace-nowrap
                    ${isActive ? 'text-blue-600' : isCompleted ? 'text-gray-700' : 'text-gray-400'}
                  `}
                >
                  {stepLabels[idx]}
                </span>
              </div>

              {/* Connector Line */}
              {idx < totalSteps - 1 && (
                <div
                  className={`
                    flex-1 h-0.5 mx-2 transition-all duration-300
                    ${isCompleted ? 'bg-blue-600' : 'bg-gray-300'}
                  `}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
