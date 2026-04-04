# Sprint 3: Job Seeker Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire job listings to the real MySQL API, display Prolog match scores with skill gap breakdown, implement real job application (apply/withdraw), and add a My Applications tracking page.
**Architecture:** The Application model is added to models.py and joins User to Job via a unique constraint. Flask endpoints handle apply/withdraw/list on the backend; the React frontend replaces the hardcoded JobMatch page with a live Jobs page that fetches all jobs and match data in parallel, plus a new Applications page for status tracking.
**Tech Stack:** Python 3 / Flask 2.3 / SQLAlchemy / MySQL / React 19 / React Router 6 / Webpack 5 / pytest / Jest

---

## File Map

| Action | Path |
|--------|------|
| Create | `tests/test_applications.py` |
| Modify | `models.py` — add `Application` model + relationships on `User` and `Job` |
| Modify | `app.py` — add apply / list / withdraw endpoints |
| Modify | `tests/conftest.py` — add `seeker_token`, `employer_token`, `sample_job` fixtures |
| Create | `frontend/src/pages/Jobs.jsx` |
| Create | `frontend/src/pages/Applications.jsx` |
| Modify | `frontend/src/api.js` — add application helper functions, remove broken `fetchJobs` |
| Modify | `frontend/src/App.jsx` — add `/jobs` and `/applications` routes, update Header nav |

---

### Task 3.1: Add Application Model to models.py

**Files:**
- Modify: `models.py`
- Modify: `tests/conftest.py`

- [ ] **Step 3.1.1: Write failing test**

```python
# tests/test_applications.py
import pytest

def test_application_model_exists(app):
    from models import Application
    assert Application.__tablename__ == 'applications'

def test_application_to_dict_keys(app):
    from models import Application
    from datetime import datetime
    # Instantiate without saving to DB — just check to_dict structure
    a = Application(job_id=1, user_id=1, status='pending')
    a.created_at = datetime(2026, 4, 4, 12, 0, 0)
    d = a.to_dict()
    for key in ('id', 'job_id', 'user_id', 'status', 'created_at'):
        assert key in d, f"Missing key: {key}"
```

Run: `pytest tests/test_applications.py::test_application_model_exists tests/test_applications.py::test_application_to_dict_keys -v`

Expected: FAILED with `ImportError: cannot import name 'Application' from 'models'`

- [ ] **Step 3.1.2: Implement Application model**

Open `models.py` and add the following. Add `from datetime import datetime` at the top if it is not already present.

```python
# Add inside models.py, after the Job class definition

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'shortlisted', 'withdrawn'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Unique constraint: one application per user per job
    __table_args__ = (db.UniqueConstraint('job_id', 'user_id', name='uq_application'),)

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
```

Also add the relationships to the existing `User` and `Job` model classes:

```python
# Inside class User (add after existing columns):
applications = db.relationship(
    'Application',
    backref='applicant',
    lazy='dynamic',
    cascade='all, delete-orphan',
    foreign_keys='Application.user_id'
)

# Inside class Job (add after existing columns):
applications = db.relationship(
    'Application',
    backref='job',
    lazy='dynamic',
    cascade='all, delete-orphan',
    foreign_keys='Application.job_id'
)
```

- [ ] **Step 3.1.3: Add shared test fixtures to conftest.py**

Append the three fixtures below to `tests/conftest.py` (keep existing `app` and `client` fixtures):

```python
# tests/conftest.py  — append below existing fixtures

@pytest.fixture
def seeker_token(client):
    client.post('/api/signup', json={
        'email': 'seeker@t.com', 'password': 'pass',
        'name': 'Seeker', 'role': 'employee'
    })
    res = client.post('/api/login', json={'email': 'seeker@t.com', 'password': 'pass'})
    return res.get_json()['token']


@pytest.fixture
def employer_token(client):
    client.post('/api/signup', json={
        'email': 'emp@t.com', 'password': 'pass',
        'name': 'Employer', 'role': 'employer'
    })
    res = client.post('/api/login', json={'email': 'emp@t.com', 'password': 'pass'})
    return res.get_json()['token']


@pytest.fixture
def sample_job(client, employer_token):
    res = client.post('/api/job-posts', json={
        'position': 'Python Dev',
        'company': 'TechCo',
        'location': 'Bangkok',
        'description': 'Build APIs',
        'required_skills': 'Python,Flask',
        'preferred_skills': 'Docker',
        'salary_min': '50000',
        'salary_max': '80000',
        'job_type': 'Full-time',
        'openings': 2,
        'deadline': '2026-12-31'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    return res.get_json()['job']
```

- [ ] **Step 3.1.4: Run model tests**

Run: `pytest tests/test_applications.py::test_application_model_exists tests/test_applications.py::test_application_to_dict_keys -v`

Expected: both PASSED

- [ ] **Step 3.1.5: Commit**

```bash
git add models.py tests/conftest.py tests/test_applications.py
git commit -m "feat: add Application model with unique constraint and conftest fixtures"
```

---

### Task 3.2: Add Application API Endpoints to app.py

**Files:**
- Modify: `app.py`
- Modify: `tests/test_applications.py`

- [ ] **Step 3.2.1: Write failing tests**

Append to `tests/test_applications.py`:

```python
# tests/test_applications.py  — append below existing tests

def test_apply_for_job(client, seeker_token, sample_job):
    res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data['application']['status'] == 'pending'
    assert data['application']['job_id'] == sample_job['id']


def test_application_unique_constraint(client, seeker_token, sample_job):
    # Apply once — should succeed
    res1 = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res1.status_code == 201
    # Apply again — should fail with 409
    res2 = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res2.status_code == 409


def test_get_my_applications(client, seeker_token, sample_job):
    client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    res = client.get('/api/applications', headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    apps = res.get_json()
    assert len(apps) == 1
    assert apps[0]['job']['position'] == 'Python Dev'


def test_withdraw_application(client, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']
    del_res = client.delete(
        f'/api/applications/{app_id}',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert del_res.status_code == 200
    # Verify actually removed
    list_res = client.get('/api/applications', headers={'Authorization': f'Bearer {seeker_token}'})
    assert len(list_res.get_json()) == 0


def test_employer_cannot_apply(client, employer_token, sample_job):
    res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 403


def test_apply_nonexistent_job(client, seeker_token):
    res = client.post(
        '/api/jobs/99999/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 404


def test_apply_requires_auth(client, sample_job):
    res = client.post(f'/api/jobs/{sample_job["id"]}/apply')
    assert res.status_code == 401


def test_withdraw_shortlisted_application_blocked(client, seeker_token, employer_token, sample_job):
    # Apply as seeker
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']

    # Employer shortlists the application
    client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'shortlisted'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )

    # Seeker tries to withdraw a shortlisted application
    del_res = client.delete(
        f'/api/applications/{app_id}',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert del_res.status_code == 400
```

Run: `pytest tests/test_applications.py -v`

Expected: all new tests FAILED with 404 (routes not yet defined)

- [ ] **Step 3.2.2: Implement the three endpoints in app.py**

Add the following after the existing job-post routes. Make sure `Application` is imported alongside `User` and `Job` at the top of `app.py`:

```python
# app.py — add near top import line, e.g.:
# from models import db, User, Job, Application
```

```python
# ── Job Application Endpoints ──────────────────────────────────────────────

@app.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
def apply_for_job(job_id):
    """Job seeker submits an application for a job."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"message": "Unauthorized"}), 401
    token = auth_header.split(' ')[1]
    parts = token.split('_')
    email = parts[1] if len(parts) >= 2 else None
    user = User.query.filter_by(email=email).first() if email else None
    if not user:
        return jsonify({"message": "Unauthorized"}), 401
    if user.role != 'employee':
        return jsonify({"message": "Only job seekers can apply"}), 403

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"message": "Job not found"}), 404

    existing = Application.query.filter_by(job_id=job_id, user_id=user.id).first()
    if existing:
        return jsonify({"message": "Already applied to this job"}), 409

    app_obj = Application(job_id=job_id, user_id=user.id, status='pending')
    db.session.add(app_obj)
    job.applicants = (job.applicants or 0) + 1
    db.session.commit()
    return jsonify({"message": "Application submitted", "application": app_obj.to_dict()}), 201


@app.route('/api/applications', methods=['GET'])
def get_my_applications():
    """Return all applications belonging to the logged-in job seeker, with job details."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"message": "Unauthorized"}), 401
    token = auth_header.split(' ')[1]
    parts = token.split('_')
    email = parts[1] if len(parts) >= 2 else None
    user = User.query.filter_by(email=email).first() if email else None
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    apps = Application.query.filter_by(user_id=user.id).all()
    result = []
    for a in apps:
        d = a.to_dict()
        job = Job.query.get(a.job_id)
        if job:
            d['job'] = job.to_dict()
        result.append(d)
    return jsonify(result), 200


@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
def withdraw_application(app_id):
    """Job seeker withdraws an application (not allowed when shortlisted)."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"message": "Unauthorized"}), 401
    token = auth_header.split(' ')[1]
    parts = token.split('_')
    email = parts[1] if len(parts) >= 2 else None
    user = User.query.filter_by(email=email).first() if email else None
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    application = Application.query.filter_by(id=app_id, user_id=user.id).first()
    if not application:
        return jsonify({"message": "Application not found"}), 404
    if application.status == 'shortlisted':
        return jsonify({"message": "Cannot withdraw a shortlisted application"}), 400

    job = Job.query.get(application.job_id)
    if job and (job.applicants or 0) > 0:
        job.applicants -= 1
    db.session.delete(application)
    db.session.commit()
    return jsonify({"message": "Application withdrawn"}), 200
```

- [ ] **Step 3.2.3: Run all application tests**

Run: `pytest tests/test_applications.py -v`

Expected: all tests PASSED

- [ ] **Step 3.2.4: Commit**

```bash
git add app.py tests/test_applications.py
git commit -m "feat: add apply/list/withdraw application endpoints with role guard"
```

---

### Task 3.3: Update frontend/src/api.js

**Files:**
- Modify: `frontend/src/api.js`

- [ ] **Step 3.3.1: Remove broken fetchJobs and add new helpers**

Open `frontend/src/api.js`. Remove any existing `fetchJobs` export (the old function that either hardcodes data or uses a broken endpoint). Then add the following exports:

```js
// frontend/src/api.js — add / replace

export async function fetchJobPosts() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/job-posts', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch jobs');
  return res.json();
}

export async function fetchJobMatches() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/jobs/matches', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch matches');
  return res.json();
}

export async function applyForJob(jobId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/jobs/${jobId}/apply`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return { ok: res.ok, status: res.status, data: await res.json() };
}

export async function fetchMyApplications() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/applications', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch applications');
  return res.json();
}

export async function withdrawApplication(appId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/applications/${appId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return { ok: res.ok, data: await res.json() };
}
```

- [ ] **Step 3.3.2: Verify no import errors**

Run: `cd frontend && npm run build 2>&1 | head -30`

Expected: build succeeds or only shows pre-existing warnings (no new errors from api.js)

- [ ] **Step 3.3.3: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat: add fetchJobPosts, fetchJobMatches, applyForJob, fetchMyApplications, withdrawApplication to api.js"
```

---

### Task 3.4: Create frontend/src/pages/Jobs.jsx

**Files:**
- Create: `frontend/src/pages/Jobs.jsx`

- [ ] **Step 3.4.1: Create the file**

Create `frontend/src/pages/Jobs.jsx` with the following complete content:

```jsx
// frontend/src/pages/Jobs.jsx
import React, { useState, useEffect } from 'react';
import { fetchJobPosts, fetchJobMatches, applyForJob, fetchMyApplications } from '../api';

export default function Jobs({ user }) {
  const [activeTab, setActiveTab] = useState('all');
  const [allJobs, setAllJobs] = useState([]);
  const [matchedJobs, setMatchedJobs] = useState([]);
  const [myApplications, setMyApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [applyLoading, setApplyLoading] = useState(false);
  const [applyMessage, setApplyMessage] = useState('');

  // Filter state
  const [filterLocation, setFilterLocation] = useState('');
  const [filterJobType, setFilterJobType] = useState('');
  const [filterMinMatch, setFilterMinMatch] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError('');
    try {
      const [jobs, apps] = await Promise.all([
        fetchJobPosts(),
        fetchMyApplications(),
      ]);
      setAllJobs(jobs);
      setMyApplications(apps);
      if (user && user.role === 'employee') {
        try {
          const matches = await fetchJobMatches();
          setMatchedJobs(matches);
        } catch {
          setMatchedJobs([]);
        }
      }
    } catch {
      setError('Failed to load jobs. Make sure you are logged in.');
    }
    setLoading(false);
  }

  function isApplied(jobId) {
    return myApplications.some(a => a.job_id === jobId);
  }

  function getMatchScore(jobId) {
    const match = matchedJobs.find(m => m.id === jobId);
    return match ? match.match_score : null;
  }

  function getMatchData(jobId) {
    return matchedJobs.find(m => m.id === jobId) || null;
  }

  function getScoreColor(score) {
    if (score === null || score === undefined) return '#6b7280';
    if (score >= 80) return '#16a34a';
    if (score >= 50) return '#6366f1';
    return '#6b7280';
  }

  async function handleApply(jobId) {
    setApplyLoading(true);
    setApplyMessage('');
    const result = await applyForJob(jobId);
    if (result.ok) {
      setApplyMessage('Application submitted successfully!');
      await loadData();
    } else if (result.status === 409) {
      setApplyMessage('You have already applied to this job.');
    } else {
      setApplyMessage('Failed to apply. Please try again.');
    }
    setApplyLoading(false);
  }

  function applyFilters(jobs) {
    return jobs.filter(job => {
      if (
        filterLocation &&
        !job.location.toLowerCase().includes(filterLocation.toLowerCase())
      ) return false;
      if (filterJobType && job.job_type !== filterJobType) return false;
      if (filterMinMatch > 0) {
        const score = getMatchScore(job.id);
        if (!score || score < filterMinMatch) return false;
      }
      return true;
    });
  }

  const sourceJobs = activeTab === 'matches' ? matchedJobs : allJobs;
  const displayJobs = applyFilters(sourceJobs);

  if (loading) return <div className="loading">Loading jobs...</div>;

  return (
    <div className="jobs-page">
      {error && <div className="error-banner">{error}</div>}

      <div className="jobs-tabs">
        <button
          className={`tab-btn${activeTab === 'all' ? ' active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          All Jobs ({allJobs.length})
        </button>
        {user && user.role === 'employee' && (
          <button
            className={`tab-btn${activeTab === 'matches' ? ' active' : ''}`}
            onClick={() => setActiveTab('matches')}
          >
            My Matches ({matchedJobs.length})
          </button>
        )}
      </div>

      <div className="jobs-layout">
        <aside className="jobs-sidebar">
          <h3>Filters</h3>

          <label>
            Location
            <input
              type="text"
              placeholder="e.g. Bangkok"
              value={filterLocation}
              onChange={e => setFilterLocation(e.target.value)}
            />
          </label>

          <label>
            Job Type
            <select
              value={filterJobType}
              onChange={e => setFilterJobType(e.target.value)}
            >
              <option value="">All Types</option>
              <option>Full-time</option>
              <option>Part-time</option>
              <option>Remote</option>
              <option>Contract</option>
            </select>
          </label>

          {user && user.role === 'employee' && (
            <label>
              Min Match %
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={filterMinMatch}
                onChange={e => setFilterMinMatch(Number(e.target.value))}
              />
              <span>{filterMinMatch}%</span>
            </label>
          )}

          <button
            className="btn-outline"
            onClick={() => {
              setFilterLocation('');
              setFilterJobType('');
              setFilterMinMatch(0);
            }}
          >
            Clear Filters
          </button>
        </aside>

        <main className="jobs-grid">
          {displayJobs.length === 0 && (
            <div className="empty-state">
              <p>No jobs found. Try adjusting your filters.</p>
            </div>
          )}
          {displayJobs.map(job => {
            const score = getMatchScore(job.id);
            const applied = isApplied(job.id);
            return (
              <div
                key={job.id}
                className="job-card"
                onClick={() => {
                  setSelectedJob(job);
                  setApplyMessage('');
                }}
              >
                <div className="job-card-header">
                  <div>
                    <h3>{job.position}</h3>
                    <p>{job.company} &bull; {job.location}</p>
                  </div>
                  {score !== null && (
                    <span
                      className="score-badge"
                      style={{ background: getScoreColor(score) }}
                    >
                      {score}%
                    </span>
                  )}
                </div>

                <div className="job-meta">
                  <span>{job.job_type}</span>
                  {job.salary_min && (
                    <span>฿{job.salary_min}–{job.salary_max}</span>
                  )}
                </div>

                <div className="job-skills">
                  {(job.required_skills || '')
                    .split(',')
                    .filter(Boolean)
                    .slice(0, 3)
                    .map(s => (
                      <span key={s} className="skill-tag">{s.trim()}</span>
                    ))}
                </div>

                {applied && <div className="applied-badge">Applied ✓</div>}
              </div>
            );
          })}
        </main>
      </div>

      {selectedJob && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedJob(null)}
        >
          <div className="modal" onClick={e => e.stopPropagation()}>
            <button
              className="modal-close"
              onClick={() => setSelectedJob(null)}
            >
              ✕
            </button>

            <h2>{selectedJob.position}</h2>
            <p className="modal-company">
              {selectedJob.company} &bull; {selectedJob.location} &bull; {selectedJob.job_type}
            </p>

            {selectedJob.salary_min && (
              <p>Salary: ฿{selectedJob.salary_min} – ฿{selectedJob.salary_max}</p>
            )}
            <p className="modal-deadline">Deadline: {selectedJob.deadline}</p>

            {(() => {
              const matchData = getMatchData(selectedJob.id);
              if (!matchData) return null;
              return (
                <div className="skill-gap-section">
                  <div className="match-score-ring">
                    <span style={{ color: getScoreColor(matchData.match_score) }}>
                      {matchData.match_score}% Match
                    </span>
                  </div>
                  <div className="skill-rows">
                    <div>
                      <strong>Matched Skills</strong>
                      <div className="skill-tags">
                        {matchData.matched_skills.length === 0
                          ? <span className="muted">None</span>
                          : matchData.matched_skills.map(s => (
                              <span key={s} className="skill-tag matched">✓ {s}</span>
                            ))}
                      </div>
                    </div>
                    <div>
                      <strong>Missing Skills</strong>
                      <div className="skill-tags">
                        {matchData.missing_skills.length === 0
                          ? <span className="muted">None — perfect match!</span>
                          : matchData.missing_skills.map(s => (
                              <span key={s} className="skill-tag missing">✗ {s}</span>
                            ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()}

            <h4>Description</h4>
            <p>{selectedJob.description}</p>

            <h4>Required Skills</h4>
            <div className="skill-tags">
              {(selectedJob.required_skills || '')
                .split(',')
                .filter(Boolean)
                .map(s => (
                  <span key={s} className="skill-tag">{s.trim()}</span>
                ))}
            </div>

            {selectedJob.preferred_skills && (
              <>
                <h4>Preferred Skills</h4>
                <div className="skill-tags">
                  {selectedJob.preferred_skills
                    .split(',')
                    .filter(Boolean)
                    .map(s => (
                      <span key={s} className="skill-tag preferred">{s.trim()}</span>
                    ))}
                </div>
              </>
            )}

            {applyMessage && (
              <div className="apply-message">{applyMessage}</div>
            )}

            {user && user.role === 'employee' && (
              isApplied(selectedJob.id)
                ? (
                  <button className="btn-primary" disabled>
                    Applied ✓
                  </button>
                )
                : (
                  <button
                    className="btn-primary"
                    disabled={applyLoading}
                    onClick={() => handleApply(selectedJob.id)}
                  >
                    {applyLoading ? 'Applying...' : 'Apply Now'}
                  </button>
                )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3.4.2: Verify build**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Expected: no new errors; bundle builds successfully

- [ ] **Step 3.4.3: Commit**

```bash
git add frontend/src/pages/Jobs.jsx
git commit -m "feat: create Jobs page with real API, match scores, skill gap view, and apply button"
```

---

### Task 3.5: Create frontend/src/pages/Applications.jsx

**Files:**
- Create: `frontend/src/pages/Applications.jsx`

- [ ] **Step 3.5.1: Create the file**

Create `frontend/src/pages/Applications.jsx` with the following complete content:

```jsx
// frontend/src/pages/Applications.jsx
import React, { useState, useEffect } from 'react';
import { fetchMyApplications, withdrawApplication } from '../api';

const STATUS_COLORS = {
  pending: '#6366f1',
  shortlisted: '#16a34a',
  withdrawn: '#9ca3af',
};

export default function Applications({ user }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadApplications();
  }, []);

  async function loadApplications() {
    setLoading(true);
    try {
      const apps = await fetchMyApplications();
      setApplications(apps);
    } catch {
      setMessage('Failed to load applications.');
    }
    setLoading(false);
  }

  async function handleWithdraw(appId) {
    if (!window.confirm('Withdraw this application?')) return;
    const result = await withdrawApplication(appId);
    if (result.ok) {
      setMessage('Application withdrawn.');
      loadApplications();
    } else {
      setMessage(result.data.message || 'Could not withdraw application.');
    }
  }

  if (loading) return <div className="loading">Loading applications...</div>;

  return (
    <div className="applications-page">
      <h2>My Applications</h2>

      {message && <div className="info-banner">{message}</div>}

      {applications.length === 0 ? (
        <div className="empty-state">
          <p>You haven&apos;t applied to any jobs yet.</p>
        </div>
      ) : (
        <table className="applications-table">
          <thead>
            <tr>
              <th>Position</th>
              <th>Company</th>
              <th>Applied</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {applications.map(app => (
              <tr key={app.id}>
                <td>{app.job?.position || '—'}</td>
                <td>{app.job?.company || '—'}</td>
                <td>{new Date(app.created_at).toLocaleDateString()}</td>
                <td>
                  <span
                    className="status-chip"
                    style={{
                      background: STATUS_COLORS[app.status] || '#6b7280',
                      color: '#fff',
                      padding: '2px 10px',
                      borderRadius: '12px',
                      fontSize: '0.85em',
                    }}
                  >
                    {app.status}
                  </span>
                </td>
                <td>
                  {app.status !== 'withdrawn' && app.status !== 'shortlisted' && (
                    <button
                      className="btn-danger-sm"
                      onClick={() => handleWithdraw(app.id)}
                    >
                      Withdraw
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
```

- [ ] **Step 3.5.2: Verify build**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Expected: no new errors

- [ ] **Step 3.5.3: Commit**

```bash
git add frontend/src/pages/Applications.jsx
git commit -m "feat: create Applications page with withdraw action and status badges"
```

---

### Task 3.6: Update App.jsx Routing and Navigation

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 3.6.1: Add imports and routes**

In `frontend/src/App.jsx`, add the following imports near the top (after existing page imports):

```jsx
import Jobs from './pages/Jobs';
import Applications from './pages/Applications';
```

Inside the logged-in `<Routes>` block, replace or supplement the existing `/jobs` (or `/job-match`) route with:

```jsx
<Route
  path="/jobs"
  element={
    <>
      <Header user={user} onLogout={handleLogout} />
      <Jobs user={user} />
    </>
  }
/>
<Route
  path="/applications"
  element={
    <>
      <Header user={user} onLogout={handleLogout} />
      <Applications user={user} />
    </>
  }
/>
```

Note: keep `JobMatch.jsx` and its route intact for now. It will be retired in Sprint 5. If an existing `/job-match` route exists, leave it. The new canonical path for job seekers is `/jobs`.

- [ ] **Step 3.6.2: Add "My Applications" link in Header**

In the Header component (either inside `App.jsx` or `frontend/src/components/Header.jsx`), add a navigation link for employee users:

```jsx
{user && user.role === 'employee' && (
  <Link to="/applications">My Applications</Link>
)}
```

Place it after the "Find Jobs" / "My Matches" links.

- [ ] **Step 3.6.3: Verify build and manual smoke test**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Then start both servers and manually verify:
1. Log in as an employee — navigate to `/jobs`; job cards load from the real API.
2. Click a job card — modal opens showing description and skills.
3. Click "Apply Now" — button changes to "Applied ✓" on success.
4. Navigate to `/applications` — the applied job appears in the table.
5. Click "Withdraw" — row disappears from the table.

- [ ] **Step 3.6.4: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: wire /jobs and /applications routes into App.jsx with Header nav update"
```

---

### Sprint 3 Final Verification

- [ ] **Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all tests in `test_applications.py` and any pre-existing tests PASSED, no regressions

- [ ] **Final sprint commit (if any stray changes remain)**

```bash
git add -p
git commit -m "chore: sprint 3 cleanup and final test pass"
```
