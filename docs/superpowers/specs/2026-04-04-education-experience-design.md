# Education & Experience Profile Fields — Design Spec

**Date:** 2026-04-04
**Status:** Approved

---

## Goal

Add `education` and `experience` as free-text profile fields for job seekers, expose them through the profile API, and surface them to employers via a "View Profile" modal on the Applicants page.

---

## Background

The PDF requirements specify: "The system shall allow job seekers to manually enter personal information, including skills, education, experience, and job preferences." Currently the `User` model has `bio` and `skills` but no `education` or `experience` columns. Employers viewing applicants have no way to see candidate background detail.

---

## Decisions

| Question | Decision | Rationale |
|---|---|---|
| Data shape | Free text (`Text` columns) | Consistent with `bio`/`skills` pattern; spec doesn't require structured parsing or matching |
| Profile display | Job seekers only | Education/experience are candidate-facing resume data |
| Employer access | Via augmented applicants endpoint | No extra network call; data bundled with existing response |
| Employer UI | Modal overlay (not a page) | Consistent with `JobModal` pattern; employer stays in context |

---

## Data Model

Add two columns to `User` in `models.py`, after `bio`:

```python
education = db.Column(db.Text, default='')
experience = db.Column(db.Text, default='')
```

Update `User.to_dict()` to include both fields:

```python
'education': self.education or '',
'experience': self.experience or '',
```

No migration script required — development uses `init_db.py` to recreate tables; tests use SQLite in-memory.

---

## Backend API

### `PUT /api/profile`

Add to the field-update block (after `user.bio = ...`):

```python
user.education = data.get('education', user.education)
user.experience = data.get('experience', user.experience)
```

Response already calls `user.to_dict()` — no further changes needed.

### `GET /api/job-posts/<id>/applicants`

Add three keys to the `result.append({...})` dict:

```python
'bio': applicant.bio or '',
'education': applicant.education or '',
'experience': applicant.experience or '',
```

No auth changes — endpoint is already employer-only via `@require_role('employer')`.

---

## Frontend — Profile Form (`Profile.jsx`)

### State

Add to `formData` initialisation:

```js
education: user?.education || '',
experience: user?.experience || '',
```

The existing `handleInputChange` handler uses `e.target.name` and already handles new fields — no changes needed.

### Rendering

Render only when `user.role === 'employee'`, placed after the `bio` textarea and before the skills section:

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

The "Background" `<h4>` reuses `.skills-section h4` from `Profile.css` (uppercase, muted, letter-spaced) — zero new CSS.

---

## Frontend — View Profile Modal (`Applicants.jsx`)

### State

```js
const [profileTarget, setProfileTarget] = useState(null);
```

### Button

Added to each row's Actions `<td>`, after the Message button:

```jsx
{' '}
<button className="btn-sm" onClick={() => setProfileTarget(a)}>
  View Profile
</button>
```

### Escape key handler

```jsx
useEffect(() => {
  if (!profileTarget) return;
  const handler = (e) => { if (e.key === 'Escape') setProfileTarget(null); };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [profileTarget]);
```

### Modal

Rendered at the bottom of the return before the closing `</div>`:

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
      <button className="modal-close" onClick={() => setProfileTarget(null)} aria-label="Close">✕</button>

      {/* Header — mirrors Profile page header card */}
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
        <span className="score-badge" style={{ background: SCORE_COLOR(profileTarget.match_score) }}>
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
```

### CSS additions

**`index.css`** — append (benefits all modals):
```css
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-overlay { animation: fadeIn 0.15s ease; }
```

**`Applicants.css`** — append:
```css
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
```

Note: `.status-chip`, `.score-badge`, `.skill-tag`, `.skill-tags`, `.muted` are global classes in `index.css` — no new CSS needed for them.

`.profile-avatar-large` and `.profile-role-badge` are defined in `Profile.css` (not global). Add these to `Applicants.css` to avoid a cross-file CSS dependency:

```css
/* Reused from Profile.css — needed for modal avatar */
.applicant-profile-modal .profile-avatar-large {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-primary-light);
  color: var(--color-primary-dark);
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
```

`.profile-role-badge` is already defined as `.profile-role-badge` in `Profile.css` but since the badge is purely cosmetic and uses only global CSS variables, it will render correctly as long as `Profile.css` is loaded anywhere in the app (it is — via the `/profile` route). No duplication needed.

---

## Testing

### `tests/test_profile.py` (new file)

```python
def test_user_has_education_experience_fields(app):
    from models import User
    with app.app_context():
        cols = [c.name for c in User.__table__.columns]
        assert 'education' in cols
        assert 'experience' in cols


def test_profile_update_saves_education_experience(client, seeker_token):
    res = client.put('/api/profile', json={
        'education': 'B.Eng Computer Engineering, KMITL 2024',
        'experience': '1 year intern at TechCorp',
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['user']['education'] == 'B.Eng Computer Engineering, KMITL 2024'
    assert data['user']['experience'] == '1 year intern at TechCorp'


def test_profile_get_returns_education_experience(client, seeker_token):
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

### `tests/test_employer.py` (add one test)

```python
def test_applicants_response_includes_profile_fields(client, employer_token, seeker_token, sample_job):
    """Applicant response includes bio, education, experience."""
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {seeker_token}'})
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

---

## File Change Summary

| File | Change |
|---|---|
| `models.py` | Add `education`, `experience` columns; update `to_dict()` |
| `app.py` | `PUT /api/profile` accepts new fields; `GET /api/job-posts/<id>/applicants` returns them |
| `frontend/src/Profile.jsx` | Add "Background" section heading + education/experience textareas (employee only); init `formData` |
| `frontend/src/pages/Applicants.jsx` | Add `profileTarget` state, Escape handler, "View Profile" button, modal |
| `frontend/src/pages/Applicants.css` | Add modal modifier + profile content styles |
| `frontend/src/index.css` | Add `fadeIn` keyframe + animation on `.modal-overlay` |
| `tests/test_profile.py` | New file — 3 tests |
| `tests/test_employer.py` | Add 1 test |
