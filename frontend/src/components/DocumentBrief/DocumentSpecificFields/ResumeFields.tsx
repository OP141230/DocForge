import { useState } from 'react';
import { User, Plus, Trash2, Briefcase, GraduationCap, Code, Award } from 'lucide-react';
import type { ResumeData } from './FieldRegistry';

interface ResumeFieldsProps {
  data: ResumeData;
  onChange: (data: ResumeData) => void;
}

const TECH_SKILLS = [
  'JavaScript', 'TypeScript', 'Python', 'Java', 'React', 'Node.js', 'AWS', 
  'Docker', 'SQL', 'MongoDB', 'Git', 'CI/CD', 'REST APIs', 'GraphQL'
];

const SOFT_SKILLS = [
  'Leadership', 'Communication', 'Problem Solving', 'Team Collaboration',
  'Time Management', 'Critical Thinking', 'Adaptability', 'Creativity'
];

export function ResumeFields({ data, onChange }: ResumeFieldsProps) {
  const [techSkillInput, setTechSkillInput] = useState('');
  const [softSkillInput, setSoftSkillInput] = useState('');
  const [newCert, setNewCert] = useState('');
  const [newAchievement, setNewAchievement] = useState('');

  const updateField = (field: keyof ResumeData, value: any) => {
    onChange({ ...data, [field]: value });
  };

  const updatePersonalInfo = (field: string, value: string) => {
    updateField('personal_info', { ...data.personal_info, [field]: value });
  };

  // Education management
  const addEducation = () => {
    updateField('education', [
      ...data.education,
      { degree: '', institution: '', year: '', gpa: '', achievements: '' },
    ]);
  };

  const updateEducation = (index: number, field: string, value: string) => {
    const updated = [...data.education];
    updated[index] = { ...updated[index], [field]: value };
    updateField('education', updated);
  };

  const removeEducation = (index: number) => {
    updateField('education', data.education.filter((_, i) => i !== index));
  };

  // Work experience management
  const addWorkExperience = () => {
    updateField('work_experience', [
      ...data.work_experience,
      { title: '', company: '', duration: '', responsibilities: [], achievements: [] },
    ]);
  };

  const updateWorkExperience = (index: number, field: string, value: any) => {
    const updated = [...data.work_experience];
    updated[index] = { ...updated[index], [field]: value };
    updateField('work_experience', updated);
  };

  const removeWorkExperience = (index: number) => {
    updateField('work_experience', data.work_experience.filter((_, i) => i !== index));
  };

  // Projects management
  const addProject = () => {
    updateField('projects', [
      ...data.projects,
      { name: '', description: '', technologies: [], link: '' },
    ]);
  };

  const updateProject = (index: number, field: string, value: any) => {
    const updated = [...data.projects];
    updated[index] = { ...updated[index], [field]: value };
    updateField('projects', updated);
  };

  const removeProject = (index: number) => {
    updateField('projects', data.projects.filter((_, i) => i !== index));
  };

  // Skills management
  const addTechSkill = (skill: string) => {
    if (skill && !data.technical_skills.includes(skill)) {
      updateField('technical_skills', [...data.technical_skills, skill]);
    }
    setTechSkillInput('');
  };

  const removeTechSkill = (skill: string) => {
    updateField('technical_skills', data.technical_skills.filter(s => s !== skill));
  };

  const addSoftSkill = (skill: string) => {
    if (skill && !data.soft_skills.includes(skill)) {
      updateField('soft_skills', [...data.soft_skills, skill]);
    }
    setSoftSkillInput('');
  };

  const removeSoftSkill = (skill: string) => {
    updateField('soft_skills', data.soft_skills.filter(s => s !== skill));
  };

  // Certifications and achievements
  const addCertification = () => {
    if (newCert.trim()) {
      updateField('certifications', [...data.certifications, newCert.trim()]);
      setNewCert('');
    }
  };

  const removeCertification = (index: number) => {
    updateField('certifications', data.certifications.filter((_, i) => i !== index));
  };

  const addAchievement = () => {
    if (newAchievement.trim()) {
      updateField('achievements', [...data.achievements, newAchievement.trim()]);
      setNewAchievement('');
    }
  };

  const removeAchievement = (index: number) => {
    updateField('achievements', data.achievements.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-cyan-100 rounded-lg">
          <User className="w-6 h-6 text-cyan-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Resume/CV Details</h2>
          <p className="text-sm text-gray-600">Build your professional profile</p>
        </div>
      </div>

      {/* Personal Information */}
      <div className="border border-gray-200 rounded-lg p-4 space-y-4">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <User className="w-5 h-5" />
          Personal Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            value={data.personal_info.name}
            onChange={(e) => updatePersonalInfo('name', e.target.value)}
            placeholder="Full Name *"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
          <input
            type="email"
            value={data.personal_info.email}
            onChange={(e) => updatePersonalInfo('email', e.target.value)}
            placeholder="Email Address *"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
          <input
            type="tel"
            value={data.personal_info.phone}
            onChange={(e) => updatePersonalInfo('phone', e.target.value)}
            placeholder="Phone Number *"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
          <input
            type="text"
            value={data.personal_info.location}
            onChange={(e) => updatePersonalInfo('location', e.target.value)}
            placeholder="Location *"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
          <input
            type="url"
            value={data.personal_info.linkedin || ''}
            onChange={(e) => updatePersonalInfo('linkedin', e.target.value)}
            placeholder="LinkedIn URL (Optional)"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
          <input
            type="url"
            value={data.personal_info.portfolio || ''}
            onChange={(e) => updatePersonalInfo('portfolio', e.target.value)}
            placeholder="Portfolio URL (Optional)"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
          <input
            type="url"
            value={data.personal_info.github || ''}
            onChange={(e) => updatePersonalInfo('github', e.target.value)}
            placeholder="GitHub URL (Optional)"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Target Role */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Role <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.target_role}
          onChange={(e) => updateField('target_role', e.target.value)}
          placeholder="e.g., Senior Software Engineer, Product Manager"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
        />
      </div>

      {/* Professional Summary */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Professional Summary <span className="text-red-500">*</span>
        </label>
        <textarea
          value={data.professional_summary}
          onChange={(e) => updateField('professional_summary', e.target.value)}
          placeholder="A brief overview of your professional background and key strengths"
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Education */}
      <div className="border border-gray-200 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <GraduationCap className="w-5 h-5" />
            Education
          </h3>
          <button
            type="button"
            onClick={addEducation}
            className="px-3 py-1 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Education
          </button>
        </div>
        {data.education.map((edu, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-3 space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-medium text-sm text-gray-700">Education {index + 1}</span>
              <button
                type="button"
                onClick={() => removeEducation(index)}
                className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                type="text"
                value={edu.degree}
                onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                placeholder="Degree *"
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
              />
              <input
                type="text"
                value={edu.institution}
                onChange={(e) => updateEducation(index, 'institution', e.target.value)}
                placeholder="Institution *"
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
              />
              <input
                type="text"
                value={edu.year}
                onChange={(e) => updateEducation(index, 'year', e.target.value)}
                placeholder="Year *"
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
              />
              <input
                type="text"
                value={edu.gpa || ''}
                onChange={(e) => updateEducation(index, 'gpa', e.target.value)}
                placeholder="GPA (Optional)"
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
              />
            </div>
            <input
              type="text"
              value={edu.achievements || ''}
              onChange={(e) => updateEducation(index, 'achievements', e.target.value)}
              placeholder="Achievements (Optional)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
            />
          </div>
        ))}
      </div>

      {/* Work Experience */}
      <div className="border border-gray-200 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Briefcase className="w-5 h-5" />
            Work Experience
          </h3>
          <button
            type="button"
            onClick={addWorkExperience}
            className="px-3 py-1 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Experience
          </button>
        </div>
        {data.work_experience.map((exp, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-3 space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-medium text-sm text-gray-700">Experience {index + 1}</span>
              <button
                type="button"
                onClick={() => removeWorkExperience(index)}
                className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                type="text"
                value={exp.title}
                onChange={(e) => updateWorkExperience(index, 'title', e.target.value)}
                placeholder="Job Title *"
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
              />
              <input
                type="text"
                value={exp.company}
                onChange={(e) => updateWorkExperience(index, 'company', e.target.value)}
                placeholder="Company *"
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
              />
            </div>
            <input
              type="text"
              value={exp.duration}
              onChange={(e) => updateWorkExperience(index, 'duration', e.target.value)}
              placeholder="Duration (e.g., Jan 2020 - Present) *"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
            />
            <textarea
              value={exp.responsibilities.join('\n')}
              onChange={(e) => updateWorkExperience(index, 'responsibilities', e.target.value.split('\n').filter(Boolean))}
              placeholder="Responsibilities (one per line)"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm resize-none"
            />
            <textarea
              value={exp.achievements.join('\n')}
              onChange={(e) => updateWorkExperience(index, 'achievements', e.target.value.split('\n').filter(Boolean))}
              placeholder="Achievements (one per line)"
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm resize-none"
            />
          </div>
        ))}
      </div>

      {/* Technical Skills */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Code className="w-4 h-4 inline mr-1" />
          Technical Skills
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={techSkillInput}
              onChange={(e) => setTechSkillInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addTechSkill(techSkillInput);
                }
              }}
              placeholder="Add a technical skill"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => addTechSkill(techSkillInput)}
              className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {TECH_SKILLS.map((skill) => (
              <button
                key={skill}
                type="button"
                onClick={() => addTechSkill(skill)}
                disabled={data.technical_skills.includes(skill)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {skill}
              </button>
            ))}
          </div>
          {data.technical_skills.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {data.technical_skills.map((skill) => (
                <span key={skill} className="inline-flex items-center gap-1 px-3 py-1 bg-cyan-100 text-cyan-700 rounded-full text-sm">
                  {skill}
                  <button type="button" onClick={() => removeTechSkill(skill)} className="hover:text-cyan-900">×</button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Soft Skills */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Soft Skills
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={softSkillInput}
              onChange={(e) => setSoftSkillInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addSoftSkill(softSkillInput);
                }
              }}
              placeholder="Add a soft skill"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={() => addSoftSkill(softSkillInput)}
              className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {SOFT_SKILLS.map((skill) => (
              <button
                key={skill}
                type="button"
                onClick={() => addSoftSkill(skill)}
                disabled={data.soft_skills.includes(skill)}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {skill}
              </button>
            ))}
          </div>
          {data.soft_skills.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {data.soft_skills.map((skill) => (
                <span key={skill} className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                  {skill}
                  <button type="button" onClick={() => removeSoftSkill(skill)} className="hover:text-purple-900">×</button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Projects */}
      <div className="border border-gray-200 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">Projects</h3>
          <button
            type="button"
            onClick={addProject}
            className="px-3 py-1 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-2 text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Project
          </button>
        </div>
        {data.projects.map((project, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-3 space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-medium text-sm text-gray-700">Project {index + 1}</span>
              <button
                type="button"
                onClick={() => removeProject(index)}
                className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <input
              type="text"
              value={project.name}
              onChange={(e) => updateProject(index, 'name', e.target.value)}
              placeholder="Project Name *"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
            />
            <textarea
              value={project.description}
              onChange={(e) => updateProject(index, 'description', e.target.value)}
              placeholder="Project Description *"
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm resize-none"
            />
            <input
              type="text"
              value={project.technologies.join(', ')}
              onChange={(e) => updateProject(index, 'technologies', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
              placeholder="Technologies (comma-separated) *"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
            />
            <input
              type="url"
              value={project.link || ''}
              onChange={(e) => updateProject(index, 'link', e.target.value)}
              placeholder="Project Link (Optional)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 text-sm"
            />
          </div>
        ))}
      </div>

      {/* Certifications */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <Award className="w-4 h-4 inline mr-1" />
          Certifications
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newCert}
              onChange={(e) => setNewCert(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addCertification();
                }
              }}
              placeholder="Add a certification"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addCertification}
              className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>
          {data.certifications.length > 0 && (
            <div className="space-y-2 mt-3">
              {data.certifications.map((cert, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 border border-gray-200 rounded-lg">
                  <span className="flex-1 text-gray-700">{cert}</span>
                  <button
                    type="button"
                    onClick={() => removeCertification(index)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Achievements */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Achievements
        </label>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={newAchievement}
              onChange={(e) => setNewAchievement(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addAchievement();
                }
              }}
              placeholder="Add an achievement"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
            <button
              type="button"
              onClick={addAchievement}
              className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>
          {data.achievements.length > 0 && (
            <div className="space-y-2 mt-3">
              {data.achievements.map((achievement, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 border border-gray-200 rounded-lg">
                  <span className="flex-1 text-gray-700">{achievement}</span>
                  <button
                    type="button"
                    onClick={() => removeAchievement(index)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
