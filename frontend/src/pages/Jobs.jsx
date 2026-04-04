// src/pages/Jobs.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchJobMatches, fetchJobPosts, applyForJob } from '../api';
import './Jobs.css';

function SkeletonCard() {
  return (
    <div className="jobs-skeleton-card">
      <div className="jobs-skel jobs-skel-title" />
      <div className="jobs-skel jobs-skel-sub" />
      <div className="jobs-skel jobs-skel-meta" />
      <div className="jobs-skel jobs-skel-body" />
      <div className="jobs-skel-chips">
        <div className="jobs-skel jobs-skel-chip" />
        <div className="jobs-skel jobs-skel-chip" />
        <div className="jobs-skel jobs-skel-chip" />
      </div>
    </div>
  );
}

function formatSalary(min, max) {
  if (!min && !max) return null;
  const fmt = (n) =>
    n >= 1000 ? `$${Math.round(n / 1000)}k` : `$${n}`;
  if (min && max) return `${fmt(min)} – ${fmt(max)}`;
  if (min) return `From ${fmt(min)}`;
  return `Up to ${fmt(max)}`;
}

function JobTypeChip({ type }) {
  const colorMap = {
    'Full-time': { bg: '#EEF2FF', color: '#4F46E5' },
    'Part-time': { bg: '#FFF7ED', color: '#C2410C' },
    'Contract': { bg: '#F0FDF4', color: '#15803D' },
    'Remote': { bg: '#F0F9FF', color: '#0369A1' },
  };
  const style = colorMap[type] || { bg: '#F3F4F6', color: '#374151' };
  return (
    <span
      className="jobs-type-chip"
      style={{ background: style.bg, color: style.color }}
    >
      {type}
    </span>
  );
}

function MatchBadge({ score }) {
  if (score == null) return null;
  const pct = Math.round(score);
  let bg = '#4F46E5';
  if (pct >= 80) bg = '#4F46E5';
  else if (pct >= 50) bg = '#7C3AED';
  else bg = '#9CA3AF';
  return (
    <span className="jobs-match-badge" style={{ background: bg }}>
      {pct}% match
    </span>
  );
}

function MatchBar({ score }) {
  if (score == null) return null;
  const pct = Math.round(score);
  let color = '#4F46E5';
  if (pct >= 80) color = '#16a34a';
  else if (pct >= 50) color = '#f59e0b';
  else color = '#9CA3AF';
  return (
    <div className="jobs-match-bar-container">
      <div className="jobs-match-bar">
        <div className="jobs-match-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="jobs-match-bar-label">{pct}%</span>
    </div>
  );
}

function SkillChip({ skill, variant }) {
  // variant: 'matched' | 'missing' | 'neutral'
  const styles = {
    matched: { bg: '#F0FDF4', color: '#15803D', border: '#BBF7D0' },
    missing: { bg: '#FFF7ED', color: '#C2410C', border: '#FED7AA' },
    neutral: { bg: '#EEF2FF', color: '#4F46E5', border: '#C7D2FE' },
  };
  const s = styles[variant] || styles.neutral;
  return (
    <span
      className="jobs-skill-chip"
      style={{ background: s.bg, color: s.color, borderColor: s.border }}
    >
      {skill}
    </span>
  );
}

function Toast({ message, type, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3500);
    return () => clearTimeout(t);
  }, [onClose]);

  return (
    <div className={`jobs-toast jobs-toast--${type}`}>
      <span>{message}</span>
      <button className="jobs-toast-close" onClick={onClose} aria-label="Close">×</button>
    </div>
  );
}

function JobModal({ job, onClose, isEmployee, onMessageEmployer }) {
  const [applying, setApplying] = useState(false);
  const [toast, setToast] = useState(null);

  const salary = formatSalary(job.salary_min, job.salary_max);

  const requiredSkills = job.required_skills
    ? job.required_skills.split(',').map((s) => s.trim()).filter(Boolean)
    : [];
  const preferredSkills = job.preferred_skills
    ? job.preferred_skills.split(',').map((s) => s.trim()).filter(Boolean)
    : [];
  const matchedSkills = job.matched_skills || [];
  const missingSkills = job.missing_skills || [];

  const handleApply = async () => {
    setApplying(true);
    try {
      await applyForJob(job.id);
      setToast({ message: 'Application submitted successfully!', type: 'success' });
    } catch (err) {
      if (err.status === 409) {
        setToast({ message: 'You have already applied for this job.', type: 'info' });
      } else {
        setToast({ message: 'Failed to apply. Please try again.', type: 'error' });
      }
    } finally {
      setApplying(false);
    }
  };

  // Close on backdrop click
  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="jobs-modal-backdrop" onClick={handleBackdropClick}>
      <div className="jobs-modal" role="dialog" aria-modal="true" aria-labelledby="jobs-modal-title">
        <button className="jobs-modal-close" onClick={onClose} aria-label="Close">×</button>

        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        <div className="jobs-modal-header">
          <div>
            <h2 id="jobs-modal-title" className="jobs-modal-title">{job.position}</h2>
            <p className="jobs-modal-company">{job.company}</p>
          </div>
          {job.match_score != null && <MatchBadge score={job.match_score} />}
        </div>

        <div className="jobs-modal-meta">
          {job.location && (
            <span className="jobs-modal-meta-item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              {job.location}
            </span>
          )}
          {job.job_type && <JobTypeChip type={job.job_type} />}
          {salary && <span className="jobs-modal-salary">{salary}</span>}
        </div>

        {job.description && (
          <div className="jobs-modal-section">
            <h3 className="jobs-modal-section-title">About this role</h3>
            <p className="jobs-modal-description">{job.description}</p>
          </div>
        )}

        {requiredSkills.length > 0 && (
          <div className="jobs-modal-section">
            <h3 className="jobs-modal-section-title">Required Skills</h3>
            <div className="jobs-skill-row">
              {requiredSkills.map((skill) => {
                const variant = matchedSkills.length > 0
                  ? (matchedSkills.includes(skill) ? 'matched' : 'missing')
                  : 'neutral';
                return <SkillChip key={skill} skill={skill} variant={variant} />;
              })}
            </div>
          </div>
        )}

        {preferredSkills.length > 0 && (
          <div className="jobs-modal-section">
            <h3 className="jobs-modal-section-title">Preferred Skills</h3>
            <div className="jobs-skill-row">
              {preferredSkills.map((skill) => (
                <SkillChip key={skill} skill={skill} variant="neutral" />
              ))}
            </div>
          </div>
        )}

        {isEmployee && (matchedSkills.length > 0 || missingSkills.length > 0) && (
          <div className="jobs-modal-section jobs-skill-gap">
            <h3 className="jobs-modal-section-title">Your Skill Gap</h3>
            {matchedSkills.length > 0 && (
              <div className="jobs-skill-gap-row">
                <span className="jobs-skill-gap-label jobs-skill-gap-label--have">You have:</span>
                <div className="jobs-skill-row">
                  {matchedSkills.map((s) => (
                    <SkillChip key={s} skill={s} variant="matched" />
                  ))}
                </div>
              </div>
            )}
            {missingSkills.length > 0 && (
              <div className="jobs-skill-gap-row">
                <span className="jobs-skill-gap-label jobs-skill-gap-label--missing">You're missing:</span>
                <div className="jobs-skill-row">
                  {missingSkills.map((s) => (
                    <SkillChip key={s} skill={s} variant="missing" />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {job.match_score != null && (
          <div className="jobs-modal-section">
            <h3 className="jobs-modal-section-title">Match Score</h3>
            <MatchBar score={job.match_score} />
          </div>
        )}

        {isEmployee && (
          <div className="jobs-modal-actions">
            <button
              className="jobs-apply-btn"
              onClick={handleApply}
              disabled={applying}
            >
              {applying ? 'Submitting…' : 'Apply Now'}
            </button>
            {job.employer_id && (
              <button
                className="jobs-message-btn"
                onClick={() => onMessageEmployer?.(job.employer_id)}
              >
                Message Employer
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function JobCard({ job, onClick, isEmployee }) {
  const salary = formatSalary(job.salary_min, job.salary_max);
  const matchedSkills = job.matched_skills || [];
  const missingSkills = job.missing_skills || [];

  // Determine which skills to show on the card (cap at 4)
  const requiredSkills = job.required_skills
    ? job.required_skills.split(',').map((s) => s.trim()).filter(Boolean)
    : [];
  const displaySkills = requiredSkills.slice(0, 4);

  return (
    <article className="jobs-card" role="button" onClick={onClick} tabIndex={0} onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onClick()}>
      <div className="jobs-card-header">
        <div className="jobs-card-title-group">
          <h3 className="jobs-card-title">{job.position}</h3>
          <p className="jobs-card-company">{job.company}</p>
        </div>
        {job.match_score != null && <MatchBadge score={job.match_score} />}
      </div>

      <div className="jobs-card-meta">
        {job.location && (
          <span className="jobs-card-meta-item">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            {job.location}
          </span>
        )}
        {job.job_type && <JobTypeChip type={job.job_type} />}
        {salary && <span className="jobs-card-salary">{salary}</span>}
      </div>

      {displaySkills.length > 0 && (
        <div className="jobs-card-skills">
          {displaySkills.map((skill) => {
            let variant = 'neutral';
            if (matchedSkills.length > 0 || missingSkills.length > 0) {
              variant = matchedSkills.includes(skill) ? 'matched' : 'missing';
            }
            return <SkillChip key={skill} skill={skill} variant={variant} />;
          })}
          {requiredSkills.length > 4 && (
            <span className="jobs-card-more">+{requiredSkills.length - 4} more</span>
          )}
        </div>
      )}

      {job.match_score != null && <MatchBar score={job.match_score} />}
    </article>
  );
}

const JOB_TYPES = ['All', 'Full-time', 'Part-time', 'Contract', 'Remote'];

export default function Jobs({ user: userProp }) {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedJob, setSelectedJob] = useState(null);

  // Filters
  const [locationFilter, setLocationFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [minMatch, setMinMatch] = useState(0);
  const navigate = useNavigate();

  // Use prop if available, fallback to localStorage
  const user = userProp || (() => {
    const raw = localStorage.getItem('user');
    try { return raw ? JSON.parse(raw) : null; } catch { return null; }
  })();
  const isEmployee = user ? user.role === 'employee' : false;

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        let data;
        if (isEmployee) {
          data = await fetchJobMatches();
        } else {
          data = await fetchJobPosts();
        }
        setJobs(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error(err);
        setError('Failed to load jobs. Please try again.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [isEmployee]);

  // Filtered jobs
  const filteredJobs = jobs.filter((job) => {
    if (locationFilter.trim()) {
      const loc = (job.location || '').toLowerCase();
      if (!loc.includes(locationFilter.trim().toLowerCase())) return false;
    }
    if (typeFilter !== 'All') {
      if ((job.job_type || '') !== typeFilter) return false;
    }
    if (isEmployee && job.match_score != null) {
      if (job.match_score < minMatch) return false;
    }
    return true;
  });

  return (
    <div className="jobs-page">
      {/* Sidebar */}
      <aside className="jobs-sidebar">
        <h2 className="jobs-sidebar-title">Filters</h2>

        <div className="jobs-filter-group">
          <label className="jobs-filter-label" htmlFor="location-filter">Location</label>
          <input
            id="location-filter"
            className="jobs-filter-input"
            type="text"
            placeholder="e.g. Remote, New York"
            value={locationFilter}
            onChange={(e) => setLocationFilter(e.target.value)}
          />
        </div>

        <div className="jobs-filter-group">
          <label className="jobs-filter-label" htmlFor="type-filter">Job Type</label>
          <select
            id="type-filter"
            className="jobs-filter-select"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            {JOB_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {isEmployee && (
          <div className="jobs-filter-group">
            <label className="jobs-filter-label" htmlFor="match-slider">
              Min Match Score: <strong>{minMatch}%</strong>
            </label>
            <input
              id="match-slider"
              className="jobs-filter-slider"
              type="range"
              min={0}
              max={100}
              value={minMatch}
              onChange={(e) => setMinMatch(Number(e.target.value))}
            />
            <div className="jobs-slider-ticks">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        )}

        {(locationFilter || typeFilter !== 'All' || minMatch > 0) && (
          <button
            className="jobs-clear-filters"
            onClick={() => { setLocationFilter(''); setTypeFilter('All'); setMinMatch(0); }}
          >
            Clear Filters
          </button>
        )}
      </aside>

      {/* Main content */}
      <main className="jobs-main">
        <div className="jobs-main-header">
          <div>
            <h1 className="jobs-main-title">
              {isEmployee ? 'Matched Jobs' : 'Browse Jobs'}
            </h1>
            {!loading && (
              <p className="jobs-main-sub">
                {filteredJobs.length} {filteredJobs.length === 1 ? 'job' : 'jobs'} found
              </p>
            )}
          </div>
        </div>

        {error && (
          <div className="jobs-error">
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="jobs-grid">
            {[1, 2, 3, 4, 5, 6].map((i) => <SkeletonCard key={i} />)}
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="jobs-empty">
            <div className="jobs-empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#C7D2FE" strokeWidth="1.5"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><line x1="12" y1="12" x2="12" y2="16"/><line x1="10" y1="14" x2="14" y2="14"/></svg>
            </div>
            <h3 className="jobs-empty-title">No jobs found</h3>
            <p className="jobs-empty-sub">Try adjusting your filters or check back later.</p>
          </div>
        ) : (
          <div className="jobs-grid">
            {filteredJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                isEmployee={isEmployee}
                onClick={() => setSelectedJob(job)}
              />
            ))}
          </div>
        )}
      </main>

      {selectedJob && (
        <JobModal
          job={selectedJob}
          isEmployee={isEmployee}
          onClose={() => setSelectedJob(null)}
          onMessageEmployer={(employerId) => navigate(`/messages?partner=${employerId}`)}
        />
      )}
    </div>
  );
}
