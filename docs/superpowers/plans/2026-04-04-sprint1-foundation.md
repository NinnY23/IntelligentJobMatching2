# Sprint 1: Foundation & Repo Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up dead code, move secrets to `.env`, add bcrypt password hashing, fix the Job model, and wire the webpack dev proxy so the frontend can reach Flask without CORS workarounds.
**Architecture:** Root `app.py` is the only active Flask backend (port 5000); the `backend/` folder and loose legacy scripts are deleted. Configuration is loaded from `.env` via `python-dotenv`. Tests run against an in-memory SQLite database via `pytest-flask`.
**Tech Stack:** Python 3.13 / Flask 2.3 / SQLAlchemy 2.0 / mysql+pymysql / bcrypt 4.0.1 / python-dotenv 1.0.0 / pytest 7.4.0 / pytest-flask 1.3.0 / React 19 / Webpack 5

---

## File Map

| Action | Path |
|--------|------|
| Delete | `backend/` (entire folder) |
| Delete | `jobs.py` |
| Delete | `matcher.py` |
| Delete | `interpreter.py` |
| Delete | `database.db` |
| Create | `.env` (not committed) |
| Create | `.env.example` |
| Modify | `.gitignore` |
| Modify | `requirements.txt` |
| Modify | `frontend/webpack.config.js` |
| Modify | `app.py` |
| Modify | `models.py` |
| Modify | `init_db.py` |
| Create | `tests/conftest.py` |
| Create | `tests/test_auth.py` |
| Create | `tests/test_models.py` |
| Create | `tests/test_endpoints.py` |

---

### Task 1.1: Delete Dead Code

**Files:**
- Delete: `backend/`
- Delete: `jobs.py`
- Delete: `matcher.py`
- Delete: `interpreter.py`
- Delete: `database.db`

- [ ] **Step 1.1.1: Remove legacy files with git**
```bash
git rm -r backend/
git rm jobs.py matcher.py interpreter.py database.db
```
Expected output:
```
rm 'backend/...'
rm 'jobs.py'
rm 'matcher.py'
rm 'interpreter.py'
rm 'database.db'
```
(Each file that exists will produce one `rm '...'` line. Files already absent will print a warning — that is acceptable.)

- [ ] **Step 1.1.2: Verify files are gone**
```bash
ls backend/ 2>&1 || echo "backend/ gone"
ls jobs.py matcher.py interpreter.py database.db 2>&1 || echo "legacy files gone"
```
Expected output (all four files absent):
```
backend/ gone
legacy files gone
```

- [ ] **Step 1.1.3: Commit**
```bash
git add -A
git commit -m "chore: delete legacy backend folder and dead-code scripts"
```

---

### Task 1.2: Create .env and .env.example

**Files:**
- Create: `.env`
- Create: `.env.example`
- Modify: `.gitignore`

- [ ] **Step 1.2.1: Write .env (never committed)**

Create the file `E:\Projects\Intelligent job matching website\.env` with the following exact content:
```
DB_URI=mysql+pymysql://root:LiShuang4330%40@localhost:3306/intelligent_job_matching
SECRET_KEY=dev-secret-change-in-production
FLASK_ENV=development
UPLOAD_FOLDER=uploads
```

- [ ] **Step 1.2.2: Write .env.example (committed as a template)**

Create the file `E:\Projects\Intelligent job matching website\.env.example` with the following exact content:
```
DB_URI=mysql+pymysql://user:password@localhost:3306/intelligent_job_matching
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
UPLOAD_FOLDER=uploads
```

- [ ] **Step 1.2.3: Update .gitignore**

Open `.gitignore` (create it if it does not exist) and ensure it contains these lines:
```
# Environment secrets
.env

# Legacy SQLite database
database.db

# Uploaded resume files
uploads/

# Python cache
__pycache__/
*.pyc
*.pyo

# Node
node_modules/
frontend/dist/
```

- [ ] **Step 1.2.4: Verify .env is ignored**
```bash
git status --short
```
Expected output: `.env` does NOT appear in the list. `.env.example` appears as an untracked (`??`) or staged (`A`) file.

- [ ] **Step 1.2.5: Commit**
```bash
git add .env.example .gitignore
git commit -m "chore: add .env.example and update .gitignore"
```

---

### Task 1.3: Update requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1.3.1: Replace requirements.txt content**

Overwrite `E:\Projects\Intelligent job matching website\requirements.txt` with exactly:
```
Flask==2.3.0
Flask-CORS==4.0.0
Werkzeug==2.3.0
PyMuPDF==1.23.8
spacy==3.7.2
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.23
python-dotenv==1.0.0
bcrypt==4.0.1
pyswip==0.2.10
pymysql==1.1.0
pytest==7.4.0
pytest-flask==1.3.0
```
(Removed: `PyPDF2==3.0.1`. Added: `python-dotenv`, `bcrypt`, `pyswip`, `pymysql`, `pytest`, `pytest-flask`.)

- [ ] **Step 1.3.2: Install updated dependencies**
```bash
pip install -r requirements.txt
```
Expected output ends with:
```
Successfully installed ...
```
No `ERROR` lines. If `pyswip` warns about SWI-Prolog not being found, that is acceptable — SWI-Prolog itself is installed manually in Sprint 2.

- [ ] **Step 1.3.3: Commit**
```bash
git add requirements.txt
git commit -m "chore: update requirements — drop PyPDF2, add dotenv/bcrypt/pyswip/pytest"
```

---

### Task 1.4: Add Webpack Dev Proxy

**Files:**
- Modify: `frontend/webpack.config.js`

- [ ] **Step 1.4.1: Read the current devServer section**

Open `frontend/webpack.config.js` and locate the `devServer` block. It currently looks like:
```js
devServer: {
  static: path.join(__dirname, 'dist'),
  compress: true,
  port: 3000,
  open: true
}
```

- [ ] **Step 1.4.2: Replace devServer block**

Replace the block above with:
```js
devServer: {
  static: path.join(__dirname, 'dist'),
  compress: true,
  port: 3000,
  open: true,
  historyApiFallback: true,
  proxy: [
    {
      context: ['/api', '/uploads'],
      target: 'http://localhost:5000',
      changeOrigin: true
    }
  ]
}
```

- [ ] **Step 1.4.3: Verify webpack starts without errors**
```bash
cd frontend && npx webpack serve --mode development 2>&1 | head -20
```
Expected: the output contains `<i> [webpack-dev-server] Project is running at:` with no proxy-related errors. Stop the process with Ctrl-C after verification.

- [ ] **Step 1.4.4: Commit**
```bash
git add frontend/webpack.config.js
git commit -m "feat: add webpack dev proxy for /api and /uploads to Flask port 5000"
```

---

### Task 1.5: Migrate app.py to Use .env

**Files:**
- Modify: `app.py`

- [ ] **Step 1.5.1: Add dotenv import at the top of app.py**

In `app.py`, find the imports block near the top. Add these two lines immediately after the last `import` statement and before any `app = Flask(...)` line:
```python
from dotenv import load_dotenv
load_dotenv()
```

- [ ] **Step 1.5.2: Remove unused PyPDF2 import**

In `app.py`, delete the line:
```python
import PyPDF2
```
(It appears around line 6. If it does not exist, skip this step.)

- [ ] **Step 1.5.3: Replace hardcoded config with os.environ lookups**

Find this block in `app.py` (around lines 115-135):
```python
CORS(app)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:LiShuang4330%40@localhost:3306/intelligent_job_matching'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()
```

Replace it with:
```python
CORS(app)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DB_URI',
    'mysql+pymysql://root:password@localhost:3306/intelligent_job_matching'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()
```

- [ ] **Step 1.5.4: Verify app starts and reads .env**
```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
import os
print('DB_URI starts with mysql+pymysql:', os.environ.get('DB_URI','').startswith('mysql+pymysql'))
print('SECRET_KEY set:', bool(os.environ.get('SECRET_KEY')))
"
```
Expected output:
```
DB_URI starts with mysql+pymysql: True
SECRET_KEY set: True
```

- [ ] **Step 1.5.5: Commit**
```bash
git add app.py
git commit -m "feat: load config from .env via python-dotenv, remove hardcoded DB credentials"
```

---

### Task 1.6: Add bcrypt Password Hashing

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_auth.py`
- Modify: `app.py`

- [ ] **Step 1.6.1: Create tests/ package and conftest.py**

Create the file `E:\Projects\Intelligent job matching website\tests\__init__.py` with empty content.

Create `E:\Projects\Intelligent job matching website\tests\conftest.py`:
```python
import pytest
from app import app as flask_app, db


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
```

- [ ] **Step 1.6.2: Write test_auth.py (tests must FAIL at this point)**

Create `E:\Projects\Intelligent job matching website\tests\test_auth.py`:
```python
import json


def test_signup_hashes_password(client):
    """Password stored in DB must not equal the plaintext input."""
    res = client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'plaintext123',
        'name': 'Test User',
        'role': 'employee'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert 'token' in data

    # Directly inspect the stored password via the ORM
    from app import db
    from models import User
    with client.application.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        # The stored value must NOT be the plaintext password
        assert user.password != 'plaintext123'
        # The stored value must look like a bcrypt hash (starts with $2b$)
        assert user.password.startswith('$2b$')


def test_login_with_correct_password(client):
    client.post('/api/signup', json={
        'email': 'login@example.com',
        'password': 'mypassword',
        'name': 'Login User',
        'role': 'employee'
    })
    res = client.post('/api/login', json={
        'email': 'login@example.com',
        'password': 'mypassword'
    })
    assert res.status_code == 200
    assert 'token' in res.get_json()


def test_login_with_wrong_password(client):
    client.post('/api/signup', json={
        'email': 'wrong@example.com',
        'password': 'correct',
        'name': 'Wrong User',
        'role': 'employee'
    })
    res = client.post('/api/login', json={
        'email': 'wrong@example.com',
        'password': 'incorrect'
    })
    assert res.status_code == 401
```

- [ ] **Step 1.6.3: Run tests — expect FAILED**
```bash
pytest tests/test_auth.py -v
```
Expected output (before implementing bcrypt):
```
FAILED tests/test_auth.py::test_signup_hashes_password - AssertionError: assert not user.password.startswith('$2b$')
```
The other two tests may pass or fail depending on current state — that is acceptable. The key failure is `test_signup_hashes_password`.

- [ ] **Step 1.6.4: Add bcrypt import to app.py**

In `app.py`, add to the imports section:
```python
import bcrypt
```

- [ ] **Step 1.6.5: Update signup endpoint to hash password**

In `app.py`, find the signup endpoint. Locate the line that stores the password, which currently reads:
```python
password=password,  # In production: use bcrypt.hashpw()
```

Replace the password storage with hashing. The full relevant section of the signup endpoint should become:
```python
# Hash the password before storing
hashed_password = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt()
).decode('utf-8')

new_user = User(
    email=email,
    password=hashed_password,
    name=name,
    role=role
)
```
(Keep all other parts of the signup endpoint — validation, duplicate-email check, token generation, etc. — unchanged.)

- [ ] **Step 1.6.6: Update login endpoint to verify hash**

In `app.py`, find the login endpoint. Locate the password check, which currently reads:
```python
if not user or user.password != password:  # In production: use bcrypt.checkpw()
```

Replace it with:
```python
if not user or not bcrypt.checkpw(
    password.encode('utf-8'),
    user.password.encode('utf-8')
):
```

- [ ] **Step 1.6.7: Run tests — expect all PASSED**
```bash
pytest tests/test_auth.py -v
```
Expected output:
```
tests/test_auth.py::test_signup_hashes_password PASSED
tests/test_auth.py::test_login_with_correct_password PASSED
tests/test_auth.py::test_wrong_password PASSED

3 passed in ...
```

- [ ] **Step 1.6.8: Commit**
```bash
git add app.py tests/conftest.py tests/test_auth.py tests/__init__.py
git commit -m "feat: hash passwords with bcrypt on signup, verify on login"
```

---

### Task 1.7: Add preferred_skills to Job Model

**Files:**
- Create: `tests/test_models.py`
- Modify: `models.py`
- Modify: `init_db.py`
- Modify: `app.py` (any reference to `job.skills` → `job.required_skills`)

- [ ] **Step 1.7.1: Write test_models.py (tests must FAIL at this point)**

Create `E:\Projects\Intelligent job matching website\tests\test_models.py`:
```python
from models import Job, User, db


def test_job_has_required_skills_field(app):
    with app.app_context():
        assert hasattr(Job, 'required_skills'), \
            "Job model must have a 'required_skills' column"


def test_job_has_preferred_skills_field(app):
    with app.app_context():
        assert hasattr(Job, 'preferred_skills'), \
            "Job model must have a 'preferred_skills' column"


def test_job_preferred_skills_defaults_to_empty(app):
    with app.app_context():
        employer = User(
            email='emp@test.com',
            password='x',
            name='Emp',
            role='employer'
        )
        db.session.add(employer)
        db.session.flush()
        job = Job(
            employer_id=employer.id,
            position='Dev',
            company='Co',
            location='BKK',
            description='desc'
        )
        db.session.add(job)
        db.session.commit()
        assert job.preferred_skills == ''


def test_job_get_preferred_skills_list(app):
    with app.app_context():
        employer = User(
            email='emp2@test.com',
            password='x',
            name='Emp2',
            role='employer'
        )
        db.session.add(employer)
        db.session.flush()
        job = Job(
            employer_id=employer.id,
            position='Dev',
            company='Co',
            location='BKK',
            description='desc',
            preferred_skills='python, flask'
        )
        db.session.add(job)
        db.session.commit()
        result = job.get_preferred_skills_list()
        assert 'python' in result
        assert 'flask' in result


def test_job_to_dict_includes_both_skill_fields(app):
    with app.app_context():
        employer = User(
            email='emp3@test.com',
            password='x',
            name='Emp3',
            role='employer'
        )
        db.session.add(employer)
        db.session.flush()
        job = Job(
            employer_id=employer.id,
            position='Dev',
            company='Co',
            location='BKK',
            description='desc',
            required_skills='python',
            preferred_skills='docker'
        )
        db.session.add(job)
        db.session.commit()
        d = job.to_dict()
        assert 'required_skills' in d
        assert 'preferred_skills' in d
```

- [ ] **Step 1.7.2: Run tests — expect FAILED**
```bash
pytest tests/test_models.py -v
```
Expected output:
```
FAILED tests/test_models.py::test_job_has_required_skills_field
FAILED tests/test_models.py::test_job_has_preferred_skills_field
...
```

- [ ] **Step 1.7.3: Update models.py Job class**

Open `models.py`. In the `Job` model, replace the existing `skills` column and any existing `get_skills_list`/`set_skills_list`/`to_dict` methods with:

```python
# Replace:
#   skills = db.Column(db.Text, default='')
# With:
required_skills = db.Column(db.Text, default='')   # was: skills
preferred_skills = db.Column(db.Text, default='')  # new column

def get_skills_list(self):
    """Return required_skills as a Python list."""
    if not self.required_skills:
        return []
    return [s.strip() for s in self.required_skills.split(',') if s.strip()]

def set_skills_list(self, skills_list):
    """Accept a list or comma string and store in required_skills."""
    if isinstance(skills_list, list):
        self.required_skills = ', '.join(list(set(skills_list)))
    else:
        self.required_skills = skills_list

def get_preferred_skills_list(self):
    """Return preferred_skills as a Python list."""
    if not self.preferred_skills:
        return []
    return [s.strip() for s in self.preferred_skills.split(',') if s.strip()]

def to_dict(self):
    return {
        'id': self.id,
        'employer_id': self.employer_id,
        'position': self.position,
        'company': self.company,
        'location': self.location,
        'description': self.description,
        'required_skills': self.required_skills,
        'preferred_skills': self.preferred_skills,
        'salary_min': self.salary_min,
        'salary_max': self.salary_max,
        'job_type': self.job_type,
        'openings': self.openings,
        'deadline': self.deadline,
        'applicants': self.applicants,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'updated_at': self.updated_at.isoformat() if self.updated_at else None,
    }
```

- [ ] **Step 1.7.4: Update init_db.py — rename skills → required_skills**

Open `init_db.py`. Find every occurrence of `skills=` in the seed data and replace with `required_skills=`. For example:
```python
# Before:
Job(employer_id=1, position='...', skills='python, flask', ...)
# After:
Job(employer_id=1, position='...', required_skills='python, flask', preferred_skills='', ...)
```

- [ ] **Step 1.7.5: Update app.py — rename all job.skills references**

In `app.py`, do a project-wide replace of every occurrence of `job.skills` → `job.required_skills` and `'skills'` key in any job-building dict → `'required_skills'`. Also update the `POST /api/job-posts` handler to read the request field. The handler currently reads something like:
```python
skills = data.get('skills', '')
```
Change it to:
```python
required_skills = data.get('required_skills', data.get('skills', ''))
preferred_skills = data.get('preferred_skills', '')
```
And when constructing the `Job` object:
```python
job = Job(
    employer_id=employer.id,
    position=position,
    company=company,
    location=location,
    description=description,
    required_skills=required_skills,
    preferred_skills=preferred_skills,
    # ... other fields unchanged
)
```

Also update `calculate_match_score` (or equivalent) in `app.py` to use `job.get_skills_list()` instead of `job.skills.split(',')`.

- [ ] **Step 1.7.6: Run tests — expect all PASSED**
```bash
pytest tests/test_models.py -v
```
Expected output:
```
tests/test_models.py::test_job_has_required_skills_field PASSED
tests/test_models.py::test_job_has_preferred_skills_field PASSED
tests/test_models.py::test_job_preferred_skills_defaults_to_empty PASSED
tests/test_models.py::test_job_get_preferred_skills_list PASSED
tests/test_models.py::test_job_to_dict_includes_both_skill_fields PASSED

5 passed in ...
```

- [ ] **Step 1.7.7: Commit**
```bash
git add models.py init_db.py app.py tests/test_models.py
git commit -m "feat: rename skills->required_skills, add preferred_skills to Job model"
```

---

### Task 1.8: Fix api.js, Remove Debug Endpoints, Add /api/jobs Alias

**Files:**
- Modify: `app.py`
- Modify: `frontend/src/api.js`
- Create: `tests/test_endpoints.py`

- [ ] **Step 1.8.1: Write test_endpoints.py (tests must FAIL at this point)**

Create `E:\Projects\Intelligent job matching website\tests\test_endpoints.py`:
```python
def test_debug_users_endpoint_is_removed(client):
    res = client.get('/api/debug/users')
    assert res.status_code == 404, \
        f"Expected 404 but got {res.status_code} — debug endpoint must be deleted"


def test_debug_jobs_endpoint_is_removed(client):
    res = client.get('/api/debug/jobs')
    assert res.status_code == 404, \
        f"Expected 404 but got {res.status_code} — debug endpoint must be deleted"


def test_jobs_alias_returns_200(client):
    """GET /api/jobs must return 200 (the alias route)."""
    res = client.get('/api/jobs')
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
```

- [ ] **Step 1.8.2: Run tests — expect FAILED**
```bash
pytest tests/test_endpoints.py -v
```
Expected output:
```
FAILED tests/test_endpoints.py::test_debug_users_endpoint_is_removed
FAILED tests/test_endpoints.py::test_debug_jobs_endpoint_is_removed
FAILED tests/test_endpoints.py::test_jobs_alias_returns_200
```

- [ ] **Step 1.8.3: Remove debug endpoints from app.py**

In `app.py`, find and delete these two route handlers entirely:

```python
@app.route('/api/debug/users', methods=['GET'])
def debug_users():
    ...  # entire function body
```

```python
@app.route('/api/debug/jobs', methods=['GET'])
def debug_jobs():
    ...  # entire function body
```

- [ ] **Step 1.8.4: Add /api/jobs alias route to app.py**

In `app.py`, find the `GET /api/job-posts` handler. It will look like:
```python
@app.route('/api/job-posts', methods=['GET'])
def get_job_posts():
    ...
```

Immediately after the closing of that function, add an alias route that calls the same function:
```python
@app.route('/api/jobs', methods=['GET'])
def get_jobs_alias():
    """Alias for /api/job-posts — kept for frontend compatibility."""
    return get_job_posts()
```

- [ ] **Step 1.8.5: Update frontend/src/api.js**

Open `frontend/src/api.js`. Apply these two changes:

1. Rename `fetchJobs` to `fetchJobPosts` and update the URL:
```js
// Before:
export async function fetchJobs() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/jobs', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
}

// After:
export async function fetchJobPosts() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/job-posts', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
}
```

2. Add a new function for the upcoming match endpoint (Sprint 2):
```js
export async function fetchJobMatches() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/jobs/matches', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
}
```

- [ ] **Step 1.8.6: Update any component that called fetchJobs**

Search `frontend/src/` for any import or call of `fetchJobs` and rename to `fetchJobPosts`. For example in `Jobs.jsx` or similar:
```js
// Before:
import { fetchJobs } from '../api';
// ...
const jobs = await fetchJobs();

// After:
import { fetchJobPosts } from '../api';
// ...
const jobs = await fetchJobPosts();
```

- [ ] **Step 1.8.7: Run tests — expect all PASSED**
```bash
pytest tests/test_endpoints.py -v
```
Expected output:
```
tests/test_endpoints.py::test_debug_users_endpoint_is_removed PASSED
tests/test_endpoints.py::test_debug_jobs_endpoint_is_removed PASSED
tests/test_endpoints.py::test_jobs_alias_returns_200 PASSED

3 passed in ...
```

- [ ] **Step 1.8.8: Run full test suite to confirm no regressions**
```bash
pytest tests/ -v
```
Expected output:
```
tests/test_auth.py::test_signup_hashes_password PASSED
tests/test_auth.py::test_login_with_correct_password PASSED
tests/test_auth.py::test_login_with_wrong_password PASSED
tests/test_models.py::test_job_has_required_skills_field PASSED
tests/test_models.py::test_job_has_preferred_skills_field PASSED
tests/test_models.py::test_job_preferred_skills_defaults_to_empty PASSED
tests/test_models.py::test_job_get_preferred_skills_list PASSED
tests/test_models.py::test_job_to_dict_includes_both_skill_fields PASSED
tests/test_endpoints.py::test_debug_users_endpoint_is_removed PASSED
tests/test_endpoints.py::test_debug_jobs_endpoint_is_removed PASSED
tests/test_endpoints.py::test_jobs_alias_returns_200 PASSED

11 passed in ...
```

- [ ] **Step 1.8.9: Commit**
```bash
git add app.py frontend/src/api.js tests/test_endpoints.py
git commit -m "feat: remove debug endpoints, add /api/jobs alias, fix api.js fetchJobPosts"
```

---

## Sprint 1 Completion Checklist

- [ ] `backend/`, `jobs.py`, `matcher.py`, `interpreter.py`, `database.db` are deleted from the repo
- [ ] `.env` is present locally but excluded by `.gitignore`
- [ ] `.env.example` is committed
- [ ] `requirements.txt` no longer contains `PyPDF2`; contains `bcrypt`, `python-dotenv`, `pytest`
- [ ] `frontend/webpack.config.js` proxies `/api` and `/uploads` to port 5000
- [ ] `app.py` reads DB_URI, SECRET_KEY, UPLOAD_FOLDER from environment
- [ ] Passwords are stored as bcrypt hashes (`$2b$...`)
- [ ] `Job` model has `required_skills` and `preferred_skills` columns
- [ ] `GET /api/debug/users` and `GET /api/debug/jobs` return 404
- [ ] `GET /api/jobs` returns 200 (alias)
- [ ] `frontend/src/api.js` exports `fetchJobPosts` (not `fetchJobs`) and `fetchJobMatches`
- [ ] All 11 tests pass: `pytest tests/ -v`
