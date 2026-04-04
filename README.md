# Intelligent Job Matching

A full-stack web application that intelligently matches job seekers with employers using NLP-based resume parsing and skill overlap scoring.

## Features

- **Smart Job Matching** -- Automatic skill-based matching algorithm scores candidates against job requirements (70% skill overlap weight)
- **Resume Parsing** -- Paste text or upload PDF resumes; extracts name, email, phone, education, experience, and 75+ skills using spaCy NLP and regex
- **Role-Based Access** -- Separate flows for job seekers (apply, track applications, manage profile) and employers (post jobs, review applicants, manage listings)
- **Real-Time Messaging** -- Direct messaging between connected users with file/image attachments
- **Job Management** -- Draft, publish, and archive job posts with deadline tracking
- **Application Tracking** -- Employers can accept/reject applications; seekers see status updates
- **Password Reset** -- Token-based password reset flow

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Webpack, CSS |
| Backend | Python 3.11+, Flask 2.3 |
| Database | MySQL (via SQLAlchemy ORM) |
| NLP | spaCy (en_core_web_sm), PyMuPDF |
| Auth | JWT (PyJWT), bcrypt |
| Testing | pytest (backend), Jest (frontend) |

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **MySQL 8.0+** (or use SQLite for quick dev setup)

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/NinnY23/IntelligentJobMatching2.git
cd IntelligentJobMatching2
```

### 2. Set up the backend

```bash
# Create and activate virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# MySQL (recommended)
DB_URI=mysql+pymysql://root:yourpassword@localhost:3306/intelligent_job_matching

# Or use SQLite for quick setup (no MySQL needed)
# DB_URI=sqlite:///dev.db

SECRET_KEY=your-secret-key-change-this
FLASK_ENV=development
UPLOAD_FOLDER=uploads
```

### 4. Initialize the database

```bash
# Create tables only
python init_db.py

# Or create tables + seed with sample data (recommended for first run)
python init_db.py --seed
```

> If using MySQL, create the database first:
> ```sql
> CREATE DATABASE intelligent_job_matching;
> ```

### 5. Set up the frontend

```bash
cd frontend
npm install
cd ..
```

### 6. Run the application

Open **two terminals**:

**Terminal 1 -- Backend** (from project root):
```bash
python app.py
```
Backend runs at `http://localhost:5000`

**Terminal 2 -- Frontend** (from project root):
```bash
cd frontend
npm start
```
Frontend runs at `http://localhost:3000`

Open your browser to **http://localhost:3000**.

## Sample Accounts (after seeding)

If you ran `python init_db.py --seed`, these accounts are available:

| Role | Email | Password |
|------|-------|----------|
| Employer | employer@company.com | password123 |
| Job Seeker | john@example.com | password123 |
| Job Seeker | jane@example.com | password123 |

## Running Tests

### Backend tests
```bash
pytest tests/ -v
```

### Frontend tests
```bash
cd frontend
npx jest --verbose
```

## Project Structure

```
.
├── app.py                  # Flask backend (API routes, auth, matching)
├── models.py               # SQLAlchemy models (User, Job, Application, Message)
├── init_db.py              # Database initialization and seeding
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── uploads/                # File uploads (attachments, resumes)
├── tests/                  # Backend tests (pytest)
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_profile.py
│   ├── test_messaging.py
│   └── ...
├── frontend/               # React frontend
│   ├── package.json
│   ├── webpack.config.js
│   ├── src/
│   │   ├── App.jsx         # Root component, routing
│   │   ├── api.js          # API client (all fetch calls)
│   │   ├── Profile.jsx     # Profile + resume import
│   │   ├── Login.jsx       # Login/Signup
│   │   ├── pages/
│   │   │   ├── Jobs.jsx        # Job listings with match scores
│   │   │   ├── Messages.jsx    # Real-time messaging
│   │   │   ├── Dashboard.jsx   # User dashboard
│   │   │   ├── MyJobs.jsx      # Employer job management
│   │   │   └── ...
│   │   └── components/
│   │       └── Navbar.jsx
│   └── tests/              # Frontend tests (Jest)
└── docs/                   # Implementation plans
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/signup` | Register new user |
| POST | `/api/login` | Login, returns JWT |
| GET | `/api/profile` | Get current user profile |
| PUT | `/api/profile` | Update profile |
| POST | `/api/parse-resume-text` | Parse pasted resume text |
| POST | `/api/upload-resume` | Upload PDF resume |
| GET | `/api/job-posts` | List active jobs (with match scores) |
| POST | `/api/job-posts` | Create job post (employer) |
| POST | `/api/apply/:id` | Apply to a job |
| GET | `/api/messages/:id` | Get message thread |
| POST | `/api/messages/:id` | Send message with optional attachment |

## License

This project is part of a Software Engineering course at KMITL.
