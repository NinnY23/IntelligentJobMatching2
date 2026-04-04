# Intelligent Job Matching — Full Design Spec
**Date:** 2026-04-04
**Project:** KMITL Team Software Engineering Project (01286990)
**Team:** Yanin Sae Ma (66011301), Syril Tuladhar (66011244)

---

## Overview

Full-stack web application for intelligent job matching between job seekers and employers. Approximately 50% complete. This spec covers all remaining work to complete the project per the official requirements document.

**Approach:** Feature-by-feature, full-stack (Option C) — each sprint delivers a working vertical slice. The app is always in a runnable state.

---

## Hard Requirements (from spec)

| Requirement | Status |
|---|---|
| React frontend | ✅ Done |
| Flask backend (Python 3) | ✅ Done |
| MySQL database | ❌ Currently SQLite — must migrate |
| Prolog reasoning engine (pyswip) | ❌ Not implemented |
| JWT authentication | ✅ Waived — current token system acceptable |
| In-app messaging (photo + file support) | ❌ Not implemented |
| Resume upload & profile population | ✅ Done |
| Job posting CRUD (employer) | ⚠️ Create done; Edit/Delete missing |
| Job seeker: ranked match results | ⚠️ Backend done; Frontend not wired |
| Job application flow | ❌ Not implemented |
| Employer: view & shortlist applicants | ❌ Not implemented |

---

## Sprint Plan

### Sprint 1 — Foundation & Repo Cleanup

**Files to delete:**
- `backend/` — entire folder (old in-memory version, unused)
- `jobs.py` — unused at root
- `matcher.py` — unused at root
- `interpreter.py` — contains only `false.` (Prolog leftover, not Python)
- `database.db` — SQLite file, replaced by MySQL

**Files to create:**
- `.env` — holds `DB_URI`, `SECRET_KEY`, `FLASK_ENV` (not committed)
- `.env.example` — committed template showing required keys without values
- `matching.pl` — Prolog rules file for the job matching engine
- `prolog_engine.py` — Python bridge to SWI-Prolog via pyswip

**Changes to existing files:**
- `app.py` — load config from `.env` via `python-dotenv`; replace hardcoded MySQL URI; add `bcrypt` password hashing on signup and login; remove `/api/debug/users` and `/api/debug/jobs` endpoints; add `/api/jobs` alias for `/api/job-posts` to fix `api.js` mismatch
- `requirements.txt` — add `python-dotenv`, `bcrypt`, `pyswip`; remove `PyPDF2` (unused; PyMuPDF is already used for PDF parsing)
- `frontend/src/api.js` — fix all endpoint names to match backend

**MySQL schema:**
- `users` — id, email, password, name, phone, location, bio, skills, role, created_at, updated_at *(no changes)*
- `jobs` — id, employer_id, position, company, location, description, required_skills, **preferred_skills** *(new column, replaces single `skills` field)*, salary_min, salary_max, job_type, openings, deadline, applicants, created_at, updated_at

> **Note:** The existing `skills` column in `jobs` becomes `required_skills`. A new `preferred_skills` column is added (comma-separated string, nullable). The Create Job and Edit Job forms both get a "Preferred Skills" field. The Prolog engine uses both columns.

**New tables added in later sprints:**
- `applications` (Sprint 3) — id, job_id, user_id, status (pending/shortlisted/withdrawn), created_at
- `messages` (Sprint 6) — id, sender_id, receiver_id, job_id, body, created_at, read (bool), attachment_path, attachment_name, attachment_type

---

### Sprint 2 — Prolog Integration

**SWI-Prolog installation** required on the machine running the backend. Install via the official SWI-Prolog installer. pyswip is the Python binding.

**`matching.pl` — rule file (committed to repo):**
```prolog
% suitable/3 — true if candidate matches >= 50% of required skills
% Score is weighted: 70% required skills + 30% preferred skills
suitable(Candidate, Job, Score) :-
    candidate_skills(Candidate, CSkills),
    job_required_skills(Job, RSkills),
    job_preferred_skills(Job, PSkills),
    intersection(CSkills, RSkills, MatchedRequired),
    intersection(CSkills, PSkills, MatchedPreferred),
    length(RSkills, RLen), RLen > 0,
    length(MatchedRequired, MRLen),
    RequiredScore is (MRLen / RLen) * 70,
    length(PSkills, PLen),
    ( PLen > 0
    -> length(MatchedPreferred, MPLen),
       PreferredScore is (MPLen / PLen) * 30
    ;  PreferredScore is 0
    ),
    Score is RequiredScore + PreferredScore,
    Score >= 50.
```

**`prolog_engine.py` — Python bridge:**
- Loads `matching.pl` on module import via `pyswip.Prolog`
- `rank_candidates(job_id) -> list[dict]` — asserts candidate and job facts, queries `suitable/3`, retracts facts, returns list sorted by score descending. Each result: `{user_id, name, score, matched_skills, missing_skills}`
- `rank_jobs_for_candidate(user_id) -> list[dict]` — asserts all active jobs and the candidate's profile, queries `suitable/3` for each job, returns ranked list

**API endpoints updated/added:**
- `GET /api/jobs/matches` — returns jobs ranked for the logged-in job seeker (calls `rank_jobs_for_candidate`)
- `GET /api/jobs/<id>/candidates` — returns candidates ranked for a job (employer only, calls `rank_candidates`)

**Score thresholds:**
- ≥ 80% — Strong match (green badge)
- 50–79% — Partial match (indigo badge)
- < 50% — Hidden from results by default

---

### Sprint 3 — Job Seeker Flow

**`/jobs` page — Find Jobs (redesigned `JobMatch.jsx`):**
- Fetches from `GET /api/job-posts` on load (replaces hardcoded sample data)
- Sidebar filters: location (dropdown), job type (Full-time/Part-time/Remote/Contract), salary range (min/max inputs), minimum match % (slider, 0–100)
- Job cards sorted by match score descending; score badge colour-coded per thresholds above
- Cards show: job title, company, location, job type, salary range, top 3 required skills, match score badge

**`/jobs/matches` tab — My Matches:**
- Fetches from `GET /api/jobs/matches`
- Same card layout but pre-filtered to jobs where score ≥ 50%
- Empty state: "Complete your profile and add skills to see matches."

**Job detail modal (overlay, not separate page):**
- Opens when any job card is clicked
- Shows: full description, all required + preferred skills as tags, salary, deadline, openings remaining
- Skill gap section: two rows — ✅ matched skills (indigo tags), ❌ missing skills (red tags)
- Circular match score ring (CSS only)
- "Apply Now" primary button → `POST /api/jobs/<id>/apply`; button becomes "Applied ✓" (disabled) if already applied
- "Message Employer" outline button (enabled in Sprint 6)

**`/applications` page — new route:**
- Fetches from `GET /api/applications` (returns applications for logged-in user)
- Table: job title, company, date applied, match score, status chip (Pending / Shortlisted / Withdrawn)
- "Withdraw" button → `DELETE /api/applications/<id>`; disabled if status is Shortlisted

**New backend endpoints:**
- `POST /api/jobs/<id>/apply` — create application; reject duplicate (409 if already applied); reject if profile incomplete (400)
- `GET /api/applications` — list applications for logged-in job seeker
- `DELETE /api/applications/<id>` — withdraw application (job seeker only, own applications only)

---

### Sprint 4 — Employer Flow

**`/dashboard` page — Employer dashboard:**
- Summary cards: Total Active Jobs, Total Applicants (across all jobs), Total Shortlisted
- Quick-action buttons: "Post a Job", "View My Jobs"
- Recent activity list: last 5 applicants across all jobs

**`/my-jobs` page:**
- Lists employer's job postings: title, # applicants, # openings, deadline, Active/Closed chip
- Per-row actions: **Edit** (opens pre-filled form modal), **Delete** (confirmation dialog → `DELETE /api/job-posts/<id>`), **View Applicants** (navigates to `/jobs/<id>/applicants`)
- "Post New Job" button → navigates to `/create-job`

**Edit job posting:**
- Same form as Create Job, pre-filled with existing data
- `PUT /api/job-posts/<id>` on save

**`/jobs/:id/applicants` page:**
- Table: candidate name, match % (from Prolog), matched skills, missing skills, date applied, status chip
- Sort: by match score (default) or by date applied
- Filter: All / Shortlisted
- Per-row actions: **Shortlist** (`PATCH /api/applications/<id>/status`), **View Profile** (modal), **Message** (Sprint 6)

**New backend endpoints:**
- `PUT /api/job-posts/<id>` — update job post (employer, own jobs only)
- `DELETE /api/job-posts/<id>` — delete job post (employer, own jobs only; cascades to applications)
- `GET /api/jobs/<id>/applicants` — returns ranked applicants for a job
- `PATCH /api/applications/<id>/status` — update application status (employer only)

---

### Sprint 5 — UI Redesign

All React components rewritten with clean CSS matching Style B (white background, indigo/purple accent palette).

**Brand:** JobMatchAI

**Design tokens (CSS variables in `index.css`):**
```css
--color-primary: #6366f1;
--color-primary-dark: #4338ca;
--color-primary-light: #e0e7ff;
--color-success: #16a34a;
--color-danger: #dc2626;
--color-text: #1e1b4b;
--color-muted: #6b7280;
--color-border: #e5e7eb;
--color-bg: #f8faff;
--font: 'Inter', sans-serif;
--radius: 10px;
--shadow: 0 1px 4px rgba(99,102,241,0.08);
```

**Shared components (new files):**
- `components/Navbar.jsx` — role-aware, shows correct nav items + unread message badge
- `components/JobCard.jsx` — reusable job card with score badge
- `components/SkillTag.jsx` — matched (indigo) / missing (red) / neutral variants
- `components/MatchScoreBadge.jsx` — colour-coded percentage badge
- `components/Modal.jsx` — reusable overlay modal
- `components/ConfirmDialog.jsx` — reusable delete/withdraw confirmation

**Pages to redesign (all existing `.css` files replaced):**
Login, SignUp, ForgotPassword, Profile, JobMatch (Find Jobs), CreateJobPost + all new pages from Sprints 3 & 4.

**Responsive breakpoints:**
- Desktop (≥1024px): sidebar visible
- Tablet (768–1023px): sidebar collapsible
- Mobile (<768px): sidebar becomes a filter drawer (toggle button)

---

### Sprint 6 — Messaging

**Access control:** A job seeker can initiate a message only after applying to a job. An employer can message any applicant. This prevents unsolicited contact.

**`/messages` page:**
- Left panel: conversation list — avatar initials, name, job context (job title), last message preview, timestamp, unread count badge
- Right panel: conversation thread — chat bubbles (sent right/indigo, received left/grey), message timestamp, read receipt
- Message input bar: text field + 📎 attachment button + send button

**Attachment handling:**
- File picker accepts: `image/*`, `.pdf`, `.doc`, `.docx` — max 10 MB
- Images render as inline thumbnails (click to view full size)
- Other files render as download card with filename, file type icon, and size
- Files stored in `uploads/messages/<sender_id>/` on the server

**Polling:** Frontend polls `GET /api/messages/<user_id>?after=<timestamp>` every 5 seconds for new messages. No WebSocket required.

**New backend endpoints:**
- `GET /api/messages` — list all conversations (one entry per unique correspondent) for logged-in user
- `GET /api/messages/<user_id>` — fetch thread between two users, paginated (50 messages, `?page=` param)
- `POST /api/messages/<user_id>` — send message; accepts `multipart/form-data` with `body` (text) and optional `attachment` (file)
- `PATCH /api/messages/<user_id>/read` — mark all messages from user_id as read

**File serving:** `GET /api/uploads/messages/<path>` — Flask serves uploaded files (auth required; only sender or receiver can access).

---

## Repo Structure After Cleanup

```
/
├── .env                    # local only, not committed
├── .env.example            # committed, shows required keys
├── app.py                  # main Flask backend
├── models.py               # SQLAlchemy models (User, Job, Application, Message)
├── prolog_engine.py        # pyswip bridge to SWI-Prolog
├── matching.pl             # Prolog rules file
├── init_db.py              # DB init + seeding
├── requirements.txt        # updated dependencies
├── uploads/                # uploaded files (not committed)
│   └── messages/
├── frontend/
│   └── src/
│       ├── index.jsx
│       ├── App.jsx
│       ├── api.js
│       ├── index.css       # design tokens + global styles
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── JobCard.jsx
│       │   ├── SkillTag.jsx
│       │   ├── MatchScoreBadge.jsx
│       │   ├── Modal.jsx
│       │   └── ConfirmDialog.jsx
│       └── pages/
│           ├── Login.jsx
│           ├── SignUp.jsx
│           ├── ForgotPassword.jsx
│           ├── Profile.jsx
│           ├── Jobs.jsx           (was JobMatch.jsx)
│           ├── Applications.jsx   (new)
│           ├── CreateJob.jsx      (was CreateJobPost.jsx)
│           ├── MyJobs.jsx         (new)
│           ├── Applicants.jsx     (new)
│           ├── Dashboard.jsx      (new)
│           └── Messages.jsx       (new)
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-04-intelligent-job-matching-design.md
└── tests/
    └── (existing test structure)
```

---

## Non-functional Requirements Addressed

| Requirement | How |
|---|---|
| Page load < 2s | Webpack production build; lazy-load job cards |
| Responsive (mobile/tablet/desktop) | CSS breakpoints per Sprint 5 |
| Secure auth | bcrypt passwords; tokens validated server-side |
| Data privacy | Auth required on all personal data endpoints; file access restricted to participants |
| Clear error messages | Frontend form validation + backend error responses with human-readable messages |
| 500 concurrent users | Out of scope for academic demo; MySQL handles production load better than SQLite |
