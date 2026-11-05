import { useState } from 'react';

interface Step2Props {
  title: string;
  topic: string;
  purpose: string;
  audience: string;
  language: string;
  onChange: (field: string, value: string) => void;
}

const audienceOptions = [
  { value: '', label: 'Select audience...' },
  { value: 'general', label: 'General Audience' },
  { value: 'technical', label: 'Technical Audience' },
  { value: 'academic', label: 'Academic Audience' },
  { value: 'business', label: 'Business Audience' },
  { value: 'students', label: 'Students' },
  { value: 'professionals', label: 'Professionals' },
  { value: 'researchers', label: 'Researchers' },
];

const languageOptions = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'other', label: 'Other' },
];

export function Step2_BasicInfo({
  title,
  topic,
  purpose,
  audience,
  language,
  onChange,
}: Step2Props) {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (field: string, value: string) => {
    const newErrors = { ...errors };

    switch (field) {
      case 'title':
        if (!value.trim()) {
          newErrors.title = 'Title is required';
        } else if (value.length > 200) {
          newErrors.title = 'Title must be 200 characters or less';
        } else {
          delete newErrors.title;
        }
        break;
      case 'topic':
        if (!value.trim()) {
          newErrors.topic = 'Topic is required';
        } else if (value.length > 500) {
          newErrors.topic = 'Topic must be 500 characters or less';
        } else {
          delete newErrors.topic;
        }
        break;
      case 'purpose':
        if (!value.trim()) {
          newErrors.purpose = 'Purpose is required';
        } else if (value.length > 300) {
          newErrors.purpose = 'Purpose must be 300 characters or less';
        } else {
          delete newErrors.purpose;
        }
        break;
      case 'audience':
        if (!value) {
          newErrors.audience = 'Audience is required';
        } else {
          delete newErrors.audience;
        }
        break;
    }

    setErrors(newErrors);
  };

  const handleChange = (field: string, value: string) => {
    onChange(field, value);
    validate(field, value);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Basic Information</h2>
        <p className="text-gray-600">Tell us about your document</p>
      </div>

      <div className="space-y-5">
        {/* Title */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Document Title <span className="text-red-500">*</span>
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => handleChange('title', e.target.value)}
            onBlur={(e) => validate('title', e.target.value)}
            maxLength={200}
            className={`
              w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2
              ${errors.title ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
            `}
            placeholder="Enter document title"
          />
          <div className="flex justify-between mt-1">
            {errors.title ? (
              <span className="text-sm text-red-600">{errors.title}</span>
            ) : (
              <span className="text-xs text-gray-500">Give your document a clear title</span>
            )}
            <span className="text-xs text-gray-400">{title.length}/200</span>
          </div>
        </div>

        {/* Topic */}
        <div>
          <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-1">
            Topic <span className="text-red-500">*</span>
          </label>
          <textarea
            id="topic"
            value={topic}
            onChange={(e) => handleChange('topic', e.target.value)}
            onBlur={(e) => validate('topic', e.target.value)}
            maxLength={500}
            rows={3}
            className={`
              w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2
              ${errors.topic ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
            `}
            placeholder="Describe the main topic or subject"
          />
          <div className="flex justify-between mt-1">
            {errors.topic ? (
              <span className="text-sm text-red-600">{errors.topic}</span>
            ) : (
              <span className="text-xs text-gray-500">What is this document about?</span>
            )}
            <span className="text-xs text-gray-400">{topic.length}/500</span>
          </div>
        </div>

        {/* Purpose */}
        <div>
          <label htmlFor="purpose" className="block text-sm font-medium text-gray-700 mb-1">
            Purpose <span className="text-red-500">*</span>
          </label>
          <textarea
            id="purpose"
            value={purpose}
            onChange={(e) => handleChange('purpose', e.target.value)}
            onBlur={(e) => validate('purpose', e.target.value)}
            maxLength={300}
            rows={3}
            className={`
              w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2
              ${errors.purpose ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
            `}
            placeholder="Why are you creating this document?"
          />
          <div className="flex justify-between mt-1">
            {errors.purpose ? (
              <span className="text-sm text-red-600">{errors.purpose}</span>
            ) : (
              <span className="text-xs text-gray-500">What goal does this document serve?</span>
            )}
            <span className="text-xs text-gray-400">{purpose.length}/300</span>
          </div>
        </div>

        {/* Audience */}
        <div>
          <label htmlFor="audience" className="block text-sm font-medium text-gray-700 mb-1">
            Target Audience <span className="text-red-500">*</span>
          </label>
          <select
            id="audience"
            value={audience}
            onChange={(e) => handleChange('audience', e.target.value)}
            onBlur={(e) => validate('audience', e.target.value)}
            className={`
              w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2
              ${errors.audience ? 'border-red-300 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}
            `}
          >
            {audienceOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {errors.audience ? (
            <span className="text-sm text-red-600 mt-1 block">{errors.audience}</span>
          ) : (
            <span className="text-xs text-gray-500 mt-1 block">Who will read this document?</span>
          )}
        </div>

        {/* Language */}
        <div>
          <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => handleChange('language', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {languageOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <span className="text-xs text-gray-500 mt-1 block">Document language</span>
        </div>
      </div>
    </div>
  );
}
