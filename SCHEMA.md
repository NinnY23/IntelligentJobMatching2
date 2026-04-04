# Database Schema Reference

## SQL Schema

### Users Table
```sql
CREATE TABLE users (
  id INTEGER NOT NULL, 
  email VARCHAR(120) NOT NULL, 
  password VARCHAR(255) NOT NULL, 
  name VARCHAR(120) NOT NULL, 
  phone VARCHAR(20), 
  location VARCHAR(120), 
  bio TEXT, 
  skills TEXT, 
  created_at DATETIME NOT NULL, 
  updated_at DATETIME NOT NULL, 
  PRIMARY KEY (id), 
  UNIQUE (email)
);

CREATE INDEX ix_users_email on users (email);
```

### Jobs Table
```sql
CREATE TABLE jobs (
  id INTEGER NOT NULL, 
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
  PRIMARY KEY (id), 
  FOREIGN KEY(employer_id) REFERENCES users (id) ON DELETE CASCADE
);
```

---

## Common SQL Queries

### Users

**Get all users**
```sql
SELECT * FROM users;
```

**Get user by email**
```sql
SELECT * FROM users WHERE email = 'john@example.com';
```

**Get user by ID**
```sql
SELECT * FROM users WHERE id = 1;
```

**Count users**
```sql
SELECT COUNT(*) FROM users;
```

**Get users by skill**
```sql
SELECT * FROM users WHERE skills LIKE '%Python%';
```

---

### Jobs

**Get all jobs**
```sql
SELECT * FROM jobs;
```

**Get jobs by employer**
```sql
SELECT * FROM jobs WHERE employer_id = 1;
```

**Get jobs by location**
```sql
SELECT * FROM jobs WHERE location = 'Austin, TX';
```

**Get jobs with specific skill requirement**
```sql
SELECT * FROM jobs WHERE skills LIKE '%Python%';
```

**Count jobs by company**
```sql
SELECT company, COUNT(*) as total 
FROM jobs 
GROUP BY company;
```

**Get most popular jobs (by applicant count)**
```sql
SELECT position, applicants 
FROM jobs 
ORDER BY applicants DESC 
LIMIT 10;
```

**Get jobs with salary range**
```sql
SELECT position, company, salary_min, salary_max 
FROM jobs 
WHERE salary_min >= 100000 
ORDER BY salary_min DESC;
```

---

### Relationships

**Get all jobs posted by a specific user**
```sql
SELECT j.* 
FROM jobs j 
JOIN users u ON j.employer_id = u.id 
WHERE u.email = 'john@example.com';
```

**Get employer details for a job**
```sql
SELECT u.name, u.email 
FROM users u 
JOIN jobs j ON u.id = j.employer_id 
WHERE j.id = 1;
```

**Get users and their job count**
```sql
SELECT u.name, u.email, COUNT(j.id) as job_count 
FROM users u 
LEFT JOIN jobs j ON u.id = j.employer_id 
GROUP BY u.id;
```

---

## Field Specifications

### User Fields

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| email | VARCHAR(120) | UNIQUE, NOT NULL | User's email (indexed) |
| password | VARCHAR(255) | NOT NULL | Plaintext (use bcrypt in production) |
| name | VARCHAR(120) | NOT NULL | User's full name |
| phone | VARCHAR(20) | OPTIONAL | Phone number |
| location | VARCHAR(120) | OPTIONAL | City/Location |
| bio | TEXT | OPTIONAL | User biography |
| skills | TEXT | OPTIONAL | Comma-separated skills list |
| created_at | DATETIME | NOT NULL | Auto-set on creation |
| updated_at | DATETIME | NOT NULL | Auto-updated on modification |

### Job Fields

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| employer_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to user who posted |
| position | VARCHAR(120) | NOT NULL | Job title |
| company | VARCHAR(120) | NOT NULL | Company name |
| location | VARCHAR(120) | NOT NULL | Job location |
| description | TEXT | NOT NULL | Full job description |
| skills | TEXT | OPTIONAL | Comma-separated required skills |
| salary_min | VARCHAR(50) | OPTIONAL | Minimum salary |
| salary_max | VARCHAR(50) | OPTIONAL | Maximum salary |
| job_type | VARCHAR(50) | OPTIONAL | Type (Full-time, Part-time, etc.) |
| openings | INTEGER | OPTIONAL | Number of open positions |
| deadline | VARCHAR(50) | OPTIONAL | Application deadline |
| applicants | INTEGER | OPTIONAL | Number of applicants |
| created_at | DATETIME | NOT NULL | Auto-set on creation |
| updated_at | DATETIME | NOT NULL | Auto-updated on modification |

---

## Indexes

Created indexes:
- `ix_users_email` - For fast email lookups during login/signup

---

## Data Types Summary

| SQLAlchemy | SQLite | Python |
|------------|--------|--------|
| Integer | INTEGER | int |
| String(120) | VARCHAR(120) | str |
| Text | TEXT | str |
| DateTime | DATETIME | datetime |

---

## Constraints & Relationships

### Primary Keys
- Users: `id` (auto-increment)
- Jobs: `id` (auto-increment)

### Foreign Keys
- Jobs.employer_id → Users.id
  - ON DELETE CASCADE (deletes all jobs when employer is deleted)

### Unique Constraints
- Users.email (only one account per email)

### Not Null Constraints
- Users: email, password, name, created_at, updated_at
- Jobs: employer_id, position, company, location, description, created_at, updated_at

---

## Migration from In-Memory

### Old (Dictionary) vs New (Database)

**Old Implementation:**
```python
users_db = {
    'john@example.com': {
        'email': 'john@example.com',
        'password': '123',
        'name': 'John',
        # ... more fields
    }
}
```

**New Implementation:**
```python
user = User(
    email='john@example.com',
    password='123',
    name='John',
    # ... more fields
)
db.session.add(user)
db.session.commit()

# Later, query:
user = User.query.filter_by(email='john@example.com').first()
```

---

## Performance Notes

### Optimization Tips

1. **Use indexes**
   - Email lookups are fast (indexed)
   - Location queries would benefit from index

2. **Limit large queries**
   ```python
   # Good: Limits results
   jobs = Job.query.limit(50).all()
   
   # Avoid: Returns all (slow on large dataset)
   jobs = Job.query.all()
   ```

3. **Lazy loading**
   - Related objects are loaded on access: `job.employer.name`
   - Use eager loading for bulk operations

---

## Backup & Restore

### Backup Database
```bash
cp backend/database.db backend/database.backup.db
```

### Restore Database
```bash
cp backend/database.backup.db backend/database.db
```

### Export to CSV
```bash
sqlite3 -header -csv backend/database.db \
  "SELECT * FROM users;" > users.csv
```

---

## Database Statistics

### Typical Sizes
- Empty database: ~20KB
- With 100 users: ~30KB
- With 1000 jobs: ~80KB

### Recommended for
- Development
- Testing
- Small-medium deployments (<1M records)

### For Production Consider
- PostgreSQL
- MySQL
- Cloud databases (Azure SQL, AWS RDS)

---

## Troubleshooting

### Foreign Key Constraint Error
```
IntegrityError: FOREIGN KEY constraint failed
```
**Solution:** Ensure employer_id references existing user before creating job

### Database Locked
```
OperationalError: database is locked
```
**Solution:** Close other connections, restart Flask

### Column Not Found
```
OperationalError: no such column: skills
```
**Solution:** Run `python init_db.py` to create tables with new schema

---

## Files Using Database

- `app.py` - Main file with all query operations
- `models.py` - Model definitions
- `init_db.py` - Database initialization
- `database.db` - The actual SQLite file
