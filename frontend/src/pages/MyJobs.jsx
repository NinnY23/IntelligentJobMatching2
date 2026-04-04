// frontend/src/pages/MyJobs.jsx
import React, { useState, useEffect } from 'react';
import './MyJobs.css';

export default function MyJobs({ user, navigate }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editJob, setEditJob] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [message, setMessage] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadMyJobs();
  }, []);

  async function loadMyJobs() {
    setLoading(true);
    const token = localStorage.getItem('token');
    try {
      const res = await fetch('/api/employer/jobs', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setJobs(data.jobs || []);
    } catch {
      setMessage('Failed to load jobs.');
    }
    setLoading(false);
  }

  async function handleArchive(jobId) {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`/api/job-posts/${jobId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ status: 'archived' }),
      });
      if (res.ok) {
        setMessage('Job archived.');
        loadMyJobs();
      } else {
        const data = await res.json();
        setMessage(data.message || 'Failed to archive job.');
      }
    } catch {
      setMessage('Network error. Could not archive job.');
    }
  }

  async function handlePublish(jobId) {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`/api/job-posts/${jobId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ status: 'active' }),
      });
      if (res.ok) {
        setMessage('Job published.');
        loadMyJobs();
      } else {
        const data = await res.json();
        setMessage(data.message || 'Failed to publish job.');
      }
    } catch {
      setMessage('Network error. Could not publish job.');
    }
  }

  async function handleDelete(jobId) {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`/api/job-posts/${jobId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        setMessage('Job posting deleted.');
        setDeleteConfirm(null);
        loadMyJobs();
      } else {
        const data = await res.json();
        setMessage(data.message || 'Failed to delete job.');
      }
    } catch {
      setMessage('Network error. Could not delete job.');
      setDeleteConfirm(null);
    }
  }

  async function handleUpdate(jobId, formData) {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`/api/job-posts/${jobId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        setMessage('Job posting updated.');
        setEditJob(null);
        loadMyJobs();
      } else {
        const data = await res.json();
        setMessage(data.message || 'Failed to update job.');
      }
    } catch {
      setMessage('Network error. Could not update job.');
    }
  }

  const filteredJobs = filter === 'all' ? jobs : jobs.filter(j => j.status === filter);

  const statusBadgeStyle = (status) => {
    const base = { padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600 };
    if (status === 'active') return { ...base, background: '#d1fae5', color: '#065f46' };
    if (status === 'draft') return { ...base, background: '#fef3c7', color: '#92400e' };
    if (status === 'archived') return { ...base, background: '#f3f4f6', color: '#6b7280' };
    return base;
  };

  if (loading) return <div className="loading">Loading your job postings...</div>;

  return (
    <div className="my-jobs-page">
      <div className="page-header">
        <h2>My Job Postings</h2>
        <button className="btn-primary" onClick={() => navigate('/create-job')}>
          + Post New Job
        </button>
      </div>

      {message && (
        <div className="info-banner" onClick={() => setMessage('')}>
          {message}
        </div>
      )}

      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {['all', 'active', 'draft', 'archived'].map(tab => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            style={{
              padding: '6px 16px', borderRadius: '20px', border: '1px solid #d1d5db',
              background: filter === tab ? '#2563eb' : '#fff',
              color: filter === tab ? '#fff' : '#374151',
              cursor: 'pointer', fontWeight: 500, textTransform: 'capitalize'
            }}
          >
            {tab === 'all' ? 'All' : tab.charAt(0).toUpperCase() + tab.slice(1) + 's'}
          </button>
        ))}
      </div>

      {filteredJobs.length === 0 ? (
        <div className="empty-state">
          <p>{jobs.length === 0 ? 'No job postings yet.' : `No ${filter} jobs.`}</p>
          {jobs.length === 0 && (
            <button className="btn-primary" onClick={() => navigate('/create-job')}>
              Create your first posting
            </button>
          )}
        </div>
      ) : (
        <table className="jobs-table">
          <thead>
            <tr>
              <th>Position</th>
              <th>Company</th>
              <th>Location</th>
              <th>Status</th>
              <th>Applicants</th>
              <th>Deadline</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredJobs.map(job => (
              <tr key={job.id}>
                <td>{job.position}</td>
                <td>{job.company}</td>
                <td>{job.location}</td>
                <td><span style={statusBadgeStyle(job.status)}>{job.status}</span></td>
                <td>{job.applicants || 0}</td>
                <td>{job.deadline}</td>
                <td className="action-cell">
                  <button
                    className="btn-sm"
                    onClick={() => setEditJob(job)}
                  >
                    Edit
                  </button>
                  <button
                    className="btn-sm"
                    onClick={() => navigate(`/jobs/${job.id}/applicants`)}
                  >
                    Applicants
                  </button>
                  {job.status === 'active' && (
                    <button
                      className="btn-sm"
                      onClick={() => handleArchive(job.id)}
                    >
                      Archive
                    </button>
                  )}
                  {job.status === 'draft' && (
                    <button
                      className="btn-sm"
                      onClick={() => handlePublish(job.id)}
                    >
                      Publish
                    </button>
                  )}
                  {job.status === 'archived' && (
                    <button
                      className="btn-sm"
                      onClick={() => handlePublish(job.id)}
                    >
                      Reactivate
                    </button>
                  )}
                  <button
                    className="btn-danger-sm"
                    onClick={() => setDeleteConfirm(job.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {deleteConfirm && (
        <div className="modal-overlay">
          <div className="modal confirm-modal" role="dialog" aria-modal="true" aria-labelledby="delete-confirm-title">
            <h3 id="delete-confirm-title">Delete Job Posting?</h3>
            <p>
              This will permanently remove the job and all associated applications.
              This action cannot be undone.
            </p>
            <div className="modal-actions">
              <button
                className="btn-outline"
                onClick={() => setDeleteConfirm(null)}
              >
                Cancel
              </button>
              <button
                className="btn-danger"
                onClick={() => handleDelete(deleteConfirm)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {editJob && (
        <EditJobModal
          job={editJob}
          onSave={handleUpdate}
          onClose={() => setEditJob(null)}
        />
      )}
    </div>
  );
}

function EditJobModal({ job, onSave, onClose }) {
  const [form, setForm] = useState({
    position: job.position || '',
    company: job.company || '',
    location: job.location || '',
    description: job.description || '',
    required_skills: job.required_skills || '',
    preferred_skills: job.preferred_skills || '',
    salary_min: job.salary_min || '',
    salary_max: job.salary_max || '',
    job_type: job.job_type || 'Full-time',
    openings: job.openings || 1,
    deadline: job.deadline || '',
  });

  function handleChange(e) {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  }

  const textareaFields = ['description'];
  const numberFields = ['openings'];

  return (
    <div className="modal-overlay">
      <div className="modal edit-modal" role="dialog" aria-modal="true" aria-labelledby="edit-modal-title">
        <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        <h3 id="edit-modal-title">Edit Job Posting</h3>
        <div className="form-grid">
          {Object.entries(form).map(([key, val]) => {
            const label = key.replace(/_/g, ' ');
            if (textareaFields.includes(key)) {
              return (
                <label key={key} className="full-width">
                  {label}
                  <textarea
                    name={key}
                    value={val}
                    onChange={handleChange}
                    rows={4}
                  />
                </label>
              );
            }
            return (
              <label key={key}>
                {label}
                <input
                  type={numberFields.includes(key) ? 'number' : 'text'}
                  name={key}
                  value={val}
                  onChange={handleChange}
                />
              </label>
            );
          })}
        </div>
        <div className="modal-actions">
          <button className="btn-outline" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary"
            onClick={() => onSave(job.id, form)}
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
