// frontend/src/pages/MyJobs.jsx
import React, { useState, useEffect } from 'react';
import { fetchEmployerJobs, updateJobPost, deleteJobPost } from '../api';
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
    try {
      const data = await fetchEmployerJobs();
      setJobs(data.jobs || []);
    } catch {
      setMessage('Failed to load jobs.');
    }
    setLoading(false);
  }

  async function handleArchive(jobId) {
    try {
      const { ok, data } = await updateJobPost(jobId, { status: 'archived' });
      setMessage(ok ? 'Job archived.' : (data.message || 'Failed to archive job.'));
      if (ok) loadMyJobs();
    } catch {
      setMessage('Network error. Could not archive job.');
    }
  }

  async function handlePublish(jobId) {
    try {
      const { ok, data } = await updateJobPost(jobId, { status: 'active' });
      setMessage(ok ? 'Job published.' : (data.message || 'Failed to publish job.'));
      if (ok) loadMyJobs();
    } catch {
      setMessage('Network error. Could not publish job.');
    }
  }

  async function handleDelete(jobId) {
    try {
      const { ok, data } = await deleteJobPost(jobId);
      if (ok) {
        setMessage('Job posting deleted.');
        setDeleteConfirm(null);
        loadMyJobs();
      } else {
        setMessage(data.message || 'Failed to delete job.');
      }
    } catch {
      setMessage('Network error. Could not delete job.');
      setDeleteConfirm(null);
    }
  }

  async function handleUpdate(jobId, formData) {
    try {
      const { ok, data } = await updateJobPost(jobId, formData);
      if (ok) {
        setMessage('Job posting updated.');
        setEditJob(null);
        loadMyJobs();
      } else {
        setMessage(data.message || 'Failed to update job.');
      }
    } catch {
      setMessage('Network error. Could not update job.');
    }
  }

  const filteredJobs = filter === 'all' ? jobs : jobs.filter(j => j.status === filter);

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

      <div className="myjobs-tabs">
        {['all', 'active', 'draft', 'archived'].map(tab => (
          <button
            key={tab}
            className={`myjobs-tab${filter === tab ? ' active' : ''}`}
            onClick={() => setFilter(tab)}
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
                <td><span className={`myjobs-status myjobs-status--${job.status}`}>{job.status}</span></td>
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
