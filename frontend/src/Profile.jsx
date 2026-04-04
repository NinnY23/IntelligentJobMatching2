// src/Profile.jsx
import React, { useState } from 'react';
import './Profile.css';

export default function Profile({ user, onUpdateProfile, onBack }) {
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    location: user?.location || '',
    bio: user?.bio || '',
    profilePicture: user?.profilePicture || '',
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
      const token = localStorage.getItem('token');
      const payload = { ...formData, skills: skills.join(', ') };
      const response = await fetch('http://localhost:5000/api/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to update profile');
      }

      const updatedUser = await response.json();
      localStorage.setItem('user', JSON.stringify(updatedUser.user));
      onUpdateProfile(updatedUser.user);
      setSuccess('Profile updated successfully!');
    } catch (err) {
      setError(err.message || 'Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
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
