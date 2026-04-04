# Sprint 8: Profile Gaps — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the two functional requirements from the PDF that are currently missing: (1) education and experience fields in the user profile, and (2) a "View Profile" modal on the Applicants page so employers can see full candidate details.

**Architecture:** Task 8.1 adds `education` (Text) and `experience` (Text) columns to the `User` model, updates the profile API and frontend form, and adds basic extraction to the resume parser. Task 8.2 adds a profile modal to the Applicants page using data already returned by the applicants endpoint (augmented with `bio`, `education`, `experience`).

**Tech Stack:** Flask / SQLAlchemy / React 19

---

## File Map

| File | Change |
|---|---|
| `models.py` | Add `education` and `experience` columns to `User`; update `to_dict()` |
| `app.py` | Update `PUT /api/profile` to accept `education`/`experience`; update `GET /api/job-posts/<id>/applicants` to include `bio`, `education`, `experience` in response |
| `frontend/src/Profile.jsx` | Add education textarea and experience textarea to form |
| `frontend/src/pages/Applicants.jsx` | Add "View Profile" button + modal showing candidate details |
| `tests/test_messaging.py` → no change | |
| `tests/test_auth.py` → no change | |
| New test additions go into `tests/test_profile.py` (new file) | |

---

## Task 8.1: Add education and experience fields to User model and profile

**Files:**
- Modify: `models.py`
- Modify: `app.py` (PUT /api/profile, GET /api/job-posts/<id>/applicants)
- Modify: `frontend/src/Profile.jsx`
- Create: `tests/test_profile.py`

### Context

**Current User model columns** (from models.py):
`id`, `email`, `password`, `name`, `phone`, `location`, `bio`, `skills`, `role`, `created_at`, `updated_at`

**Current `to_dict()` returns:**
`id`, `email`, `name`, `phone`, `location`, `bio`, `skills`, `role`

**Current `PUT /api/profile`** accepts: `name`, `phone`, `location`, `bio`, `skills`

**Current Profile.jsx form fields:** name, email (disabled), phone, location, bio, skills tag-builder

The tests use SQLite in-memory via conftest.py (`os.environ['DB_URI'] = 'sqlite:///:memory:'`).

---

- [ ] **Step 1: Write failing tests first**

Create `tests/test_profile.py`:

```python
import pytest


def test_user_has_education_field(app):
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
    # First set them
    client.put('/api/profile', json={
        'education': 'Masters in AI',
        'experience': '3 years at StartupX',
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    # Then retrieve
    res = client.get('/api/profile', headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    user = res.get_json()['user']
    assert user['education'] == 'Masters in AI'
    assert user['experience'] == '3 years at StartupX'
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/test_profile.py -v 2>&1
```

Expected: all 3 FAIL (columns not found, 200 but keys missing).

- [ ] **Step 3: Add `education` and `experience` columns to User model**

In `models.py`, find the User model's column declarations. After the `bio` column:
```python
bio = db.Column(db.Text, default='')
```

Add:
```python
education = db.Column(db.Text, default='')
experience = db.Column(db.Text, default='')
```

- [ ] **Step 4: Update `User.to_dict()` to include the new fields**

In `models.py`, find `User.to_dict()`. It currently returns:
```python
return {
    'id': self.id,
    'email': self.email,
    'name': self.name,
    'phone': self.phone,
    'location': self.location,
    'bio': self.bio,
    'skills': self.skills,
    'role': self.role
}
```

Add `education` and `experience`:
```python
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

- [ ] **Step 5: Update `PUT /api/profile` in app.py to accept the new fields**

Find the `PUT /api/profile` endpoint in `app.py`. It currently updates `name`, `phone`, `location`, `bio`, `skills`. Add the two new fields.

Find the block that sets fields from data (will look like):
```python
user.name = data.get('name', user.name)
user.phone = data.get('phone', user.phone)
user.location = data.get('location', user.location)
user.bio = data.get('bio', user.bio)
```

Add after `user.bio`:
```python
user.education = data.get('education', user.education)
user.experience = data.get('experience', user.experience)
```

- [ ] **Step 6: Run profile tests — expect PASS**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/test_profile.py -v 2>&1
```

Expected: all 3 PASS.

- [ ] **Step 7: Run full test suite — no regressions**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: 72 passed (69 existing + 3 new).

- [ ] **Step 8: Update Profile.jsx — add education and experience textareas**

Read `frontend/src/Profile.jsx` to find exactly where `bio` textarea is rendered. After the `bio` textarea section, add two new textareas.

The bio section currently looks like:
```jsx
<div className="form-group">
  <label>Bio</label>
  <textarea
    rows="4"
    value={formData.bio}
    onChange={e => setFormData({ ...formData, bio: e.target.value })}
    placeholder="Tell employers about yourself..."
  />
</div>
```

Add after it:
```jsx
<div className="form-group">
  <label>Education</label>
  <textarea
    rows="3"
    value={formData.education || ''}
    onChange={e => setFormData({ ...formData, education: e.target.value })}
    placeholder="e.g. B.Eng Computer Engineering, KMITL (2024)"
  />
</div>

<div className="form-group">
  <label>Experience</label>
  <textarea
    rows="3"
    value={formData.experience || ''}
    onChange={e => setFormData({ ...formData, experience: e.target.value })}
    placeholder="e.g. 1 year internship at TechCorp as Backend Developer"
  />
</div>
```

Also ensure `formData` state initialisation includes `education` and `experience`. Find where `formData` is initialised (will look like `useState({ name: '', phone: '', ... })`). Add:
```js
education: user?.education || '',
experience: user?.experience || '',
```

- [ ] **Step 9: Verify frontend build**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -20
```

Expected: no errors.

- [ ] **Step 10: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add models.py app.py frontend/src/Profile.jsx tests/test_profile.py && git commit -m "feat: add education and experience fields to user profile (sprint 8)"
```

---

## Task 8.2: View Profile modal in Applicants page

**Files:**
- Modify: `app.py` (GET /api/job-posts/<id>/applicants — add bio/education/experience to response)
- Modify: `frontend/src/pages/Applicants.jsx` (add View Profile button + modal)
- Modify: `frontend/src/pages/Applicants.css` (modal styles)
- Modify: `tests/test_employer.py` (update existing applicants test to include new fields)

### Context

**Current `GET /api/job-posts/<id>/applicants` response per applicant:**
```json
{
  "application_id": 1,
  "status": "pending",
  "applied_at": "2026-04-04T...",
  "user_id": 2,
  "name": "Seeker",
  "email": "seeker@t.com",
  "skills": "Python,Flask",
  "match_score": 70,
  "matched_skills": ["python"],
  "missing_skills": ["flask"]
}
```

We need to also return `bio`, `education`, `experience` so the modal can display them without a second API call.

**Current Applicants.jsx actions column** has: Shortlist/Unshortlist button + Message button. We add a "View Profile" button that opens a modal.

---

- [ ] **Step 1: Write failing test first**

In `tests/test_employer.py`, add a new test at the end:

```python
def test_applicants_response_includes_profile_fields(client, employer_token, seeker_token, sample_job):
    """Applicant response includes bio, education, experience."""
    # Seeker applies
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

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/test_employer.py::test_applicants_response_includes_profile_fields -v 2>&1
```

Expected: FAIL — `bio` key not in applicant dict.

- [ ] **Step 3: Update GET /api/job-posts/<id>/applicants in app.py**

In `app.py`, find `get_job_applicants`. The `result.append({...})` block currently has these keys: `application_id`, `status`, `applied_at`, `user_id`, `name`, `email`, `skills`, `match_score`, `matched_skills`, `missing_skills`.

Add three fields to the dict:
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

- [ ] **Step 4: Run the new test — expect PASS**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/test_employer.py::test_applicants_response_includes_profile_fields -v 2>&1
```

Expected: PASS.

- [ ] **Step 5: Run full test suite**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: 73 passed.

- [ ] **Step 6: Add the View Profile modal to Applicants.jsx**

Read `frontend/src/pages/Applicants.jsx` to understand the current structure.

Add `profileTarget` state (the applicant object to show, or null):
```js
const [profileTarget, setProfileTarget] = useState(null);
```

Add the View Profile button to the Actions cell — after the Message button:
```jsx
{' '}
<button
  className="btn-sm"
  onClick={() => setProfileTarget(a)}
>
  View Profile
</button>
```

Add the profile modal at the bottom of the return, just before the closing `</div>`:
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
      >×</button>

      <h3 id="applicant-profile-title" className="applicant-profile-name">
        {profileTarget.name}
      </h3>
      <p className="applicant-profile-email">{profileTarget.email}</p>

      <div className="applicant-profile-score">
        <span
          className="score-badge"
          style={{ background: SCORE_COLOR(profileTarget.match_score) }}
        >
          {profileTarget.match_score}% match
        </span>
      </div>

      {profileTarget.bio && (
        <div className="applicant-profile-section">
          <h4>About</h4>
          <p>{profileTarget.bio}</p>
        </div>
      )}

      {profileTarget.education && (
        <div className="applicant-profile-section">
          <h4>Education</h4>
          <p>{profileTarget.education}</p>
        </div>
      )}

      {profileTarget.experience && (
        <div className="applicant-profile-section">
          <h4>Experience</h4>
          <p>{profileTarget.experience}</p>
        </div>
      )}

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
    </div>
  </div>
)}
```

- [ ] **Step 7: Add modal styles to Applicants.css**

Read `frontend/src/pages/Applicants.css` to find the end of the file, then append:

```css
.applicant-profile-modal {
  max-width: 520px;
  width: 90%;
  position: relative;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-close {
  position: absolute;
  top: 12px;
  right: 16px;
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  color: var(--color-muted);
  line-height: 1;
}

.applicant-profile-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 4px 0;
  padding-right: 32px;
}

.applicant-profile-email {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0 0 12px 0;
}

.applicant-profile-score {
  margin-bottom: 16px;
}

.applicant-profile-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.applicant-profile-section h4 {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-muted);
  margin: 0 0 8px 0;
}

.applicant-profile-section p {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
  margin: 0;
}
```

- [ ] **Step 8: Verify frontend build**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -20
```

Expected: no errors.

- [ ] **Step 9: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add app.py frontend/src/pages/Applicants.jsx frontend/src/pages/Applicants.css tests/test_employer.py && git commit -m "feat: add View Profile modal to Applicants page (sprint 8)"
```
