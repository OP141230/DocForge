interface Step3Props {
  desiredLength: string;
  tone: string;
  writingStyle: string;
  onChange: (field: string, value: string) => void;
}

interface OptionCard {
  value: string;
  label: string;
  description: string;
}

const lengthOptions: OptionCard[] = [
  {
    value: 'short',
    label: 'Short',
    description: '1-2 pages, brief and concise',
  },
  {
    value: 'medium',
    label: 'Medium',
    description: '3-5 pages, balanced coverage',
  },
  {
    value: 'long',
    label: 'Long',
    description: '6-10 pages, comprehensive',
  },
  {
    value: 'very_long',
    label: 'Very Long',
    description: '10+ pages, exhaustive detail',
  },
];

const toneOptions: OptionCard[] = [
  {
    value: 'professional',
    label: 'Professional',
    description: 'Business-appropriate and polished',
  },
  {
    value: 'casual',
    label: 'Casual',
    description: 'Relaxed and conversational',
  },
  {
    value: 'formal',
    label: 'Formal',
    description: 'Academic and structured',
  },
  {
    value: 'friendly',
    label: 'Friendly',
    description: 'Warm and approachable',
  },
  {
    value: 'technical',
    label: 'Technical',
    description: 'Precise and specialized',
  },
];

export function Step3_Preferences({
  desiredLength,
  tone,
  writingStyle,
  onChange,
}: Step3Props) {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Document Preferences</h2>
        <p className="text-gray-600">Customize how your document should be written</p>
      </div>

      {/* Desired Length */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Desired Length <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {lengthOptions.map((option) => {
            const isSelected = desiredLength === option.value;
            return (
              <button
                key={option.value}
                onClick={() => onChange('desired_length', option.value)}
                className={`
                  p-4 rounded-lg border-2 transition-all duration-200 text-left
                  hover:shadow-md hover:scale-105
                  ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-blue-300'
                  }
                `}
              >
                <div className={`font-semibold mb-1 ${isSelected ? 'text-blue-600' : 'text-gray-900'}`}>
                  {option.label}
                </div>
                <div className="text-xs text-gray-500">{option.description}</div>
              </button>
            );
          })}
        </div>
        {!desiredLength && (
          <p className="text-sm text-red-600 mt-2">Please select a desired length</p>
        )}
      </div>

      {/* Tone */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Tone <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {toneOptions.map((option) => {
            const isSelected = tone === option.value;
            return (
              <button
                key={option.value}
                onClick={() => onChange('tone', option.value)}
                className={`
                  p-4 rounded-lg border-2 transition-all duration-200 text-left
                  hover:shadow-md hover:scale-105
                  ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-blue-300'
                  }
                `}
              >
                <div className={`font-semibold mb-1 ${isSelected ? 'text-blue-600' : 'text-gray-900'}`}>
                  {option.label}
                </div>
                <div className="text-xs text-gray-500">{option.description}</div>
              </button>
            );
          })}
        </div>
        {!tone && (
          <p className="text-sm text-red-600 mt-2">Please select a tone</p>
        )}
      </div>

      {/* Writing Style (Optional) */}
      <div>
        <label htmlFor="writingStyle" className="block text-sm font-medium text-gray-700 mb-1">
          Writing Style (Optional)
        </label>
        <input
          id="writingStyle"
          type="text"
          value={writingStyle}
          onChange={(e) => onChange('writing_style', e.target.value)}
          maxLength={100}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g., Concise bullet points, storytelling approach, data-driven"
        />
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500">Any specific writing style preferences?</span>
          <span className="text-xs text-gray-400">{writingStyle.length}/100</span>
        </div>
      </div>
    </div>
  );
}
