# Education & Experience Profile Fields — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `education` and `experience` free-text fields to the User model, expose them through the profile API, show them on the job-seeker profile form, and surface them to employers via a "View Profile" modal on the Applicants page.

**Architecture:** Two `Text` columns are added to the `User` model; `PUT /api/profile` and `GET /api/job-posts/<id>/applicants` are updated to read/write them. The Profile form renders the new textareas only for job seekers. The Applicants page gains a modal that reads from the already-augmented applicants response — no new API endpoint.

**Tech Stack:** Flask 2.3 / SQLAlchemy 2.0 / pytest-flask (backend) · React 19 / Webpack 5 / plain CSS with CSS custom properties (frontend)

**Design spec:** `docs/superpowers/specs/2026-04-04-education-experience-design.md`

---

## File Map

| File | Change |
|---|---|
| `models.py` | Add `education`, `experience` columns to `User`; update `to_dict()` |
| `app.py` | `PUT /api/profile` saves new fields; `GET /api/job-posts/<id>/applicants` returns `bio`/`education`/`experience` |
| `frontend/src/Profile.jsx` | Add "Background" section heading + education/experience textareas (employee role only); init `formData` |
| `frontend/src/pages/Applicants.jsx` | Add `profileTarget` state, Escape handler, "View Profile" button, full profile modal |
| `frontend/src/pages/Applicants.css` | Modal modifier + profile header/section styles + scoped avatar style |
| `frontend/src/index.css` | `fadeIn` keyframe + animation on `.modal-overlay` (benefits all modals) |
| `tests/test_profile.py` | New file — 3 TDD tests for model columns and profile API |
| `tests/test_employer.py` | Add 1 test — applicants endpoint returns profile fields |

---

## Task 1: Backend — User model + profile API + applicants endpoint

**Files:**
- Modify: `models.py`
- Modify: `app.py`
- Create: `tests/test_profile.py`
- Modify: `tests/test_employer.py`

### Context

**Token format:** `token_{email}_{timestamp}`. Email is extracted via `'_'.join(parts[1:-1])`.

**Test fixtures** (already in `tests/conftest.py`):
- `app` — Flask app with SQLite in-memory DB, tables created fresh per test
- `client` — Flask test client
- `seeker_token` — token for user `seeker@t.com` (role: `employee`)
- `employer_token` — token for user `emp@t.com` (role: `employer`)
- `sample_job` — job post created by employer, returns `{"id": ..., "position": "Python Dev", ...}`

**Current `User.to_dict()`** returns: `id`, `email`, `name`, `phone`, `location`, `bio`, `skills`, `role`.

**Current `PUT /api/profile`** field-update block (around line 348 in `app.py`):
```python
user.name = data.get('name', user.name)
user.phone = data.get('phone', user.phone)
user.location = data.get('location', user.location)
user.bio = data.get('bio', user.bio)
user.skills = data.get('skills', user.skills)
```

**Current `result.append({...})` in `get_job_applicants`** (around line 863 in `app.py`):
```python
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
```

---

- [ ] **Step 1: Create `tests/test_profile.py` with 3 failing tests**

```python
# tests/test_profile.py
import pytest


def test_user_has_education_experience_fields(app):
    """User model must have education and experience columns."""
    from models import User
    with app.app_context():
        cols = [c.name for c in User.__table__.columns]
        assert 'education' in cols
        assert 'experience' in cols


def test_profile_update_saves_education_experience(client, seeker_token):
    """PUT /api/profile persists education and experience."""
    res = client.put('/api/profile', json={
        'education': 'B.Eng Computer Engineering, KMITL 2024',
        'experience': '1 year intern at TechCorp',
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['user']['education'] == 'B.Eng Computer Engineering, KMITL 2024'
    assert data['user']['experience'] == '1 year intern at TechCorp'


def test_profile_get_returns_education_experience(client, seeker_token):
    """GET /api/profile returns education and experience after save."""
    client.put('/api/profile', json={
        'education': 'Masters in AI',
        'experience': '3 years at StartupX',
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    res = client.get('/api/profile', headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    user = res.get_json()['user']
    assert user['education'] == 'Masters in AI'
    assert user['experience'] == '3 years at StartupX'
```

- [ ] **Step 2: Run tests — confirm all 3 FAIL**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/test_profile.py -v 2>&1
```

Expected output: 3 FAILED. `test_user_has_education_experience_fields` fails with `AssertionError` (column not found). The other two fail because `to_dict()` doesn't include the keys.

- [ ] **Step 3: Add `education` and `experience` columns to `User` in `models.py`**

Find the `bio` column declaration in `models.py` (line 19):
```python
bio = db.Column(db.Text, default='')
```

Add two lines directly after it:
```python
bio = db.Column(db.Text, default='')
education = db.Column(db.Text, default='')
experience = db.Column(db.Text, default='')
```

- [ ] **Step 4: Update `User.to_dict()` in `models.py`**

Find the `to_dict` method (around line 36). Replace the return dict:

```python
def to_dict(self):
    """Convert user to dictionary for JSON serialization."""
    return {
        'id': self.id,
        'email': self.email,
        'name': self.name,
        'phone': self.phone,
        'location': self.location,
        'bio': self.bio,
        'education': self.education or '',
        'experience': self.experience or '',
        'skills': self.skills,
        'role': self.role
    }
```

- [ ] **Step 5: Update `PUT /api/profile` in `app.py` to save the new fields**

Find the field-update block inside `update_profile()` (around line 348). After `user.bio = data.get('bio', user.bio)`, add:

```python
user.name = data.get('name', user.name)
user.phone = data.get('phone', user.phone)
user.location = data.get('location', user.location)
user.bio = data.get('bio', user.bio)
user.education = data.get('education', user.education)
user.experience = data.get('experience', user.experience)
user.skills = data.get('skills', user.skills)
```

- [ ] **Step 6: Run profile tests — confirm all 3 PASS**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/test_profile.py -v 2>&1
```

Expected: 3 passed.

- [ ] **Step 7: Add the applicants endpoint test to `tests/test_employer.py`**

Open `tests/test_employer.py` and append at the end of the file:

```python
def test_applicants_response_includes_profile_fields(client, employer_token, seeker_token, sample_job):
    """GET /api/job-posts/<id>/applicants returns bio, education, experience per applicant."""
    # Seeker applies for the job
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {seeker_token}'})
    # Employer views applicants
    res = client.get(f'/api/job-posts/{sample_job["id"]}/applicants',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    applicant = data[0]
    assert 'bio' in applicant
    assert 'education' in applicant
    assert 'experience' in applicant
```

- [ ] **Step 8: Run the new employer test — confirm it FAILS**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/test_employer.py::test_applicants_response_includes_profile_fields -v 2>&1
```

Expected: FAILED — `KeyError: 'bio'` or `AssertionError`.

- [ ] **Step 9: Update `get_job_applicants` in `app.py` to include profile fields**

Find `result.append({...})` inside `get_job_applicants` (around line 863). Replace it with:

```python
result.append({
    'application_id': a.id,
    'status': a.status,
    'applied_at': a.created_at.isoformat(),
    'user_id': applicant.id,
    'name': applicant.name,
    'email': applicant.email,
    'skills': applicant.skills,
    'bio': applicant.bio or '',
    'education': applicant.education or '',
    'experience': applicant.experience or '',
    'match_score': score,
    'matched_skills': matched,
    'missing_skills': missing,
})
```

- [ ] **Step 10: Run the employer test — confirm it PASSES**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/test_employer.py::test_applicants_response_includes_profile_fields -v 2>&1
```

Expected: PASSED.

- [ ] **Step 11: Run the full test suite — no regressions**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: all existing tests pass + 4 new tests pass (3 profile + 1 employer).

- [ ] **Step 12: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add models.py app.py tests/test_profile.py tests/test_employer.py && git commit -m "feat: add education and experience fields to User model and profile API"
```

---

## Task 2: Profile form — education/experience textareas

**Files:**
- Modify: `frontend/src/Profile.jsx`

### Context

`Profile.jsx` is at `frontend/src/Profile.jsx` (not inside `pages/`). It receives a `user` prop with the full user object from `App.jsx`.

**Current `formData` state initialisation** (lines 6–13):
```js
const [formData, setFormData] = useState({
  name: user?.name || '',
  email: user?.email || '',
  phone: user?.phone || '',
  location: user?.location || '',
  bio: user?.bio || '',
  profilePicture: user?.profilePicture || '',
});
```

**Current bio textarea** (lines 153–163):
```jsx
<div className="form-group full-width">
  <label htmlFor="bio">Bio</label>
  <textarea
    id="bio"
    name="bio"
    value={formData.bio}
    onChange={handleInputChange}
    placeholder="Tell us about yourself"
    rows="4"
  />
</div>
```

**Immediately after the bio div** is the skills section (line 165):
```jsx
<div className="form-group full-width">
  <div className="skills-section">
    <h4>Skills</h4>
```

The existing `handleInputChange` reads `e.target.name` and updates `formData` — it already handles any new `name` attribute without modification.

The "Background" `<h4>` uses className `skills-section` which is defined in `Profile.css` (line 98–99):
```css
.skills-section { margin-top: 20px; }
.skills-section h4 { font-size: 13px; font-weight: 700; margin-bottom: 10px; color: var(--color-muted); text-transform: uppercase; letter-spacing: 0.5px; }
```

---

- [ ] **Step 1: Add `education` and `experience` to `formData` state initialisation**

Replace the existing `useState` call (lines 6–13 of `Profile.jsx`):

```js
const [formData, setFormData] = useState({
  name: user?.name || '',
  email: user?.email || '',
  phone: user?.phone || '',
  location: user?.location || '',
  bio: user?.bio || '',
  profilePicture: user?.profilePicture || '',
  education: user?.education || '',
  experience: user?.experience || '',
});
```

- [ ] **Step 2: Insert the Background section after the bio textarea**

Find the closing `</div>` of the bio form-group (the one wrapping the bio `<textarea>`). After it, insert:

```jsx
{user?.role === 'employee' && (
  <>
    <div className="form-group full-width">
      <div className="skills-section">
        <h4>Background</h4>
      </div>
    </div>
    <div className="form-group full-width">
      <label htmlFor="education">Education</label>
      <textarea
        id="education"
        name="education"
        value={formData.education}
        onChange={handleInputChange}
        placeholder={"e.g.\nB.Eng Computer Engineering, KMITL (2024)\nHigh School Diploma, Bangkok (2020)"}
        rows="3"
      />
    </div>
    <div className="form-group full-width">
      <label htmlFor="experience">Experience</label>
      <textarea
        id="experience"
        name="experience"
        value={formData.experience}
        onChange={handleInputChange}
        placeholder={"e.g.\n1 year internship at TechCorp as Backend Developer (2023–2024)\nFreelance web development (2022–2023)"}
        rows="3"
      />
    </div>
  </>
)}
```

- [ ] **Step 3: Verify the frontend builds without errors**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -15
```

Expected: `successfully compiled` or webpack output with no errors. If there is an error, read the full error and fix it before continuing.

- [ ] **Step 4: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add frontend/src/Profile.jsx && git commit -m "feat: add education and experience fields to profile form (employee only)"
```

---

## Task 3: View Profile modal — Applicants page

**Files:**
- Modify: `frontend/src/pages/Applicants.jsx`
- Modify: `frontend/src/pages/Applicants.css`
- Modify: `frontend/src/index.css`

### Context

**Top of `Applicants.jsx`** already has:
```js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Applicants.css';
```

**Constants already defined** at the top of the file (used inside the modal):
```js
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
```

**Inside `Applicants({ jobId })`**, current state declarations:
```js
const [applicants, setApplicants] = useState([]);
const [loading, setLoading] = useState(true);
const [filter, setFilter] = useState('all');
const [message, setMessage] = useState('');
const navigate = useNavigate();
```

**Current Actions `<td>`** (lines 165–193) has Shortlist/Unshortlist and Message buttons.

**Global CSS classes available** (from `index.css`): `.modal-overlay`, `.modal`, `.modal-close`, `.score-badge`, `.skill-tag`, `.skill-tag.matched`, `.skill-tag.missing`, `.skill-tags`, `.status-chip`, `.muted`.

**`profile-avatar-large`** is in `Profile.css` (not global). The plan scopes a slightly smaller (56px) version inside `.applicant-profile-modal` in `Applicants.css` to avoid a cross-file dependency. `.profile-role-badge` is also in `Profile.css` but since Webpack bundles all CSS statically, it is available globally once built. No duplication needed.

---

- [ ] **Step 1: Add `profileTarget` state inside `Applicants()`**

Find the line `const navigate = useNavigate();` and add one line after it:

```js
const navigate = useNavigate();
const [profileTarget, setProfileTarget] = useState(null);
```

- [ ] **Step 2: Add the Escape key `useEffect`**

Add after the existing `useEffect(() => { if (jobId) loadApplicants(); }, [jobId]);` block:

```js
useEffect(() => {
  if (!profileTarget) return;
  const handler = (e) => { if (e.key === 'Escape') setProfileTarget(null); };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [profileTarget]);
```

- [ ] **Step 3: Add the "View Profile" button to each row's Actions `<td>`**

Find the Actions `<td>` which currently ends with:

```jsx
  {' '}
  <button
    className="btn-sm"
    onClick={() => navigate(`/messages?partner=${a.user_id}`)}
  >
    Message
  </button>
</td>
```

Add the View Profile button after the Message button, before `</td>`:

```jsx
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
```

- [ ] **Step 4: Add the View Profile modal at the bottom of the return**

Find the closing `</div>` at the very end of the `return (...)` statement (the one that closes `<div className="applicants-page">`). Insert the modal just before it:

```jsx
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
                {profileTarget.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()}
              </div>
              <div className="applicant-profile-header-info">
                <h3 id="applicant-profile-title" className="applicant-profile-name">
                  {profileTarget.name}
                </h3>
                <p className="applicant-profile-email">{profileTarget.email}</p>
                <div className="applicant-profile-meta">
                  <span className="profile-role-badge">job seeker</span>
                  <span
                    className="status-chip"
                    style={{ background: STATUS_COLORS[profileTarget.status] || '#6b7280' }}
                  >
                    {profileTarget.status}
                  </span>
                  <span className="muted">
                    Applied {new Date(profileTarget.applied_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Match score */}
            <div className="applicant-profile-section">
              <h4>Match Score</h4>
              <span
                className="score-badge"
                style={{ background: SCORE_COLOR(profileTarget.match_score) }}
              >
                {profileTarget.match_score}% match
              </span>
            </div>

            {/* Matched skills */}
            {profileTarget.matched_skills.length > 0 && (
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
            {profileTarget.missing_skills.length > 0 && (
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
```

- [ ] **Step 5: Add modal styles to `Applicants.css`**

Append to the end of `frontend/src/pages/Applicants.css`:

```css
/* View Profile modal */
.applicant-profile-modal { max-width: 520px; }

.applicant-profile-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 4px;
}

.applicant-profile-header-info { flex: 1; min-width: 0; }

.applicant-profile-name {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 2px 0;
  padding-right: 32px;
}

.applicant-profile-email {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0 0 8px 0;
}

.applicant-profile-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.applicant-profile-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.applicant-profile-section h4 {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-muted);
  margin: 0 0 8px 0;
}

.applicant-profile-section p {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
  margin: 0;
  white-space: pre-wrap;
}

/* Scoped avatar for the modal — profile-avatar-large is defined in Profile.css
   but at 64px; this overrides to 56px for the more compact modal header */
.applicant-profile-modal .profile-avatar-large {
  width: 56px;
  height: 56px;
  font-size: 20px;
}
```

- [ ] **Step 6: Add fade-in animation to `index.css`**

Open `frontend/src/index.css`. Find the `/* Modal */` comment block (around line 44). The existing `.modal-overlay` rule is:
```css
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
```

Add the keyframe above it and append `animation` to `.modal-overlay`:

```css
/* Modal */
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; animation: fadeIn 0.15s ease; }
.modal { background: #fff; border-radius: var(--radius); padding: 32px; max-width: 600px; width: 90%; max-height: 85vh; overflow-y: auto; position: relative; box-shadow: var(--shadow-md); }
.modal-close { position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 18px; cursor: pointer; color: var(--color-muted); }
```

- [ ] **Step 7: Verify the frontend builds without errors**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -15
```

Expected: `successfully compiled` with no errors. If there is a JSX syntax error, the output will show the file and line number — read it and fix it.

- [ ] **Step 8: Run the full backend test suite — confirm no regressions**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add frontend/src/pages/Applicants.jsx frontend/src/pages/Applicants.css frontend/src/index.css && git commit -m "feat: add View Profile modal to Applicants page with education/experience display"
```
