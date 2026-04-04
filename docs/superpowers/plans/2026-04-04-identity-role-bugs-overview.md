# Identity, Role & Application Bugs — Fix Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the identity mismatch bug (login as Ester, see John Doe), seed data role bug (employer seed user has no role set), and employer applicant visibility issues so the full user workflow works end-to-end.

**Architecture:** The bugs span three layers: (1) seed data creates users without `role` field, making the "employer" a default employee; (2) the frontend has no mechanism to refresh stale user data from the server after page reload; (3) the withdraw endpoint DELETEs the application row instead of setting status='withdrawn', making it disappear from the employee's applications list. All fixes are surgical — no new tables or endpoints needed.

**Tech Stack:** Flask/SQLAlchemy backend, React 19 frontend, JWT auth, MySQL

---

## Root Cause Analysis

### Bug A: "Login as Ester but see John Doe" — Identity Mismatch

**Root cause chain:**
1. `init_db.py` seeds 3 users — user1 (John Doe), user2 (Jane Smith), user3 (Tech Company HR)
2. Someone logs in as John Doe → `localStorage.user = { name: "John Doe", ... }`
3. That person (or another browser tab) signs up as "Ester" → new user created
4. BUT: If the browser still has the old token + user in localStorage from step 2, and the App.jsx `useEffect` (line 46-48) reads stale localStorage on mount, the Navbar shows "John Doe"
5. **The fundamental flaw:** After login/signup, the frontend trusts localStorage forever. There's no mechanism to re-fetch the user profile from the server on page reload. If localStorage is stale (from a previous session, or corrupted by the resume-parse bug below), the wrong identity persists.

**Secondary cause — Profile.jsx resume parse saves wrong object:**
- `Profile.jsx:65` (manual save) correctly does: `localStorage.setItem('user', JSON.stringify(updatedUser.user))`
- `Profile.jsx:98` (resume parse) incorrectly does: `localStorage.setItem('user', JSON.stringify(updatedUser))` — this saves the FULL API response `{ user: {...}, extracted_skills: [...], fields_populated: 3 }` as the "user" object, corrupting localStorage with extra fields and nesting

### Bug B: Employer Can't See Applicants

**Root cause:**
1. `init_db.py` never sets `role` on any seed user → all 3 users get the model default `role='employee'`
2. The "employer" seed user (`employer@company.com`) is actually role=employee
3. When this user tries to access `/api/employer/jobs` or `/api/job-posts/<id>/applicants`, the `@require_role('employer')` decorator returns 403
4. Even if a real employer signs up properly, their jobs won't have seed applications, so the applicant list is empty

### Bug C: Withdraw Deletes Instead of Setting Status

**Root cause:**
- `app.py:845` does `db.session.delete(application)` — the application ROW is deleted from the database
- The frontend `Applications.jsx:130` does `prev.map(a => a.id === confirmTarget.id ? { ...a, status: 'withdrawn' } : a)` — it optimistically updates the status in React state
- But on next page load, the application is gone from the database, so it disappears entirely
- The correct behavior per the status model (`pending` → `shortlisted` → `withdrawn`) is to SET status='withdrawn', not delete the row

---

## Summary of All Bugs

| # | Bug | File(s) | Line(s) | Severity |
|---|-----|---------|---------|----------|
| 1 | Seed users have no `role` set — employer is employee | `init_db.py` | 53-81 | Critical |
| 2 | No user-refresh on page reload — stale localStorage identity | `App.jsx` | 41-57 | Critical |
| 3 | Resume parse saves wrong object to localStorage | `Profile.jsx` | 98 | High |
| 4 | Withdraw endpoint DELETEs row instead of setting status | `app.py` | 845 | High |
| 5 | Seed data has no sample applications | `init_db.py` | — | Medium |
| 6 | `Login.jsx` doesn't use centralized `loginUser()` from `api.js` | `Login.jsx` | 15-20 | Low |

## Plan Files

1. **This file** — Overview
2. **`2026-04-04-identity-role-bugs-tasks.md`** — All implementation tasks
