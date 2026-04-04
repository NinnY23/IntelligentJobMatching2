# Intelligent Job Matching — Missing Features & Fixes Design Spec

**Date:** 2026-04-04
**Timeline:** 2 days
**Approach:** PDF Compliance Sprint — address all PDF requirement gaps on Day 1, polish and testing on Day 2

## Context

Analysis of the project PDF (IntelligentJobMatching.pdf) against the current codebase revealed gaps in security, feature completeness, UI/UX, and testing. This spec covers all changes needed to bring the project into full compliance with the PDF requirements while improving code quality.

## Out of Scope

- Refresh tokens / token rotation
- Email sending for password reset
- Flask-Migrate / Alembic database migrations
- CSS framework adoption (Tailwind/Bootstrap)
- WebSocket real-time messaging
- API pagination on job listings
- Swagger/OpenAPI documentation

---

## Day 1: PDF Requirement Compliance

### 1. JWT Authentication

**Requirement:** PDF Section 2.2.2 #10 — "The system must implement a secure authentication mechanism using JWT"

**Current state:** Custom plaintext tokens (`token_{email}_{timestamp}`) with no cryptographic signing and no expiration.

**Changes:**

**Backend (`app.py`):**
- Add `PyJWT` to `requirements.txt`
- Replace `generate_token(email)` with JWT encoding:
  ```python
  jwt.encode({'user_id': user.id, 'email': user.email, 'role': user.role, 'exp': datetime.utcnow() + timedelta(hours=24)}, SECRET_KEY, algorithm='HS256')
  ```
- Replace `get_current_user()` to decode JWT via `jwt.decode()` and lookup user by `user_id` from payload
- Return `401` with `"Token expired"` message on `jwt.ExpiredSignatureError`

**Frontend:**
- No changes to token storage/sending (already uses `Authorization: Bearer <token>`)
- Add global 401 handling in `api.js` — clear localStorage, redirect to `/login`

**Files modified:** `app.py`, `requirements.txt`, `api.js`

---

### 2. Move Credentials to `.env`

**Current state:** Hardcoded `SQLALCHEMY_DATABASE_URI` and `SECRET_KEY` in `app.py`.

**Changes:**
- Load config via `python-dotenv` (already in requirements.txt):
  ```python
  SECRET_KEY = os.getenv('SECRET_KEY', 'dev-fallback-key')
  SQLALCHEMY_DATABASE_URI = os.getenv('DB_URI', 'sqlite:///dev.db')
  ```
- Update `.env.example` with all required variables
- Add `.env` to `.gitignore` if not present

**Files modified:** `app.py`, `.env.example`, `.gitignore`

---

### 3. Forgot / Reset Password

**Requirement:** PDF UC1 includes authentication flows. Currently the forgot-password endpoint is a stub.

**Changes:**

**Backend (`app.py`):**
- `POST /api/forgot-password` — accepts email, generates a random reset token with 1-hour expiry, stores in an in-memory `password_resets` dict, logs token to console
- `POST /api/reset-password` — new endpoint, accepts `{token, new_password}`, validates token exists and hasn't expired, updates user password with bcrypt, invalidates token

**Frontend:**
- Update `ForgotPassword.jsx` — show success message ("Reset link generated — check server console in development mode")
- New `ResetPassword.jsx` — form with new password + confirm password, reads token from URL query param `?token=xxx`
- Add route `/reset-password` in `App.jsx`

**Files modified:** `app.py`, `frontend/src/ForgotPassword.jsx`, `frontend/src/App.jsx`
**Files created:** `frontend/src/pages/ResetPassword.jsx`

---

### 4. Resume Auto-Populate Profile

**Requirement:** PDF Section 2.1.1 #3 — "upload a resume to automatically populate their profile"

**Current state:** Extracts name, email, phone, skills, education from PDF. Only merges skills into profile; other fields are returned in response but not saved.

**Changes:**

**Backend (`app.py` — `/api/upload-resume`):**
- After extraction, save to user profile:
  - `name` — only if user's current name is empty
  - `phone` — only if current phone is empty
  - `education` — only if current education is empty
  - `experience` — only if current experience is empty
  - Skills — merge with deduplication (already working)
- Commit changes to database

**Frontend (`Profile.jsx`):**
- After successful resume upload, refresh form fields from response data
- Show notification: "Profile updated from resume — X fields populated"

**Files modified:** `app.py`, `Profile.jsx`

---

### 5. Job Drafts & Archiving

**Requirement:** PDF UC4 Alt A2 ("Save as Draft"), PDF UC5 Alt A2 ("Archive Instead of Delete")

**Changes:**

**Database (`models.py`):**
- Add `status` field to `Job` model: `db.Column(db.String(20), default='active')` — values: `'draft'`, `'active'`, `'archived'`
- Update `to_dict()` to include status

**Backend (`app.py`):**
- `POST /api/job-posts` — accept optional `status` param, default `'active'`
- `GET /api/job-posts` — filter to `status='active'` only (public listings for employees)
- `GET /api/employer/jobs` — return all statuses for the employer
- `PUT /api/job-posts/<id>` — allow status changes (draft→active, active→archived, archived→active)

**Frontend (`MyJobs.jsx`):**
- Status badge on each job card (Draft / Active / Archived)
- "Archive" button alongside "Delete"
- "Publish" button on draft jobs
- Filter tabs: All | Active | Drafts | Archived

**Frontend (`CreateJobPost.jsx`):**
- "Save as Draft" button next to "Post Job"

**Files modified:** `models.py`, `app.py`, `MyJobs.jsx`, `CreateJobPost.jsx`

---

## Day 2: Polish, UI/UX & Testing

### 6. Responsive CSS

**Requirement:** PDF Section 2.1.2 #2 — "fully responsive across smartphones, tablets, and laptops"

**Approach:** Add media queries to existing CSS. No new framework.

**Breakpoints:**
- Desktop: >1024px (current layout, no changes)
- Tablet: 768–1024px
- Mobile: <768px

**Key responsive changes:**
- **Navbar** — hamburger menu on mobile with slide-out/dropdown menu
- **Job cards** — grid on desktop, stacked full-width on mobile
- **Forms** (profile, create job, login/signup) — full-width single-column inputs on mobile
- **Dashboard stats** — row on desktop, stacked column on mobile
- **Messages** — side-by-side panes on desktop; conversation list as full screen on mobile, tap to open thread with back button
- **Applicants table** — card layout on mobile instead of table rows

**Files modified:** CSS files — `Navbar.css`, `Jobs.css`, `Profile.css`, `CreateJobPost.css`, `Dashboard.css`, `MyJobs.css`, `Applicants.css`, `Messages.css`, `Applications.css`, `AuthCard.css`
**May create:** A shared `responsive.css` or `global.css` if common breakpoint rules are better centralized

---

### 7. Visual Highlighting

**Requirement:** PDF Section 2.1.2 #6 — "provide visual highlighting of key information in job descriptions"

**Changes:**

**Frontend (`Jobs.jsx` — job detail modal):**
- Matched skills displayed with green background/badge
- Missing skills displayed with orange/red background/badge
- Visual match bar alongside score number: `████████░░ 78%`
- In job description text, bold keywords matching required skills

**Frontend (`Applicants.jsx`):**
- Same color-coded skill treatment on candidate cards
- Matched skills green, missing skills muted

**No backend changes** — matched_skills, missing_skills, and score already returned by Prolog matching API.

**Files modified:** `Jobs.jsx`, `Applicants.jsx`, associated CSS

---

### 8. Error Boundaries & Polish

**Changes:**

- New `ErrorBoundary.jsx` component — React class component wrapping `<App>`, catches render errors, shows "Something went wrong" fallback with retry button
- Standardize loading spinners across pages — consistent skeleton/spinner component
- Global 401 handling in `api.js` — on expired JWT, clear localStorage, redirect to `/login`

**Files created:** `ErrorBoundary.jsx`
**Files modified:** `App.jsx` (wrap with ErrorBoundary), `api.js` (401 handler)

---

### 9. Testing

**Backend test updates:**
- Update `conftest.py` — generate JWT tokens instead of old `token_` format for test fixtures
- New test: forgot-password and reset-password flow (token generation, validation, expiry, password update)
- New test: job draft/archive status filtering (draft not visible in public listings, archive workflow)

**Frontend tests (new files):**
- `Login.test.jsx` — form submission, error display, redirect on success
- `Jobs.test.jsx` — job listing render, match score display, skill highlighting colors
- `CreateJobPost.test.jsx` — form validation, draft vs publish submission

Uses existing Jest + React Testing Library config from `package.json`.

**Files modified:** `tests/conftest.py`
**Files created:** `tests/test_password_reset.py`, `tests/test_job_status.py`, `frontend/src/__tests__/Login.test.jsx`, `frontend/src/__tests__/Jobs.test.jsx`, `frontend/src/__tests__/CreateJobPost.test.jsx`
