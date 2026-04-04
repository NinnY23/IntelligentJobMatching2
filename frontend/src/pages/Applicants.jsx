// frontend/src/pages/Applicants.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchJobApplicants, updateApplicationStatus } from '../api';
import './Applicants.css';

const scoreClass = score => {
  if (score >= 80) return 'score-badge--high';
  if (score >= 50) return 'score-badge--mid';
  return 'score-badge--low';
};

function MatchBar({ score }) {
  const pct = Math.round(score);
  let color = 'var(--color-primary)';
  if (pct >= 80) color = 'var(--color-success)';
  else if (pct >= 50) color = '#f59e0b';
  else color = 'var(--color-muted)';
  return (
    <div className="applicants-match-bar-container">
      <div className="applicants-match-bar">
        <div className="applicants-match-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="applicants-match-bar-label">{pct}%</span>
    </div>
  );
}


export default function Applicants({ jobId }) {
  const [applicants, setApplicants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const [profileTarget, setProfileTarget] = useState(null);

  useEffect(() => {
    if (jobId) loadApplicants();
  }, [jobId]);

  useEffect(() => {
    if (!profileTarget) return;
    const handler = (e) => { if (e.key === 'Escape') setProfileTarget(null); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [profileTarget]);

  async function loadApplicants() {
    setLoading(true);
    try {
      const data = await fetchJobApplicants(jobId);
      setApplicants(data);
    } catch {
      setMessage('Failed to load applicants.');
    }
    setLoading(false);
  }

  async function handleStatusChange(appId, newStatus) {
    try {
      const { ok, data } = await updateApplicationStatus(appId, newStatus);
      if (ok) {
        setMessage(`Candidate marked as ${newStatus}.`);
        loadApplicants();
      } else {
        setMessage(data.message || 'Failed to update status.');
      }
    } catch {
      setMessage('Network error. Could not update status.');
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

      <div className="filter-bar">
        {['all', 'pending', 'shortlisted'].map(f => (
          <button
            key={f}
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
                  <span className={`score-badge ${scoreClass(a.match_score)}`}>
                    {a.match_score}%
                  </span>
                </td>
                <td>
                  <div className="skill-tags">
                    {(a.matched_skills || []).length === 0
                      ? <span className="muted">—</span>
                      : (a.matched_skills || []).map(s => (
                          <span key={s} className="skill-tag matched">{s}</span>
                        ))}
                  </div>
                </td>
                <td>
                  <div className="skill-tags">
                    {(a.missing_skills || []).length === 0
                      ? <span className="muted">—</span>
                      : (a.missing_skills || []).map(s => (
                          <span key={s} className="skill-tag missing">{s}</span>
                        ))}
                  </div>
                </td>
                <td>{new Date(a.applied_at).toLocaleDateString()}</td>
                <td>
                  <span className={`status-chip status-${a.status}`}>{a.status}</span>
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
                  {' '}
                  <button
                    className="btn-sm"
                    onClick={() => navigate(`/messages?partner=${a.user_id}`)}
                  >
                    Message
                  </button>
                  {' '}
                  <button
                    className="btn-sm"
                    onClick={() => setProfileTarget(a)}
                  >
                    View Profile
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {profileTarget && (
        <div className="modal-overlay" onClick={() => setProfileTarget(null)}>
          <div
            className="modal applicant-profile-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="applicant-profile-title"
            onClick={e => e.stopPropagation()}
          >
            <button
              className="modal-close"
              onClick={() => setProfileTarget(null)}
              aria-label="Close"
            >
              ✕
            </button>

            {/* Header: avatar + name + email + status */}
            <div className="applicant-profile-header">
              <div className="profile-avatar-large">
                {(profileTarget.name || '?').split(' ').filter(Boolean).map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?'}
              </div>
              <div className="applicant-profile-header-info">
                <h3 id="applicant-profile-title" className="applicant-profile-name">
                  {profileTarget.name}
                </h3>
                <p className="applicant-profile-email">{profileTarget.email}</p>
                <div className="applicant-profile-meta">
                  <span className="profile-role-badge">job seeker</span>
                  <span className={`status-chip status-${profileTarget.status}`}>{profileTarget.status}</span>
                  <span className="muted">
                    Applied {new Date(profileTarget.applied_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Match score */}
            <div className="applicant-profile-section">
              <h4>Match Score</h4>
              <span className={`score-badge ${scoreClass(profileTarget.match_score)}`}>
                {profileTarget.match_score}% match
              </span>
              {profileTarget.match_score != null && <MatchBar score={profileTarget.match_score} />}
            </div>

            {/* Matched skills */}
            {(profileTarget.matched_skills || []).length > 0 && (
              <div className="applicant-profile-section">
                <h4>Matched Skills</h4>
                <div className="skill-tags">
                  {profileTarget.matched_skills.map(s => (
                    <span key={s} className="skill-tag matched">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Missing skills */}
            {(profileTarget.missing_skills || []).length > 0 && (
              <div className="applicant-profile-section">
                <h4>Missing Skills</h4>
                <div className="skill-tags">
                  {profileTarget.missing_skills.map(s => (
                    <span key={s} className="skill-tag missing">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {/* About */}
            {profileTarget.bio && (
              <div className="applicant-profile-section">
                <h4>About</h4>
                <p>{profileTarget.bio}</p>
              </div>
            )}

            {/* Education */}
            {profileTarget.education && (
              <div className="applicant-profile-section">
                <h4>Education</h4>
                <p>{profileTarget.education}</p>
              </div>
            )}

            {/* Experience */}
            {profileTarget.experience && (
              <div className="applicant-profile-section">
                <h4>Experience</h4>
                <p>{profileTarget.experience}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
