# Sprint 4: Employer Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add edit and delete for employer job postings, employer view of ranked applicants with shortlisting capability, and an employer dashboard summarising posting and applicant statistics.
**Architecture:** Three new backend routes handle PUT/DELETE on job posts and PATCH on application status; a fourth route serves dashboard aggregate data. On the frontend three new pages are added — MyJobs (list + edit + delete), Applicants (ranked table with shortlisting), and Dashboard (stats + quick actions) — all gated behind the employer role. App.jsx receives updated routing and role-aware Header navigation.
**Tech Stack:** Python 3 / Flask 2.3 / SQLAlchemy / MySQL / React 19 / React Router 6 / Webpack 5 / pytest

---

## File Map

| Action | Path |
|--------|------|
| Create | `tests/test_employer.py` |
| Modify | `app.py` — add PUT/DELETE `/api/job-posts/<id>`, GET `/api/job-posts/<id>/applicants`, PATCH `/api/applications/<id>/status`, GET `/api/employer/dashboard` |
| Create | `frontend/src/pages/MyJobs.jsx` |
| Create | `frontend/src/pages/Applicants.jsx` |
| Create | `frontend/src/pages/Dashboard.jsx` |
| Modify | `frontend/src/api.js` — add employer helper functions |
| Modify | `frontend/src/App.jsx` — add employer routes and role-aware Header nav |

**Prerequisite:** Sprint 3 must be complete. `tests/conftest.py` must already contain the `seeker_token`, `employer_token`, and `sample_job` fixtures added in Sprint 3 Task 3.1.

---

### Task 4.1: Add PUT and DELETE /api/job-posts/<id>

**Files:**
- Modify: `app.py`
- Create: `tests/test_employer.py`

- [ ] **Step 4.1.1: Write failing tests**

Create `tests/test_employer.py` with the following content:

```python
# tests/test_employer.py
import pytest


# ── PUT /api/job-posts/<id> ────────────────────────────────────────────────

def test_update_own_job(client, employer_token, sample_job):
    res = client.put(
        f'/api/job-posts/{sample_job["id"]}',
        json={'position': 'Senior Python Dev'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    assert res.get_json()['job']['position'] == 'Senior Python Dev'


def test_update_partial_fields(client, employer_token, sample_job):
    res = client.put(
        f'/api/job-posts/{sample_job["id"]}',
        json={'salary_min': '60000', 'salary_max': '90000'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    job = res.get_json()['job']
    assert job['salary_min'] == '60000'
    assert job['position'] == 'Python Dev'   # unchanged


def test_cannot_update_other_employers_job(client, sample_job):
    # Create a second employer
    client.post('/api/signup', json={
        'email': 'emp2@t.com', 'password': 'p',
        'name': 'E2', 'role': 'employer'
    })
    res2 = client.post('/api/login', json={'email': 'emp2@t.com', 'password': 'p'})
    token2 = res2.get_json()['token']

    res = client.put(
        f'/api/job-posts/{sample_job["id"]}',
        json={'position': 'Hacked'},
        headers={'Authorization': f'Bearer {token2}'}
    )
    assert res.status_code == 404


def test_update_requires_employer_role(client, seeker_token, sample_job):
    res = client.put(
        f'/api/job-posts/{sample_job["id"]}',
        json={'position': 'Hacked'},
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 403


# ── DELETE /api/job-posts/<id> ─────────────────────────────────────────────

def test_delete_own_job(client, employer_token, sample_job):
    res = client.delete(
        f'/api/job-posts/{sample_job["id"]}',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200

    # Verify the job is actually gone
    list_res = client.get('/api/job-posts')
    jobs = list_res.get_json()
    assert not any(j['id'] == sample_job['id'] for j in jobs)


def test_cannot_delete_other_employers_job(client, sample_job):
    client.post('/api/signup', json={
        'email': 'emp3@t.com', 'password': 'p',
        'name': 'E3', 'role': 'employer'
    })
    r = client.post('/api/login', json={'email': 'emp3@t.com', 'password': 'p'})
    token3 = r.get_json()['token']

    res = client.delete(
        f'/api/job-posts/{sample_job["id"]}',
        headers={'Authorization': f'Bearer {token3}'}
    )
    assert res.status_code == 404


def test_seeker_cannot_delete_job(client, seeker_token, sample_job):
    res = client.delete(
        f'/api/job-posts/{sample_job["id"]}',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 403


def test_delete_nonexistent_job(client, employer_token):
    res = client.delete(
        '/api/job-posts/99999',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 404
```

Run: `pytest tests/test_employer.py::test_update_own_job tests/test_employer.py::test_delete_own_job -v`

Expected: FAILED with 405 Method Not Allowed (routes not yet defined)

- [ ] **Step 4.1.2: Implement PUT and DELETE endpoints in app.py**

The project uses a `@require_role` decorator that injects the authenticated user as the first positional argument. Add the two endpoints after the existing POST `/api/job-posts` route:

```python
# app.py — add after existing POST /api/job-posts

@app.route('/api/job-posts/<int:job_id>', methods=['PUT'])
@require_role('employer')
def update_job_post(employer, job_id):
    """Employer edits their own job posting."""
    job = Job.query.filter_by(id=job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    data = request.get_json()
    updatable_fields = [
        'position', 'company', 'location', 'description',
        'required_skills', 'preferred_skills',
        'salary_min', 'salary_max', 'job_type', 'openings', 'deadline'
    ]
    for field in updatable_fields:
        if field in data:
            setattr(job, field, data[field])

    db.session.commit()
    return jsonify({"message": "Job updated", "job": job.to_dict()}), 200


@app.route('/api/job-posts/<int:job_id>', methods=['DELETE'])
@require_role('employer')
def delete_job_post(employer, job_id):
    """Employer deletes their own job posting (cascades to applications)."""
    job = Job.query.filter_by(id=job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job deleted"}), 200
```

- [ ] **Step 4.1.3: Run all PUT/DELETE tests**

Run: `pytest tests/test_employer.py -v -k "update or delete"`

Expected: all eight tests PASSED

- [ ] **Step 4.1.4: Commit**

```bash
git add app.py tests/test_employer.py
git commit -m "feat: add PUT and DELETE /api/job-posts/<id> with ownership guard"
```

---

### Task 4.2: Add GET Applicants and PATCH Application Status Endpoints

**Files:**
- Modify: `app.py`
- Modify: `tests/test_employer.py`

- [ ] **Step 4.2.1: Write failing tests**

Append to `tests/test_employer.py`:

```python
# tests/test_employer.py  — append below existing tests

# ── GET /api/job-posts/<id>/applicants ─────────────────────────────────────

def test_employer_can_view_applicants(client, employer_token, seeker_token, sample_job):
    # Seeker applies
    client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    res = client.get(
        f'/api/job-posts/{sample_job["id"]}/applicants',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    applicants = res.get_json()
    assert len(applicants) == 1
    assert applicants[0]['name'] == 'Seeker'


def test_applicants_response_includes_match_fields(client, employer_token, seeker_token, sample_job):
    client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    res = client.get(
        f'/api/job-posts/{sample_job["id"]}/applicants',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    a = res.get_json()[0]
    for field in ('application_id', 'status', 'applied_at', 'name', 'email',
                  'match_score', 'matched_skills', 'missing_skills'):
        assert field in a, f"Missing field: {field}"


def test_applicants_sorted_by_match_score_descending(client, employer_token, sample_job):
    # Create two seekers with different skills
    client.post('/api/signup', json={
        'email': 'high@t.com', 'password': 'p', 'name': 'High',
        'role': 'employee'
    })
    client.post('/api/signup', json={
        'email': 'low@t.com', 'password': 'p', 'name': 'Low',
        'role': 'employee'
    })
    # Give high-match seeker skills matching the job
    high_login = client.post('/api/login', json={'email': 'high@t.com', 'password': 'p'})
    high_token = high_login.get_json()['token']
    client.put('/api/profile', json={'skills': 'Python,Flask,Docker'},
               headers={'Authorization': f'Bearer {high_token}'})

    low_login = client.post('/api/login', json={'email': 'low@t.com', 'password': 'p'})
    low_token = low_login.get_json()['token']
    # low seeker has no matching skills

    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {high_token}'})
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {low_token}'})

    res = client.get(f'/api/job-posts/{sample_job["id"]}/applicants',
                     headers={'Authorization': f'Bearer {employer_token}'})
    applicants = res.get_json()
    assert applicants[0]['match_score'] >= applicants[-1]['match_score']


def test_seeker_cannot_view_applicants(client, seeker_token, sample_job):
    res = client.get(
        f'/api/job-posts/{sample_job["id"]}/applicants',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 403


# ── PATCH /api/applications/<id>/status ───────────────────────────────────

def test_employer_can_shortlist(client, employer_token, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']

    res = client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'shortlisted'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    assert res.get_json()['application']['status'] == 'shortlisted'


def test_employer_can_unshortlist(client, employer_token, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']
    # Shortlist first
    client.patch(f'/api/applications/{app_id}/status',
                 json={'status': 'shortlisted'},
                 headers={'Authorization': f'Bearer {employer_token}'})
    # Then revert to pending
    res = client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'pending'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    assert res.get_json()['application']['status'] == 'pending'


def test_invalid_status_rejected(client, employer_token, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']
    res = client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'hired'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 400


def test_employer_cannot_change_status_of_other_employers_application(
        client, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']

    # Second employer tries to shortlist
    client.post('/api/signup', json={
        'email': 'emp4@t.com', 'password': 'p', 'name': 'E4', 'role': 'employer'
    })
    r = client.post('/api/login', json={'email': 'emp4@t.com', 'password': 'p'})
    token4 = r.get_json()['token']

    res = client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'shortlisted'},
        headers={'Authorization': f'Bearer {token4}'}
    )
    assert res.status_code == 403
```

Run: `pytest tests/test_employer.py -v -k "applicant or shortlist or status"`

Expected: all new tests FAILED (routes not yet defined)

- [ ] **Step 4.2.2: Implement the two endpoints in app.py**

```python
# app.py — add after the DELETE /api/job-posts/<id> route

@app.route('/api/job-posts/<int:job_id>/applicants', methods=['GET'])
@require_role('employer')
def get_job_applicants(employer, job_id):
    """Return all applicants for a job, ranked by match score."""
    job = Job.query.filter_by(id=job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    apps = Application.query.filter_by(job_id=job_id).all()
    result = []
    required = [s.strip().lower() for s in (job.required_skills or '').split(',') if s.strip()]
    preferred = [s.strip().lower() for s in (job.preferred_skills or '').split(',') if s.strip()]
    all_required = required + preferred

    for a in apps:
        applicant = User.query.get(a.user_id)
        if not applicant:
            continue
        candidate_skills = [
            s.strip().lower()
            for s in (applicant.skills or '').split(',') if s.strip()
        ]
        matched = [s for s in required if s in candidate_skills]
        missing = [s for s in required if s not in candidate_skills]
        # Score: 70% weight on required skill overlap
        score = round((len(matched) / len(required) * 70) if required else 0)
        result.append({
            'application_id': a.id,
            'status': a.status,
            'applied_at': a.created_at.isoformat(),
            'user_id': applicant.id,
            'name': applicant.name,
            'email': applicant.email,
            'skills': applicant.skills,
            'match_score': score,
            'matched_skills': matched,
            'missing_skills': missing,
        })

    result.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(result), 200


@app.route('/api/applications/<int:app_id>/status', methods=['PATCH'])
@require_role('employer')
def update_application_status(employer, app_id):
    """Employer sets an application's status (pending / shortlisted / withdrawn)."""
    application = Application.query.get(app_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    # Verify the application's job belongs to this employer
    job = Job.query.filter_by(id=application.job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Forbidden"}), 403

    data = request.get_json()
    new_status = data.get('status')
    if new_status not in ('pending', 'shortlisted', 'withdrawn'):
        return jsonify({"message": "Invalid status. Must be pending, shortlisted, or withdrawn"}), 400

    application.status = new_status
    db.session.commit()
    return jsonify({"message": "Status updated", "application": application.to_dict()}), 200
```

- [ ] **Step 4.2.3: Run all employer tests so far**

Run: `pytest tests/test_employer.py -v`

Expected: all tests PASSED

- [ ] **Step 4.2.4: Commit**

```bash
git add app.py tests/test_employer.py
git commit -m "feat: add GET applicants (ranked) and PATCH application status endpoints"
```

---

### Task 4.3: Add GET /api/employer/dashboard

**Files:**
- Modify: `app.py`
- Modify: `tests/test_employer.py`

- [ ] **Step 4.3.1: Write failing tests**

Append to `tests/test_employer.py`:

```python
# tests/test_employer.py  — append below existing tests

# ── GET /api/employer/dashboard ────────────────────────────────────────────

def test_dashboard_returns_stats(client, employer_token, sample_job):
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 200
    data = res.get_json()
    for key in ('total_jobs', 'total_applicants', 'total_shortlisted', 'recent_applications'):
        assert key in data, f"Missing key: {key}"


def test_dashboard_counts_jobs(client, employer_token, sample_job):
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.get_json()['total_jobs'] == 1


def test_dashboard_counts_applicants(client, employer_token, seeker_token, sample_job):
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {seeker_token}'})
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.get_json()['total_applicants'] == 1


def test_dashboard_counts_shortlisted(client, employer_token, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']
    client.patch(f'/api/applications/{app_id}/status',
                 json={'status': 'shortlisted'},
                 headers={'Authorization': f'Bearer {employer_token}'})

    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.get_json()['total_shortlisted'] == 1


def test_dashboard_recent_applications_structure(client, employer_token, seeker_token, sample_job):
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {seeker_token}'})
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    recent = res.get_json()['recent_applications']
    assert len(recent) == 1
    for key in ('applicant_name', 'job_position', 'applied_at', 'status'):
        assert key in recent[0], f"Missing key in recent_applications: {key}"


def test_dashboard_requires_employer_role(client, seeker_token):
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 403


def test_dashboard_empty_for_new_employer(client):
    client.post('/api/signup', json={
        'email': 'fresh@t.com', 'password': 'p',
        'name': 'Fresh', 'role': 'employer'
    })
    r = client.post('/api/login', json={'email': 'fresh@t.com', 'password': 'p'})
    token = r.get_json()['token']
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {token}'})
    data = res.get_json()
    assert data['total_jobs'] == 0
    assert data['total_applicants'] == 0
    assert data['total_shortlisted'] == 0
    assert data['recent_applications'] == []
```

Run: `pytest tests/test_employer.py -v -k "dashboard"`

Expected: all new tests FAILED with 404 (route not yet defined)

- [ ] **Step 4.3.2: Implement the dashboard endpoint in app.py**

```python
# app.py — add after the PATCH /api/applications/<id>/status route

@app.route('/api/employer/dashboard', methods=['GET'])
@require_role('employer')
def employer_dashboard(employer):
    """Aggregate stats for the employer's dashboard."""
    jobs = Job.query.filter_by(employer_id=employer.id).all()
    total_jobs = len(jobs)
    total_applicants = sum(j.applicants or 0 for j in jobs)
    job_ids = [j.id for j in jobs]

    total_shortlisted = (
        Application.query.filter(
            Application.job_id.in_(job_ids),
            Application.status == 'shortlisted'
        ).count()
        if job_ids else 0
    )

    recent_apps = (
        Application.query
        .filter(Application.job_id.in_(job_ids))
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
        if job_ids else []
    )

    recent = []
    for a in recent_apps:
        applicant = User.query.get(a.user_id)
        job = Job.query.get(a.job_id)
        if applicant and job:
            recent.append({
                'applicant_name': applicant.name,
                'job_position': job.position,
                'applied_at': a.created_at.isoformat(),
                'status': a.status,
            })

    return jsonify({
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'total_shortlisted': total_shortlisted,
        'recent_applications': recent,
    }), 200
```

- [ ] **Step 4.3.3: Run all employer tests**

Run: `pytest tests/test_employer.py -v`

Expected: all tests PASSED

- [ ] **Step 4.3.4: Run full test suite to check for regressions**

Run: `pytest tests/ -v`

Expected: all tests across all files PASSED

- [ ] **Step 4.3.5: Commit**

```bash
git add app.py tests/test_employer.py
git commit -m "feat: add GET /api/employer/dashboard with job/applicant/shortlist counts"
```

---

### Task 4.4: Create frontend/src/pages/MyJobs.jsx

**Files:**
- Create: `frontend/src/pages/MyJobs.jsx`

- [ ] **Step 4.4.1: Create the file**

Create `frontend/src/pages/MyJobs.jsx` with the following complete content:

```jsx
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
        <button className="modal-close" onClick={onClose}>✕</button>
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
```

- [ ] **Step 4.4.2: Verify build**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Expected: no new errors

- [ ] **Step 4.4.3: Commit**

```bash
git add frontend/src/pages/MyJobs.jsx
git commit -m "feat: create MyJobs page with edit modal, delete confirmation, and applicant navigation"
```

---

### Task 4.5: Create frontend/src/pages/Applicants.jsx

**Files:**
- Create: `frontend/src/pages/Applicants.jsx`

- [ ] **Step 4.5.1: Create the file**

Create `frontend/src/pages/Applicants.jsx` with the following complete content:

```jsx
// frontend/src/pages/Applicants.jsx
import React, { useState, useEffect } from 'react';

const SCORE_COLOR = score => {
  if (score >= 80) return '#16a34a';
  if (score >= 50) return '#6366f1';
  return '#9ca3af';
};

const STATUS_COLORS = {
  pending: '#6366f1',
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
```

- [ ] **Step 4.5.2: Verify build**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Expected: no new errors

- [ ] **Step 4.5.3: Commit**

```bash
git add frontend/src/pages/Applicants.jsx
git commit -m "feat: create Applicants page with match scores, skill gap columns, and shortlist toggle"
```

---

### Task 4.6: Create frontend/src/pages/Dashboard.jsx

**Files:**
- Create: `frontend/src/pages/Dashboard.jsx`

- [ ] **Step 4.6.1: Create the file**

Create `frontend/src/pages/Dashboard.jsx` with the following complete content:

```jsx
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
    pending: '#6366f1',
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
```

- [ ] **Step 4.6.2: Verify build**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Expected: no new errors

- [ ] **Step 4.6.3: Commit**

```bash
git add frontend/src/pages/Dashboard.jsx
git commit -m "feat: create employer Dashboard page with stats, quick actions, and recent activity"
```

---

### Task 4.7: Update frontend/src/api.js with Employer Helpers

**Files:**
- Modify: `frontend/src/api.js`

- [ ] **Step 4.7.1: Add employer API functions**

Append the following exports to `frontend/src/api.js`:

```js
// frontend/src/api.js — employer helpers

export async function updateJobPost(jobId, data) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/job-posts/${jobId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return { ok: res.ok, data: await res.json() };
}

export async function deleteJobPost(jobId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/job-posts/${jobId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return { ok: res.ok, data: await res.json() };
}

export async function fetchJobApplicants(jobId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/job-posts/${jobId}/applicants`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch applicants');
  return res.json();
}

export async function updateApplicationStatus(appId, status) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/applications/${appId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ status }),
  });
  return { ok: res.ok, data: await res.json() };
}

export async function fetchEmployerDashboard() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/employer/dashboard', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
}
```

Note: `MyJobs.jsx`, `Applicants.jsx`, and `Dashboard.jsx` currently call `fetch` directly. You may optionally refactor those files to use these helpers in a follow-up pass — both approaches are equivalent.

- [ ] **Step 4.7.2: Verify build**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Expected: no new errors

- [ ] **Step 4.7.3: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat: add updateJobPost, deleteJobPost, fetchJobApplicants, updateApplicationStatus, fetchEmployerDashboard to api.js"
```

---

### Task 4.8: Update App.jsx Routing and Role-Aware Navigation

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 4.8.1: Add imports**

In `frontend/src/App.jsx`, add the following imports near the top (after existing page imports):

```jsx
import { useNavigate, useParams } from 'react-router-dom';
import MyJobs from './pages/MyJobs';
import Applicants from './pages/Applicants';
import Dashboard from './pages/Dashboard';
```

- [ ] **Step 4.8.2: Add employer routes**

Inside the logged-in `<Routes>` block, add the following routes. Pass `navigate` from `useNavigate()` as a prop to `Dashboard` and `MyJobs`. Use `useParams` inside a wrapper component (or inline) for `Applicants` to extract `jobId` from the URL.

```jsx
{/* Employer Dashboard */}
<Route
  path="/dashboard"
  element={
    <>
      <Header user={user} onLogout={handleLogout} />
      <DashboardWrapper user={user} />
    </>
  }
/>

{/* My Job Postings */}
<Route
  path="/my-jobs"
  element={
    <>
      <Header user={user} onLogout={handleLogout} />
      <MyJobsWrapper user={user} />
    </>
  }
/>

{/* Applicants for a specific job */}
<Route
  path="/jobs/:jobId/applicants"
  element={
    <>
      <Header user={user} onLogout={handleLogout} />
      <ApplicantsWrapper />
    </>
  }
/>
```

Add the three thin wrapper components just above or below the `App` default export (not inside it):

```jsx
function DashboardWrapper({ user }) {
  const navigate = useNavigate();
  return <Dashboard navigate={navigate} user={user} />;
}

function MyJobsWrapper({ user }) {
  const navigate = useNavigate();
  return <MyJobs user={user} navigate={navigate} />;
}

function ApplicantsWrapper() {
  const { jobId } = useParams();
  return <Applicants jobId={jobId} />;
}
```

- [ ] **Step 4.8.3: Update Header navigation for role-aware links**

In the Header component (either inside `App.jsx` or `frontend/src/components/Header.jsx`), update the navigation links so employees and employers see different menus:

```jsx
{/* Employee navigation */}
{user && user.role === 'employee' && (
  <>
    <Link to="/jobs">Find Jobs</Link>
    <Link to="/applications">My Applications</Link>
    <Link to="/profile">Profile</Link>
  </>
)}

{/* Employer navigation */}
{user && user.role === 'employer' && (
  <>
    <Link to="/dashboard">Dashboard</Link>
    <Link to="/my-jobs">My Jobs</Link>
    <Link to="/create-job">Post a Job</Link>
    <Link to="/profile">Profile</Link>
  </>
)}
```

- [ ] **Step 4.8.4: Redirect employers to dashboard on login**

In `App.jsx`, find the section that handles a successful login and redirect employers to `/dashboard` instead of `/jobs`:

```jsx
// After login succeeds:
if (loggedInUser.role === 'employer') {
  navigate('/dashboard');
} else {
  navigate('/jobs');
}
```

- [ ] **Step 4.8.5: Verify build and manual smoke test**

Run: `cd frontend && npm run build 2>&1 | tail -20`

Then start both servers and manually verify:
1. Log in as an employer — redirected to `/dashboard`; stats show 0 jobs, 0 applicants.
2. Navigate to `/my-jobs` — empty state with "Post Your First Job" button.
3. Create a job via `/create-job` — it appears in `/my-jobs` table.
4. Click "Edit" on a job — modal opens pre-filled; save updates the row.
5. Log in as a seeker, apply for the job.
6. Back as employer, click "Applicants" — applicant row appears with match score.
7. Click "Shortlist" — status badge updates to shortlisted.
8. Dashboard at `/dashboard` — applicant count increments, recent activity shows the new application.
9. Click "Delete" on the job — confirm dialog appears; confirm removes the job.

- [ ] **Step 4.8.6: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: add employer routes (dashboard, my-jobs, applicants) with role-aware Header nav"
```

---

### Sprint 4 Final Verification

- [ ] **Run the complete test suite**

```bash
pytest tests/ -v
```

Expected: all tests across `test_applications.py`, `test_employer.py`, and any pre-existing files PASSED, no regressions

- [ ] **Frontend production build clean**

```bash
cd frontend && npm run build
```

Expected: exits with code 0, no errors

- [ ] **Final sprint commit (if any stray changes remain)**

```bash
git add -p
git commit -m "chore: sprint 4 cleanup and final verification pass"
```
