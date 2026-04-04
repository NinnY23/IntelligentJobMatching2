// frontend/src/pages/Applicants.jsx
import React, { useState, useEffect } from 'react';

const SCORE_COLOR = score => {
  if (score >= 80) return '#16a34a';
  if (score >= 50) return '#4F46E5';
  return '#9ca3af';
};

const STATUS_COLORS = {
  pending: '#4F46E5',
  shortlisted: '#16a34a',
  withdrawn: '#9ca3af',
};

export default function Applicants({ jobId }) {
  const [applicants, setApplicants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (jobId) loadApplicants();
  }, [jobId]);

  async function loadApplicants() {
    setLoading(true);
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`/api/job-posts/${jobId}/applicants`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        setApplicants(await res.json());
      } else {
        setMessage('Failed to load applicants.');
      }
    } catch {
      setMessage('Network error loading applicants.');
    }
    setLoading(false);
  }

  async function handleStatusChange(appId, newStatus) {
    const token = localStorage.getItem('token');
    const res = await fetch(`/api/applications/${appId}/status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ status: newStatus }),
    });
    if (res.ok) {
      setMessage(`Candidate marked as ${newStatus}.`);
      loadApplicants();
    } else {
      const data = await res.json();
      setMessage(data.message || 'Failed to update status.');
    }
  }

  const filtered =
    filter === 'all'
      ? applicants
      : applicants.filter(a => a.status === filter);

  if (loading) return <div className="loading">Loading applicants...</div>;

  return (
    <div className="applicants-page">
      <h2>Applicants</h2>

      {message && (
        <div className="info-banner" onClick={() => setMessage('')}>
          {message}
        </div>
      )}

      <div className="filter-bar" role="tablist">
        {['all', 'pending', 'shortlisted'].map(f => (
          <button
            key={f}
            role="tab"
            aria-selected={filter === f}
            className={`filter-btn${filter === f ? ' active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <p>No applicants {filter !== 'all' ? `with status "${filter}"` : ''}.</p>
        </div>
      ) : (
        <table className="applicants-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Match</th>
              <th>Matched Skills</th>
              <th>Missing Skills</th>
              <th>Applied</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(a => (
              <tr key={a.application_id}>
                <td>
                  <strong>{a.name}</strong>
                  <br />
                  <span className="muted">{a.email}</span>
                </td>
                <td>
                  <span
                    className="score-badge"
                    style={{ background: SCORE_COLOR(a.match_score) }}
                  >
                    {a.match_score}%
                  </span>
                </td>
                <td>
                  <div className="skill-tags">
                    {a.matched_skills.length === 0
                      ? <span className="muted">—</span>
                      : a.matched_skills.map(s => (
                          <span key={s} className="skill-tag matched">{s}</span>
                        ))}
                  </div>
                </td>
                <td>
                  <div className="skill-tags">
                    {a.missing_skills.length === 0
                      ? <span className="muted">—</span>
                      : a.missing_skills.map(s => (
                          <span key={s} className="skill-tag missing">{s}</span>
                        ))}
                  </div>
                </td>
                <td>{new Date(a.applied_at).toLocaleDateString()}</td>
                <td>
                  <span
                    className="status-chip"
                    style={{
                      background: STATUS_COLORS[a.status] || '#6b7280',
                      color: '#fff',
                      padding: '2px 10px',
                      borderRadius: '12px',
                      fontSize: '0.85em',
                    }}
                  >
                    {a.status}
                  </span>
                </td>
                <td>
                  {a.status !== 'shortlisted' && (
                    <button
                      className="btn-sm"
                      onClick={() =>
                        handleStatusChange(a.application_id, 'shortlisted')
                      }
                    >
                      Shortlist
                    </button>
                  )}
                  {a.status === 'shortlisted' && (
                    <button
                      className="btn-sm"
                      onClick={() =>
                        handleStatusChange(a.application_id, 'pending')
                      }
                    >
                      Unshortlist
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
