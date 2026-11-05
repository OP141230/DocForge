import { BookOpen } from 'lucide-react';
import type { UserGuideData } from './FieldRegistry';

interface UserGuideFieldsProps {
  data: UserGuideData;
  onChange: (data: UserGuideData) => void;
}

export function UserGuideFields({ data, onChange }: UserGuideFieldsProps) {
  const updateField = (field: keyof UserGuideData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-teal-100 rounded-lg">
          <BookOpen className="w-6 h-6 text-teal-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">User Guide Details</h2>
          <p className="text-sm text-gray-600">Create comprehensive user documentation</p>
        </div>
      </div>

      {/* Product Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Product Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.product_name}
          onChange={(e) => updateField('product_name', e.target.value)}
          placeholder="e.g., DocForge, Acme CRM, XYZ Software"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        />
      </div>

      {/* Product Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Product Type <span className="text-red-500">*</span>
        </label>
        <select
          value={data.product_type}
          onChange={(e) => updateField('product_type', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        >
          <option value="software">Software</option>
          <option value="hardware">Hardware</option>
          <option value="service">Service</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* User Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target User Level <span className="text-red-500">*</span>
        </label>
        <select
          value={data.user_level}
          onChange={(e) => updateField('user_level', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        >
          <option value="beginner">Beginner (No prior experience)</option>
          <option value="intermediate">Intermediate (Some experience)</option>
          <option value="advanced">Advanced (Expert users)</option>
          <option value="all">All Levels</option>
        </select>
      </div>

      {/* Guide Purpose */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Guide Purpose <span className="text-red-500">*</span>
        </label>
        <select
          value={data.guide_purpose}
          onChange={(e) => updateField('guide_purpose', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        >
          <option value="quick_start">Quick Start Guide</option>
          <option value="complete_manual">Complete User Manual</option>
          <option value="troubleshooting">Troubleshooting Guide</option>
          <option value="reference">Reference Documentation</option>
        </select>
      </div>

      {/* Content Options */}
      <div className="border border-gray-200 rounded-lg p-4 space-y-3">
        <h3 className="font-semibold text-gray-900">Content Options</h3>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={data.include_screenshots}
            onChange={(e) => updateField('include_screenshots', e.target.checked)}
            className="w-5 h-5 text-teal-600 border-gray-300 rounded focus:ring-teal-500"
          />
          <div>
            <div className="font-medium text-gray-900">Include Screenshots</div>
            <div className="text-sm text-gray-600">Add visual guides and examples</div>
          </div>
        </label>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={data.include_troubleshooting}
            onChange={(e) => updateField('include_troubleshooting', e.target.checked)}
            className="w-5 h-5 text-teal-600 border-gray-300 rounded focus:ring-teal-500"
          />
          <div>
            <div className="font-medium text-gray-900">Include Troubleshooting Section</div>
            <div className="text-sm text-gray-600">Common problems and solutions</div>
          </div>
        </label>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={data.include_faq}
            onChange={(e) => updateField('include_faq', e.target.checked)}
            className="w-5 h-5 text-teal-600 border-gray-300 rounded focus:ring-teal-500"
          />
          <div>
            <div className="font-medium text-gray-900">Include FAQ Section</div>
            <div className="text-sm text-gray-600">Frequently asked questions</div>
          </div>
        </label>
      </div>

      {/* Platform */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Platform/Compatibility <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.platform}
          onChange={(e) => updateField('platform', e.target.value)}
          placeholder="e.g., Windows, macOS, Linux, Web Browser, iOS, Android"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        />
      </div>

      {/* Prerequisites */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Prerequisites <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.prerequisites}
          onChange={(e) => updateField('prerequisites', e.target.value)}
          placeholder="What do users need before getting started? (e.g., system requirements, accounts, basic knowledge)"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Support Contact */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Support Contact <span className="text-gray-500 text-xs">(Optional)</span>
        </label>
        <input
          type="text"
          value={data.support_contact || ''}
          onChange={(e) => updateField('support_contact', e.target.value)}
          placeholder="e.g., support@example.com, https://support.example.com"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
        />
      </div>
    </div>
  );
}
