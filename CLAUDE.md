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
pytest backend/tests/
```

## Database

- **Engine:** MySQL via `mysql+pymysql`
- **Config:** Hardcoded URI in `app.py` — connection string targets `intelligent_job_matching` database on localhost
- **Tables:** `users` and `jobs`; `jobs.employer_id` FK → `users.id`
- **Skills field:** Stored as comma-separated strings in both tables

## Key Backend Concepts

**Authentication:** Token format is `token_{email}_{timestamp}` — not JWT. Validated by extracting the email and querying the database. Stored in `localStorage` on the frontend.

**RBAC:** `@require_role('employer')` / `@require_role('employee')` decorators in `app.py` gate employer-only endpoints.

**Job matching algorithm** (`calculate_match_score` in `app.py`): Scores candidates by skill overlap — 70% weight on skills matched vs. required.

**Resume parsing:** PyMuPDF extracts text; spaCy NER extracts name; regex extracts email/phone; keyword matching against a hardcoded 30+ skill list.

## Frontend Structure

- `App.jsx` — auth state (localStorage), routing
- `api.js` — all `fetch()` calls to backend
- Routes: `/login`, `/signup`, `/forgot-password`, `/jobs`, `/profile`, `/create-job`
- No state management library — plain React state

## CI

GitHub Actions runs `pytest` on push/PR to `backend/**` paths (Python 3.11).

## Known Issues

- Passwords stored in plaintext (no bcrypt)
- Token system has no expiry or cryptographic signing
- Debug endpoints `/api/debug/users` and `/api/debug/jobs` are exposed
- Database credentials are hardcoded in `app.py`
