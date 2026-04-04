// frontend/src/pages/MyJobs.jsx
import React, { useState, useEffect } from 'react';

export default function MyJobs({ user, navigate }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editJob, setEditJob] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadMyJobs();
  }, []);

  async function loadMyJobs() {
    setLoading(true);
    const token = localStorage.getItem('token');
    try {
      const res = await fetch('/api/job-posts', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const allJobs = await res.json();
      // Filter to only this employer's jobs
      const myJobs = allJobs.filter(j => j.employer_id === user.id);
      setJobs(myJobs);
    } catch {
      setMessage('Failed to load jobs.');
    }
    setLoading(false);
  }

  async function handleDelete(jobId) {
    const token = localStorage.getItem('token');
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
  }

  async function handleUpdate(jobId, formData) {
    const token = localStorage.getItem('token');
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
  }

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

      {jobs.length === 0 ? (
        <div className="empty-state">
          <p>No job postings yet.</p>
          <button className="btn-primary" onClick={() => navigate('/create-job')}>
            Create your first posting
          </button>
        </div>
      ) : (
        <table className="jobs-table">
          <thead>
            <tr>
              <th>Position</th>
              <th>Company</th>
              <th>Location</th>
              <th>Applicants</th>
              <th>Deadline</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map(job => (
              <tr key={job.id}>
                <td>{job.position}</td>
                <td>{job.company}</td>
                <td>{job.location}</td>
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
          <div className="modal confirm-modal">
            <h3>Delete Job Posting?</h3>
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
      <div className="modal edit-modal">
        <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        <h3>Edit Job Posting</h3>
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
