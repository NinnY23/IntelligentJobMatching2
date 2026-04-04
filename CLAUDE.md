# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Full-stack intelligent job matching web application. Backend is Python/Flask with MySQL (SQLAlchemy ORM), frontend is React 19 with Webpack. NLP-based resume parsing uses spaCy; job matching uses a skill overlap scoring algorithm.

## Architecture

```
Root app.py          ← Main Flask backend (port 5000)
frontend/            ← React frontend (port 3000)
backend/             ← Legacy in-memory version (not the active backend)
init_db.py           ← Database initialization and seeding
models.py            ← SQLAlchemy model definitions
```

The **root `app.py`** is the active backend (MySQL + SQLAlchemy). The `backend/` folder contains an older in-memory version — do not confuse the two.

## Running the App

### Backend
```bash
# One-time setup
python -m spacy download en_core_web_sm
python init_db.py           # create tables
python init_db.py --seed    # create tables + sample data

# Start server
python app.py               # http://localhost:5000
```

### Frontend
```bash
cd frontend
npm install
npm start       # dev server at http://localhost:3000
npm run build   # production build → dist/bundle.js
npm test        # Jest tests
```

### Backend tests
```bash
pytest tests/ -v            # 88 tests (auth, password reset, profile, job status, etc.)
```

### Frontend tests
```bash
cd frontend
npx jest --verbose          # 15 tests (Login, Jobs, CreateJobPost, App)
```

## Database

- **Engine:** MySQL via `mysql+pymysql`
- **Config:** URI loaded from `DB_URI` env var (`.env` file). Fallback: `sqlite:///dev.db` for development
- **Tables:** `users` and `jobs`; `jobs.employer_id` FK → `users.id`
- **Skills field:** Stored as comma-separated strings in both tables

## Key Backend Concepts

**Authentication:** JWT (HS256) via PyJWT with 24-hour expiry. Tokens contain `user_id`, `email`, `role`, `exp`. Validated by `get_current_user_or_401()` helper and `@require_role` decorator. Stored in `localStorage` on the frontend. Global 401 handler in `api.js` clears localStorage and redirects to login on token expiry.

**Password hashing:** bcrypt via `bcrypt` package. Passwords hashed on signup, verified on login.

**Password reset:** Simulated flow — `POST /api/forgot-password` generates a token logged to server console (no email). `POST /api/reset-password` validates the token and updates the password. Tokens are single-use with 1-hour expiry.

**Job status:** Jobs have a `status` field: `draft`, `active`, or `archived`. Public job listings (`GET /api/job-posts`) only return active jobs. Employers see all statuses via `GET /api/employer/jobs`.

**RBAC:** `@require_role('employer')` / `@require_role('employee')` decorators in `app.py` gate employer-only endpoints.

**Job matching algorithm** (`calculate_match_score` in `app.py`): Scores candidates by skill overlap — 70% weight on skills matched vs. required.

**Resume parsing:** PyMuPDF extracts text; spaCy NER extracts name; regex extracts email/phone; keyword matching against a hardcoded 30+ skill list.

## Frontend Structure

- `App.jsx` — auth state (localStorage), routing
- `api.js` — all `fetch()` calls to backend
- Routes: `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/jobs`, `/profile`, `/create-job`
- `ErrorBoundary` component wraps the app for crash recovery
- Responsive CSS with media queries at 768px breakpoint
- No state management library — plain React state

## CI

GitHub Actions runs `pytest` on push/PR to `backend/**` paths (Python 3.11).

## Known Issues

- Debug endpoints `/api/debug/users` and `/api/debug/jobs` are exposed (disable in production)
- Password reset tokens stored in-memory (lost on server restart)
- Messaging endpoints still use legacy `get_current_user(request)` pattern instead of `get_current_user_or_401()`
- `frontend/node_modules/` is tracked in git (should be removed with `git rm -r --cached`)
