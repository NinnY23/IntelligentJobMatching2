// frontend/src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';

export default function Dashboard({ navigate }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadDashboard() {
      const token = localStorage.getItem('token');
      try {
        const res = await fetch('/api/employer/dashboard', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (res.ok) {
          setStats(await res.json());
        } else {
          setError('Failed to load dashboard data.');
        }
      } catch {
        setError('Network error. Is the server running?');
      }
      setLoading(false);
    }
    loadDashboard();
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error-banner">{error}</div>;

  const STATUS_CHIP_COLORS = {
    pending: '#4F46E5',
    shortlisted: '#16a34a',
    withdrawn: '#9ca3af',
  };

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
            {stats.recent_applications.map((a, i) => (
              <li key={i} className="activity-item">
                <div className="activity-info">
                  <strong>{a.applicant_name}</strong>
                  {' applied for '}
                  <em>{a.job_position}</em>
                  <span className="muted">
                    {' — '}{new Date(a.applied_at).toLocaleDateString()}
                  </span>
                </div>
                <span
                  className={`status-chip status-${a.status}`}
                  style={{
                    background: STATUS_CHIP_COLORS[a.status] || '#6b7280',
                    color: '#fff',
                    padding: '2px 10px',
                    borderRadius: '12px',
                    fontSize: '0.82em',
                  }}
                >
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
