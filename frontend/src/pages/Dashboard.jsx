// frontend/src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { fetchEmployerDashboard } from '../api';
import './Dashboard.css';

export default function Dashboard({ navigate }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await fetchEmployerDashboard();
        setStats(data);
      } catch {
        setError('Failed to load dashboard data.');
      }
      setLoading(false);
    }
    loadDashboard();
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div className="dashboard-page">
      <h2>Employer Dashboard</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{stats.total_jobs}</div>
          <div className="stat-label">Active Job Postings</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.total_applicants}</div>
          <div className="stat-label">Total Applicants</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.total_shortlisted}</div>
          <div className="stat-label">Shortlisted</div>
        </div>
      </div>

      <div className="dashboard-actions">
        <button
          className="btn-primary"
          onClick={() => navigate('/create-job')}
        >
          + Post New Job
        </button>
        <button
          className="btn-outline"
          onClick={() => navigate('/my-jobs')}
        >
          View My Jobs
        </button>
      </div>

      {stats.recent_applications.length > 0 && (
        <div className="recent-activity">
          <h3>Recent Applications</h3>
          <ul className="activity-list">
            {stats.recent_applications.map((a) => (
              <li key={`${a.applicant_name}-${a.job_position}-${a.applied_at}`} className="activity-item">
                <div className="activity-info">
                  <strong>{a.applicant_name}</strong>
                  {' applied for '}
                  <em>{a.job_position}</em>
                  <span className="muted">
                    {' — '}{new Date(a.applied_at).toLocaleDateString()}
                  </span>
                </div>
                <span className={`status-chip status-${a.status}`}>
                  {a.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {stats.recent_applications.length === 0 && stats.total_jobs > 0 && (
        <div className="empty-state">
          <p>No applications yet. Share your job postings to attract candidates.</p>
        </div>
      )}

      {stats.total_jobs === 0 && (
        <div className="empty-state">
          <p>You have no job postings. Create one to get started.</p>
          <button className="btn-primary" onClick={() => navigate('/create-job')}>
            Post Your First Job
          </button>
        </div>
      )}
    </div>
  );
}
