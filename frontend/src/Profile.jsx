// src/Profile.jsx
import React, { useState } from 'react';
import { updateProfile, parseResumeText, uploadResumePdf } from './api';
import './Profile.css';

export default function Profile({ user, onUpdateProfile, onBack }) {
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    location: user?.location || '',
    bio: user?.bio || '',
    profilePicture: user?.profilePicture || '',
    education: user?.education || '',
    experience: user?.experience || '',
  });

  // Skills stored as array internally, joined to comma-string on save
  const [skills, setSkills] = useState(() => {
    if (!user?.skills) return [];
    return user.skills.split(',').map((s) => s.trim()).filter(Boolean);
  });
  const [skillInput, setSkillInput] = useState('');

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const [resumeText, setResumeText] = useState('');
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeFile, setResumeFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleAddSkill = () => {
    const trimmed = skillInput.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills((prev) => [...prev, trimmed]);
    }
    setSkillInput('');
  };

  const handleSkillInputKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddSkill();
    }
  };

  const handleRemoveSkill = (skill) => {
    setSkills((prev) => prev.filter((s) => s !== skill));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const payload = { ...formData, skills: skills.join(', ') };
      const updatedUser = await updateProfile(payload);
      localStorage.setItem('user', JSON.stringify(updatedUser.user));
      onUpdateProfile(updatedUser.user);
      setSuccess('Profile updated successfully!');
    } catch (err) {
      setError(err.message || 'Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleParseResume = async () => {
    if (!resumeText.trim()) return;
    setResumeLoading(true);
    setError('');
    setSuccess('');
    try {
      const data = await parseResumeText(resumeText);

      // Refresh form fields from populated profile
      const updatedUser = data.user;
      setFormData({
        name: updatedUser.name || '',
        email: updatedUser.email || '',
        phone: updatedUser.phone || '',
        location: updatedUser.location || '',
        bio: updatedUser.bio || '',
        profilePicture: updatedUser.profilePicture || '',
        education: updatedUser.education || '',
        experience: updatedUser.experience || '',
      });
      if (updatedUser.skills) {
        setSkills(updatedUser.skills.split(',').map(s => s.trim()).filter(Boolean));
      }
      localStorage.setItem('user', JSON.stringify(updatedUser));
      onUpdateProfile(updatedUser);

      const populated = data.fields_populated || 0;
      setSuccess(`Resume parsed! ${data.extracted_skills.length} skills found.${populated > 0 ? ` ${populated} profile field(s) auto-populated.` : ''}`);
      setResumeText('');
    } catch (err) {
      setError(err.message || 'Failed to parse resume. Please try again.');
    } finally {
      setResumeLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('File must be smaller than 5MB');
      return;
    }
    setResumeFile(file);
    setResumeLoading(true);
    setError('');
    setSuccess('');
    try {
      const data = await uploadResumePdf(file);
      const updatedUser = data.user;
      setFormData({
        name: updatedUser.name || '',
        email: updatedUser.email || '',
        phone: updatedUser.phone || '',
        location: updatedUser.location || '',
        bio: updatedUser.bio || '',
        profilePicture: updatedUser.profilePicture || '',
        education: updatedUser.education || '',
        experience: updatedUser.experience || '',
      });
      if (updatedUser.skills) {
        setSkills(updatedUser.skills.split(',').map(s => s.trim()).filter(Boolean));
      }
      localStorage.setItem('user', JSON.stringify(updatedUser));
      onUpdateProfile(updatedUser);
      const populated = data.fields_populated || 0;
      setSuccess(`PDF parsed! ${data.extracted_skills.length} skills found.${populated > 0 ? ` ${populated} profile field(s) auto-populated.` : ''}`);
    } catch (err) {
      setError(err.message || 'Failed to parse PDF. Please try again.');
    } finally {
      setResumeLoading(false);
      setResumeFile(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  const initials = user?.name
    ? user.name.split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase()
    : '?';

  return (
    <div className="profile-page">
      <div className="profile-header-card">
        <div className="profile-avatar-large">{initials}</div>
        <div className="profile-header-info">
          <h2>{user?.name || 'Your Profile'}</h2>
          <span className="profile-role-badge">{user?.role || 'user'}</span>
        </div>
      </div>

      <div className="profile-form-card">
        <h3>Edit Profile</h3>

        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input
                id="name"
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Enter your full name"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                disabled
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone">Phone</label>
              <input
                id="phone"
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleInputChange}
                placeholder="Enter your phone number"
              />
            </div>

            <div className="form-group">
              <label htmlFor="location">Location</label>
              <input
                id="location"
                type="text"
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                placeholder="Enter your location"
              />
            </div>

            <div className="form-group full-width">
              <label htmlFor="bio">Bio</label>
              <textarea
                id="bio"
                name="bio"
                value={formData.bio}
                onChange={handleInputChange}
                placeholder="Tell us about yourself"
                rows="4"
              />
            </div>

            {user?.role === 'employee' && (
              <>
                <div className="form-group full-width">
                  <div className="skills-section">
                    <h4>Background</h4>
                  </div>
                </div>
                <div className="form-group full-width">
                  <label htmlFor="education">Education</label>
                  <textarea
                    id="education"
                    name="education"
                    value={formData.education}
                    onChange={handleInputChange}
                    placeholder={"e.g.\nB.Eng Computer Engineering, KMITL (2024)\nHigh School Diploma, Bangkok (2020)"}
                    rows="3"
                  />
                </div>
                <div className="form-group full-width">
                  <label htmlFor="experience">Experience</label>
                  <textarea
                    id="experience"
                    name="experience"
                    value={formData.experience}
                    onChange={handleInputChange}
                    placeholder={"e.g.\n1 year internship at TechCorp as Backend Developer (2023–2024)\nFreelance web development (2022–2023)"}
                    rows="3"
                  />
                </div>
              </>
            )}

            {user?.role === 'employee' && (
              <div className="form-group full-width">
                <div className="skills-section">
                  <h4>Import from Resume</h4>

                  <div
                    className={`resume-dropzone${dragActive ? ' drag-active' : ''}`}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onClick={() => document.getElementById('resume-file-input').click()}
                  >
                    <input
                      id="resume-file-input"
                      type="file"
                      accept=".pdf"
                      style={{ display: 'none' }}
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) handleFileUpload(file);
                        e.target.value = '';
                      }}
                    />
                    <div className="resume-dropzone-icon">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="12" y1="18" x2="12" y2="12" />
                        <line x1="9" y1="15" x2="12" y2="12" />
                        <line x1="15" y1="15" x2="12" y2="12" />
                      </svg>
                    </div>
                    <p className="resume-dropzone-text">
                      {resumeLoading && resumeFile
                        ? 'Parsing PDF...'
                        : 'Drag & drop a PDF here or click to browse'}
                    </p>
                    <span className="resume-dropzone-hint">PDF files only, max 5MB</span>
                  </div>

                  <div className="resume-divider">
                    <span>or paste text</span>
                  </div>

                  <textarea
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    placeholder="Paste your resume text here..."
                    rows="4"
                  />
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={handleParseResume}
                    disabled={resumeLoading || !resumeText.trim()}
                  >
                    {resumeLoading && !resumeFile ? 'Parsing...' : 'Parse Text'}
                  </button>
                </div>
              </div>
            )}

            <div className="form-group full-width">
              <div className="skills-section">
                <h4>Skills</h4>
                <div className="skills-input-row">
                  <input
                    type="text"
                    value={skillInput}
                    onChange={(e) => setSkillInput(e.target.value)}
                    onKeyDown={handleSkillInputKeyDown}
                    placeholder="e.g. JavaScript, React, Python"
                  />
                  <button type="button" className="btn-primary" onClick={handleAddSkill}>
                    Add
                  </button>
                </div>
                {skills.length > 0 && (
                  <div className="skill-list">
                    {skills.map((skill) => (
                      <span key={skill} className="skill-item">
                        {skill}
                        <button
                          type="button"
                          className="skill-remove"
                          onClick={() => handleRemoveSkill(skill)}
                          aria-label={`Remove ${skill}`}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {success && <div className="form-success">{success}</div>}
          {error && <div className="form-error-msg">{error}</div>}

          <div className="form-actions">
            <button type="button" className="btn-outline" onClick={onBack}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
