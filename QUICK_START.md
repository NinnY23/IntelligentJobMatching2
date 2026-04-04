# Quick Start Guide - Database Setup

## TL;DR (Quick Setup)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Download spaCy model (required for NLP)
python -m spacy download en_core_web_sm

# Initialize database with sample data
python init_db.py --seed

# Start the server
python app.py
```

Server runs on `http://localhost:5000`

---

## What Was Changed

### Before
- In-memory Python dictionaries: `users_db`, `job_posts_db`
- Data lost on restart
- No persistence

### After
- **SQLite database** stored in `database.db`
- **Flask-SQLAlchemy** ORM for database operations
- **Two models**: `User` and `Job` with One-to-Many relationship
- **Persistent data** across restarts

---

## Database Models

### User Model
```
Fields: id, email, password, name, phone, location, bio, skills, created_at, updated_at
Skills: Stored as comma-separated string
```

### Job Model
```
Fields: id, employer_id, position, company, location, description, 
        skills, salary_min, salary_max, job_type, openings, deadline, 
        applicants, created_at, updated_at
Relationship: Many jobs → One employer (User)
```

---

## Common Commands

### Create empty database
```bash
python init_db.py
```

### Create database with 3 users + 3 sample jobs
```bash
python init_db.py --seed
```

### Reset database (start fresh)
```bash
rm database.db
python init_db.py --seed
```

### Check database contents (debug)
```bash
# Using Python sqlite3
sqlite3 backend/database.db
sqlite> SELECT * FROM users;
sqlite> SELECT * FROM jobs;
sqlite> .quit
```

---

## API Endpoints (All Working)

### Authentication
- `POST /api/signup` - Create new account
- `POST /api/login` - Login user
- `POST /api/forgot-password` - Password reset

### User Profile
- `GET /api/profile` - Get profile (auth required)
- `PUT /api/profile` - Update profile (auth required)

### Resume Parsing
- `POST /api/upload-resume` - Upload PDF resume (auth required)
- `POST /api/parse-resume-text` - Parse resume text (auth required)

### Job Management
- `POST /api/job-posts` - Create job post (auth required)
- `GET /api/job-posts` - Get all jobs

### Debug
- `GET /api/debug/users` - View all users
- `GET /api/debug/jobs` - View all jobs

---

## Skills Field

Skills are stored as a **comma-separated string** in the database:
```
"Python, JavaScript, React, Docker, AWS"
```

The User and Job models have helper methods:

```python
# Get skills as a list
skills_list = user.get_skills_list()  # ['Python', 'JavaScript', ...]

# Set skills from a list (auto-deduplicates)
user.set_skills_list(['Python', 'JavaScript', 'Python'])  
# Stored as: "Python, JavaScript"

# Direct access
user.skills = 'Python, React, Docker'
```

---

## Sample Data (from --seed)

### Users
1. **john@example.com** - Full-stack developer
2. **jane@example.com** - Data scientist
3. **employer@company.com** - Hiring manager

### Jobs (all posted by employer@company.com)
1. Senior Python Developer (3 openings)
2. React Frontend Engineer (2 openings)
3. Data Scientist (1 opening)

---

## Testing the API

### Create Account
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123","name":"Test User"}'
```

### Login
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
```

### Get Profile (using token from login response)
```bash
curl -X GET http://localhost:5000/api/profile \
  -H "Authorization: Bearer token_test@example.com_1234567890"
```

### View All Jobs
```bash
curl -X GET http://localhost:5000/api/job-posts
```

---

## Database File

Location: `backend/database.db`

Size: Typically < 100KB for development

To backup:
```bash
cp backend/database.db backend/database.backup.db
```

---

## Frontend Changes

**No frontend changes needed!** 

The API responses are identical to the in-memory version:
- Same response formats
- Same HTTP status codes
- Same error messages

Frontend will work exactly as before.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask_sqlalchemy'"
```bash
pip install -r requirements.txt
```

### "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### "database is locked"
- Close other connections/editors
- Restart Flask

### "Foreign key constraint failed" (when creating jobs)
- Ensure user exists in database
- Use valid employer_id from existing user

### Want to see raw database?
```bash
sqlite3 database.db
SELECT * FROM users;
SELECT * FROM jobs;
.exit
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `models.py` | User and Job model definitions |
| `app.py` | Flask app with SQLAlchemy (database queries) |
| `init_db.py` | Initialize database + optional seeding |
| `database.db` | SQLite database file (auto-created) |
| `DATABASE_GUIDE.md` | Detailed documentation |
| `requirements.txt` | Python dependencies (includes SQLAlchemy) |

---

## Next Steps

1. ✅ Run `pip install -r requirements.txt`
2. ✅ Run `python -m spacy download en_core_web_sm`
3. ✅ Run `python init_db.py --seed`
4. ✅ Run `python app.py`
5. ✅ Test with frontend at `http://localhost:3000`

Done! Your data now persists in the SQLite database! 🎉
