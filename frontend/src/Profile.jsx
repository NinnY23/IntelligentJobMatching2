// src/Profile.jsx
import React, { useState, useEffect } from 'react';
import './Profile.css';

export default function Profile({ user, onUpdateProfile, onBack }) {
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    location: user?.location || '',
    bio: user?.bio || '',
    skills: user?.skills || '',
    profilePicture: user?.profilePicture || '',
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Failed to update profile');
      }

      const updatedUser = await response.json();
      localStorage.setItem('user', JSON.stringify(updatedUser.user));
      onUpdateProfile(updatedUser.user);
      setSuccess('Profile updated successfully!');
      setIsEditing(false);
    } catch (err) {
      setError(err.message || 'Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-container">
      <div className="profile-header">
        <button className="back-btn" onClick={onBack}>← Back</button>
        <h1>My Profile</h1>
        {!isEditing && (
          <button className="edit-btn" onClick={() => setIsEditing(true)}>
            Edit Profile
          </button>
        )}
      </div>

      <div className="profile-content">
        {isEditing ? (
          <form onSubmit={handleSubmit} className="profile-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name">Full Name:</label>
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
                <label htmlFor="email">Email:</label>
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
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="phone">Phone:</label>
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
                <label htmlFor="location">Location:</label>
                <input
                  id="location"
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  placeholder="Enter your location"
                />
              </div>
            </div>

            <div className="form-group full-width">
              <label htmlFor="bio">Bio:</label>
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
              <label htmlFor="skills">Skills (comma-separated):</label>
              <input
                id="skills"
                type="text"
                name="skills"
                value={formData.skills}
                onChange={handleInputChange}
                placeholder="e.g., JavaScript, React, Python"
              />
            </div>

            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}

            <div className="form-actions">
              <button type="submit" disabled={loading} className="save-btn">
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="cancel-btn"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="profile-view">
            <div className="profile-item">
              <span className="label">Name:</span>
              <span className="value">{formData.name || 'Not set'}</span>
            </div>

            <div className="profile-item">
              <span className="label">Email:</span>
              <span className="value">{formData.email}</span>
            </div>

            <div className="profile-item">
              <span className="label">Phone:</span>
              <span className="value">{formData.phone || 'Not set'}</span>
            </div>

            <div className="profile-item">
              <span className="label">Location:</span>
              <span className="value">{formData.location || 'Not set'}</span>
            </div>

            <div className="profile-item">
              <span className="label">Bio:</span>
              <span className="value">{formData.bio || 'Not set'}</span>
            </div>

            <div className="profile-item">
              <span className="label">Skills:</span>
              <span className="value">{formData.skills || 'Not set'}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
