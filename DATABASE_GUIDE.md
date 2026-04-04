# SQLAlchemy Database Integration Guide

## Overview

This document explains the migration from in-memory storage to persistent database using Flask-SQLAlchemy with SQLite.

## What Changed

### Before (In-Memory)
```python
users_db = {}          # Dictionary storing users
job_posts_db = {}      # Dictionary storing jobs
reset_tokens = {}      # Dictionary storing reset tokens
```

### After (SQLAlchemy + SQLite)
```python
# SQLite file-based database
database.db            # Created automatically in the backend directory

# Models
User model            # Represents users table
Job model             # Represents jobs table with foreign key to User
```

## Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- Flask==2.3.0
- Flask-SQLAlchemy==3.1.1
- SQLAlchemy==2.0.23
- Plus all other existing dependencies

### 2. Initialize the Database

**Option A: Create empty database**
```bash
python init_db.py
```

This creates the SQLite database file and all required tables.

**Option B: Create database with sample data**
```bash
python init_db.py --seed
```

Creates tables and seeds with 3 sample users and 3 sample job postings.

### 3. Start the Application

```bash
python app.py
```

The Flask server starts on `http://localhost:5000`. The database file `database.db` is automatically created if it doesn't exist.

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    location VARCHAR(120),
    bio TEXT,
    skills TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

**Fields:**
- `id`: Auto-incrementing primary key
- `email`: Unique user email (indexed for faster queries)
- `password`: User password (plaintext - should use bcrypt in production)
- `name`: User's full name
- `phone`: Phone number (optional)
- `location`: Location/city (optional)
- `bio`: User biography (optional)
- `skills`: Comma-separated skills string
- `created_at`: Account creation timestamp
- `updated_at`: Last profile update timestamp

### Jobs Table

```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employer_id INTEGER NOT NULL,
    position VARCHAR(120) NOT NULL,
    company VARCHAR(120) NOT NULL,
    location VARCHAR(120) NOT NULL,
    description TEXT NOT NULL,
    skills TEXT,
    salary_min VARCHAR(50),
    salary_max VARCHAR(50),
    job_type VARCHAR(50),
    openings INTEGER,
    deadline VARCHAR(50),
    applicants INTEGER,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (employer_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Fields:**
- `id`: Auto-incrementing primary key
- `employer_id`: Foreign key referencing users.id (who posted the job)
- `position`: Job title/position name
- `company`: Company name
- `location`: Job location
- `description`: Full job description
- `skills`: Comma-separated required skills
- `salary_min`: Minimum salary
- `salary_max`: Maximum salary
- `job_type`: Type of job (Full-time, Part-time, etc.)
- `openings`: Number of open positions
- `deadline`: Application deadline
- `applicants`: Number of applicants (counter)
- `created_at`: Job posting creation timestamp
- `updated_at`: Last update timestamp

### Relationships

**One-to-Many: User → Job**
- One user (employer) can create many job posts
- When a user is deleted, all their job posts are automatically deleted (CASCADE)
- Access jobs of a user: `user.job_posts`

## Key Implementation Details

### Skills Handling

Skills are stored as **comma-separated strings** in the database:
```
"Python, JavaScript, React, Docker, AWS"
```

**Python Model Methods:**
```python
user = User.query.get(1)

# Get skills as list
skills_list = user.get_skills_list()  # ['Python', 'JavaScript', ...]

# Set skills from list
user.set_skills_list(['Python', 'React', 'Docker'])  # Auto-deduplicates

# Direct access
user.skills = 'Python, React, Docker'
```

### To_dict() Methods

Both models have `to_dict()` methods for easy JSON serialization:

```python
user = User.query.get(1)
print(user.to_dict())  # Returns dictionary for JSON response

job = Job.query.get(1)
print(job.to_dict())   # Returns dictionary including employer_email
```

## API Compatibility

All existing API endpoints work exactly the same:
- Same request/response formats
- Same HTTP status codes
- Same error messages
- Database is transparent to the frontend

## Data Persistence

Unlike in-memory storage, data now persists across:
- Server restarts
- Application crashes
- Multiple deployments

## Migration Notes

### From In-Memory to Database

The application automatically handles the transition:

1. **First Run**: If `database.db` doesn't exist, SQLAlchemy creates it
2. **Existing Data**: In-memory data is lost (use `init_db.py --seed` for sample data)
3. **Authentication**: Token format remains the same (email extraction works identically)

### Backwards Compatibility

The database implementation maintains 100% API compatibility with the in-memory version, so no frontend changes are needed.

## Database Transactions

The application uses database transactions to ensure data consistency:

```python
try:
    user = User(email=email, ...)
    db.session.add(user)
    db.session.commit()  # Changes saved to database
except Exception as e:
    db.session.rollback()  # Undo changes on error
```

## Querying Examples

### Find user by email
```python
user = User.query.filter_by(email='john@example.com').first()
```

### Get all jobs
```python
jobs = Job.query.all()
```

### Get jobs by employer
```python
user = User.query.get(1)
user_jobs = user.job_posts.all()  # Uses relationship
```

### Filter jobs by location
```python
jobs = Job.query.filter_by(location='Austin, TX').all()
```

### Count jobs
```python
total_jobs = Job.query.count()
```

## Production Considerations

### TODO for Production:
1. **Password Security**: Replace plaintext with bcrypt hashing
2. **Database**: Migrate from SQLite to PostgreSQL for production
3. **Environment Variables**: Store database URL in .env
4. **Backups**: Implement regular database backups
5. **Migration Tool**: Use Alembic for schema changes
6. **Connection Pooling**: Configure SQLAlchemy connection pool

### Production Configuration Example:
```python
# Use PostgreSQL instead of SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# Configure connection pool
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

## Troubleshooting

### Error: "database.db is locked"
- Close other connections to the database
- Restart the Flask application

### Error: "Foreign key constraint failed"
- Ensure employer_id references an existing user
- Check job is assigned to a valid user before saving

### Missing `en_core_web_sm` spaCy model
```bash
python -m spacy download en_core_web_sm
```

### Reset Database
```bash
# Delete the database file
rm database.db

# Reinitialize
python init_db.py --seed
```

## Files Overview

- `models.py` - User and Job model definitions
- `app.py` - Flask application with SQLAlchemy integration
- `init_db.py` - Database initialization and seeding script
- `database.db` - SQLite database file (created after first run)

## Next Steps

1. Run `python init_db.py --seed` to create database with sample data
2. Start the Flask app with `python app.py`
3. Test endpoints with curl, Postman, or the frontend
4. Review `models.py` to understand the database schema
