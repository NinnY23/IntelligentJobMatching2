# Intelligent Job Matching — Fixes & Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Intelligent Job Matching website into full PDF requirement compliance and improve code quality within a 2-day sprint.

**Architecture:** Flask backend with JWT authentication replacing custom tokens, React 19 frontend with responsive CSS media queries, SWI-Prolog matching engine (unchanged). All changes are additive — no architectural rewrites.

**Tech Stack:** Python 3.11, Flask 2.3, PyJWT, React 19, Jest + React Testing Library, pytest

---

## Plan Files

This plan is split across multiple files to keep each manageable:

| File | Tasks | Scope |
|------|-------|-------|
| [Part 1: JWT Auth & .env](2026-04-04-fixes-plan-part1-jwt.md) | Tasks 1-2 | JWT authentication, credentials to .env |
| [Part 2: Forgot Password & Resume](2026-04-04-fixes-plan-part2-password-resume.md) | Tasks 3-4 | Password reset flow, resume auto-populate |
| [Part 3: Job Drafts & Archiving](2026-04-04-fixes-plan-part3-job-status.md) | Task 5 | Draft/active/archived job status |
| [Part 4: Frontend Polish](2026-04-04-fixes-plan-part4-frontend.md) | Tasks 6-8 | Responsive CSS, visual highlighting, error boundaries |
| [Part 5: Testing](2026-04-04-fixes-plan-part5-testing.md) | Task 9 | Backend test updates, frontend tests |

## Execution Order

Tasks must be executed in order 1-9. Tasks 1-5 are Day 1 (PDF compliance). Tasks 6-9 are Day 2 (polish & testing).

## File Map

### Files Modified
- `app.py` — JWT auth, forgot-password, resume auto-populate, job status filtering
- `models.py` — Job status field
- `requirements.txt` — Add PyJWT
- `.env.example` — Document all env vars
- `frontend/src/api.js` — Global 401 handler
- `frontend/src/App.jsx` — Error boundary wrapper, reset-password route
- `frontend/src/ForgotPassword.jsx` — Updated success message
- `frontend/src/Profile.jsx` — Resume auto-populate UI refresh
- `frontend/src/CreateJobPost.jsx` — Save as Draft button
- `frontend/src/pages/MyJobs.jsx` — Status badges, archive, filter tabs
- `frontend/src/pages/Jobs.jsx` — Skill highlighting, match bar
- `frontend/src/pages/Applicants.jsx` — Skill highlighting
- `frontend/src/components/Navbar.css` — Responsive hamburger
- `frontend/src/pages/Jobs.css` — Responsive grid
- `frontend/src/Profile.css` — Responsive form
- `frontend/src/CreateJobPost.css` — Responsive form
- `frontend/src/pages/Dashboard.css` — Responsive stats
- `frontend/src/pages/MyJobs.css` — Responsive + status badges
- `frontend/src/pages/Messages.css` — Responsive split pane
- `frontend/src/pages/Applications.css` — Responsive cards
- `frontend/src/pages/Applicants.css` — Responsive + highlighting
- `frontend/src/components/AuthCard.css` — Responsive auth forms
- `tests/conftest.py` — JWT token generation for fixtures

### Files Created
- `frontend/src/pages/ResetPassword.jsx` — Password reset form
- `frontend/src/components/ErrorBoundary.jsx` — React error boundary
- `tests/test_password_reset.py` — Password reset tests
- `tests/test_job_status.py` — Job draft/archive tests
- `frontend/src/__tests__/Login.test.jsx` — Login component tests
- `frontend/src/__tests__/Jobs.test.jsx` — Jobs page tests
- `frontend/src/__tests__/CreateJobPost.test.jsx` — Create job tests
