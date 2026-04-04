# PDF Resume Upload — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PDF file upload to the Profile "Import from Resume" section so users can upload a PDF alongside the existing text-paste option, with the same extraction pipeline.

**Architecture:** The backend `/api/upload-resume` endpoint already exists (`app.py:536-603`) and accepts PDF files via multipart form data, extracting text with PyMuPDF. What's missing: (1) the frontend has no `uploadResumePdf()` API function, (2) the Profile.jsx has no file upload UI, and (3) the backend upload endpoint is missing the `extract_experience()` call added in the recent parsing fix. This plan adds the frontend upload UI with drag-and-drop support, creates the API function, and fixes the backend parity gap.

**Tech Stack:** React 19 (frontend), Flask/PyMuPDF (backend, already implemented), CSS

---

## Current State

| Layer | Text Paste | PDF Upload |
|-------|-----------|------------|
| Backend endpoint | `/api/parse-resume-text` | `/api/upload-resume` (exists) |
| Backend experience extraction | Yes | **No** (missing) |
| `api.js` function | `parseResumeText()` | **Missing** |
| `Profile.jsx` UI | Textarea + button | **Missing** |
| CSS | Exists | **Missing** |
| Tests | 12 profile tests | **No upload tests** |

## Files Modified

| File | Change |
|------|--------|
| `app.py:536-603` | Add `extract_experience()` call + `experience` in response |
| `frontend/src/api.js` | Add `uploadResumePdf()` function |
| `frontend/src/Profile.jsx` | Add file upload UI with drag-and-drop |
| `frontend/src/Profile.css` | Add upload dropzone styles |
| `tests/test_profile.py` | Add PDF upload backend tests |

---

### Task 1: Fix Backend Upload Endpoint Parity — Add Experience Extraction

**Problem:** The `/api/upload-resume` endpoint is missing `extract_experience()` (which was added to `/api/parse-resume-text` in the recent fix). The response also lacks `"experience"` in `resume_data`.

**Files:**
- Modify: `app.py:536-603`
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Write failing test for PDF upload experience extraction**

Add to `tests/test_profile.py`:

```python
def test_upload_resume_extracts_experience(client, seeker_token):
    """PDF upload endpoint should also extract experience like the text endpoint."""
    import io
    # Create a minimal PDF with PyMuPDF (fitz)
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    text = """John Smith
john@example.com
+1-555-123-4567

Education:
Bachelor of Science, KMITL (2024)

Experience:
Software Engineer at Google (2022-2024)
Intern at TechCorp (Summer 2019)

Skills: Python, JavaScript, React"""
    page.insert_text((72, 72), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    data = {'resume': (io.BytesIO(pdf_bytes), 'resume.pdf')}
    res = client.post('/api/upload-resume',
                      data=data,
                      content_type='multipart/form-data',
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    result = res.get_json()
    assert 'experience' in result['resume_data'], "resume_data should include experience key"
    assert len(result['resume_data']['experience']) >= 1, \
        f"Should extract experience, got: {result['resume_data'].get('experience')}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_upload_resume_extracts_experience -v`

Expected: FAIL — `'experience'` not in `resume_data`.

- [ ] **Step 3: Add experience extraction to upload endpoint**

In `app.py`, in the `upload_resume()` function (around line 561, after `extracted_education = extract_education(pdf_text)`), add:

```python
        extracted_experience = extract_experience(pdf_text)
```

Then after the education auto-populate block, add:

```python
        if extracted_experience and not user.experience.strip():
            user.experience = '\n'.join(extracted_experience)
            fields_populated += 1
```

And update the response `resume_data` dict to include experience:

```python
            "resume_data": {
                "name": extracted_name,
                "email": extracted_email,
                "phone": extracted_phone,
                "skills": extracted_skills,
                "education": extracted_education,
                "experience": extracted_experience
            },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_upload_resume_extracts_experience -v`

Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v 2>&1 | tail -10`

Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_profile.py
git commit -m "fix: add experience extraction to PDF upload endpoint

The /api/upload-resume endpoint was missing extract_experience() and
the experience key in resume_data. Now has parity with the text
parse endpoint."
```

---

### Task 2: Add `uploadResumePdf()` to `api.js`

**Problem:** No frontend API function exists to call `/api/upload-resume`.

**Files:**
- Modify: `frontend/src/api.js`

- [ ] **Step 1: Add the function**

In `frontend/src/api.js`, add this function right after the existing `parseResumeText()` function (around line 207):

```javascript
export async function uploadResumePdf(file) {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('resume', file);
  const res = await fetch('/api/upload-resume', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });
  handleAuthError(res);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.message || 'Failed to upload resume');
  }
  return res.json();
}
```

Note: No `Content-Type` header — the browser sets `multipart/form-data` with the correct boundary automatically when using `FormData`.

- [ ] **Step 2: Verify frontend build**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx webpack --mode development 2>&1 | tail -3`

Expected: `compiled successfully`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat: add uploadResumePdf() API function

Sends PDF file as multipart/form-data to /api/upload-resume.
Returns same structure as parseResumeText()."
```

---

### Task 3: Add PDF Upload UI to Profile.jsx

**Problem:** The Profile page only has a textarea for pasting resume text. Need to add a file upload option alongside it.

**Files:**
- Modify: `frontend/src/Profile.jsx`
- Modify: `frontend/src/Profile.css`

- [ ] **Step 1: Add import and state for file upload**

In `Profile.jsx` line 3, update the import to include `uploadResumePdf`:

```javascript
import { updateProfile, parseResumeText, uploadResumePdf } from './api';
```

After the existing `resumeLoading` state (around line 30), add:

```javascript
  const [resumeFile, setResumeFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
```

- [ ] **Step 2: Add the file upload handler**

Add this function after the existing `handleParseResume` function (after line 109):

```javascript
  const handleFileUpload = async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('File must be smaller than 5MB');
      return;
    }
    setResumeFile(file);
    setResumeLoading(true);
    setError('');
    setSuccess('');
    try {
      const data = await uploadResumePdf(file);
      const updatedUser = data.user;
      setFormData({
        name: updatedUser.name || '',
        email: updatedUser.email || '',
        phone: updatedUser.phone || '',
        location: updatedUser.location || '',
        bio: updatedUser.bio || '',
        profilePicture: updatedUser.profilePicture || '',
        education: updatedUser.education || '',
        experience: updatedUser.experience || '',
      });
      if (updatedUser.skills) {
        setSkills(updatedUser.skills.split(',').map(s => s.trim()).filter(Boolean));
      }
      localStorage.setItem('user', JSON.stringify(updatedUser));
      onUpdateProfile(updatedUser);
      const populated = data.fields_populated || 0;
      setSuccess(`PDF parsed! ${data.extracted_skills.length} skills found.${populated > 0 ? ` ${populated} profile field(s) auto-populated.` : ''}`);
    } catch (err) {
      setError(err.message || 'Failed to parse PDF. Please try again.');
    } finally {
      setResumeLoading(false);
      setResumeFile(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };
```

- [ ] **Step 3: Replace the "Import from Resume" UI section**

In `Profile.jsx`, find the "Import from Resume" section (lines 224-244). Replace the entire block:

```jsx
            {user?.role === 'employee' && (
              <div className="form-group full-width">
                <div className="skills-section">
                  <h4>Import from Resume</h4>
                  <textarea
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    placeholder="Paste your resume text here to auto-populate skills and profile fields…"
                    rows="5"
                  />
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={handleParseResume}
                    disabled={resumeLoading || !resumeText.trim()}
                  >
                    {resumeLoading ? 'Parsing…' : 'Parse Resume'}
                  </button>
                </div>
              </div>
            )}
```

with:

```jsx
            {user?.role === 'employee' && (
              <div className="form-group full-width">
                <div className="skills-section">
                  <h4>Import from Resume</h4>

                  <div
                    className={`resume-dropzone${dragActive ? ' drag-active' : ''}`}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onClick={() => document.getElementById('resume-file-input').click()}
                  >
                    <input
                      id="resume-file-input"
                      type="file"
                      accept=".pdf"
                      style={{ display: 'none' }}
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) handleFileUpload(file);
                        e.target.value = '';
                      }}
                    />
                    <div className="resume-dropzone-icon">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="12" y1="18" x2="12" y2="12" />
                        <line x1="9" y1="15" x2="12" y2="12" />
                        <line x1="15" y1="15" x2="12" y2="12" />
                      </svg>
                    </div>
                    <p className="resume-dropzone-text">
                      {resumeLoading && resumeFile
                        ? 'Parsing PDF...'
                        : 'Drag & drop a PDF here or click to browse'}
                    </p>
                    <span className="resume-dropzone-hint">PDF files only, max 5MB</span>
                  </div>

                  <div className="resume-divider">
                    <span>or paste text</span>
                  </div>

                  <textarea
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    placeholder="Paste your resume text here..."
                    rows="4"
                  />
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={handleParseResume}
                    disabled={resumeLoading || !resumeText.trim()}
                  >
                    {resumeLoading && !resumeFile ? 'Parsing...' : 'Parse Text'}
                  </button>
                </div>
              </div>
            )}
```

- [ ] **Step 4: Add CSS for the upload dropzone**

Add to the end of `frontend/src/Profile.css` (before the `@media` query):

```css
/* Resume upload dropzone */
.resume-dropzone {
  border: 2px dashed var(--color-border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-bg);
  margin-bottom: 12px;
}
.resume-dropzone:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}
.resume-dropzone.drag-active {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}
.resume-dropzone-icon {
  color: var(--color-muted);
  margin-bottom: 8px;
}
.resume-dropzone:hover .resume-dropzone-icon,
.resume-dropzone.drag-active .resume-dropzone-icon {
  color: var(--color-primary);
}
.resume-dropzone-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px;
}
.resume-dropzone-hint {
  font-size: 12px;
  color: var(--color-muted);
}

/* Divider between upload and text paste */
.resume-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.resume-divider::before,
.resume-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border);
}
```

- [ ] **Step 5: Verify frontend build**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx webpack --mode development 2>&1 | tail -3`

Expected: `compiled successfully`

- [ ] **Step 6: Run frontend tests**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx jest --verbose 2>&1 | tail -10`

Expected: 15/15 pass.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/Profile.jsx frontend/src/Profile.css frontend/src/api.js
git commit -m "feat: add PDF upload to Profile import-from-resume section

Users can now drag-and-drop or click-to-browse a PDF file in the
Profile page. The upload area sits above the existing text-paste
textarea with a divider. Includes file type and size validation
(PDF only, 5MB max), drag-active visual feedback, and loading state."
```

---

### Task 4: Add Backend PDF Upload Validation Tests

**Problem:** The existing backend test coverage for `/api/upload-resume` is thin. Need tests for validation (no file, wrong type, empty file) and successful extraction.

**Files:**
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Add validation tests**

Add to `tests/test_profile.py`:

```python
def test_upload_resume_rejects_no_file(client, seeker_token):
    """Upload endpoint should return 400 when no file is provided."""
    res = client.post('/api/upload-resume',
                      data={},
                      content_type='multipart/form-data',
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 400
    assert 'No file' in res.get_json()['message']


def test_upload_resume_rejects_non_pdf(client, seeker_token):
    """Upload endpoint should reject non-PDF files."""
    import io
    data = {'resume': (io.BytesIO(b'not a pdf'), 'resume.txt')}
    res = client.post('/api/upload-resume',
                      data=data,
                      content_type='multipart/form-data',
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 400
    assert 'PDF' in res.get_json()['message']


def test_upload_resume_requires_auth(client):
    """Upload endpoint should require authentication."""
    import io
    data = {'resume': (io.BytesIO(b'fake'), 'resume.pdf')}
    res = client.post('/api/upload-resume',
                      data=data,
                      content_type='multipart/form-data')
    assert res.status_code == 401


def test_upload_resume_extracts_skills_from_pdf(client, seeker_token):
    """Upload endpoint should extract skills from PDF content."""
    import io
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Skills: Python, JavaScript, React, Docker, AWS", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    data = {'resume': (io.BytesIO(pdf_bytes), 'resume.pdf')}
    res = client.post('/api/upload-resume',
                      data=data,
                      content_type='multipart/form-data',
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    result = res.get_json()
    skills = result['extracted_skills']
    skills_lower = [s.lower() for s in skills]
    assert 'python' in skills_lower
    assert 'react' in skills_lower
    assert 'aws' in skills_lower
    # Verify correct casing
    assert 'AWS' in skills, f"Expected 'AWS' not 'Aws': {skills}"
```

- [ ] **Step 2: Run the new tests**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py -k "upload_resume" -v`

Expected: All 5 upload tests pass (4 new + 1 from Task 1).

- [ ] **Step 3: Run full backend suite**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v 2>&1 | tail -10`

Expected: All pass (~100 tests).

- [ ] **Step 4: Commit**

```bash
git add tests/test_profile.py
git commit -m "test: add PDF upload validation and extraction tests

Tests cover: no file (400), non-PDF file (400), missing auth (401),
successful skill extraction with correct casing from PDF content."
```

---

## Quick Reference

| Task | What | Files |
|------|------|-------|
| 1 | Fix backend upload endpoint — add experience extraction | `app.py`, `tests/test_profile.py` |
| 2 | Add `uploadResumePdf()` to `api.js` | `frontend/src/api.js` |
| 3 | Add file upload UI with drag-and-drop to Profile | `Profile.jsx`, `Profile.css` |
| 4 | Add backend upload validation tests | `tests/test_profile.py` |
