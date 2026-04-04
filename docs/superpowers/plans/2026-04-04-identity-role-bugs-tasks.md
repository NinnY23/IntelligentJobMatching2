# Identity, Role & Application Bugs — Tasks

> See `2026-04-04-identity-role-bugs-overview.md` for root cause analysis.

---

### Task 1: Fix Seed Data — Set Roles and Add Sample Applications

**Problem:** `init_db.py` creates 3 users but never sets the `role` field. The model defaults to `'employee'`, so the "employer" seed user can't access any employer endpoints. Also, no sample applications exist, so even after fixing roles the applicant list is empty.

**Files:**
- Modify: `init_db.py`

- [ ] **Step 1: Add role to all seed users**

In `init_db.py`, the three User constructors (lines 53-81) don't pass `role`. Fix each:

For user1 (John Doe, line 53-61), add `role='employee'`:
```python
user1 = User(
    email='john@example.com',
    password=hashed_password,
    name='John Doe',
    phone='+1-234-567-8900',
    location='San Francisco, CA',
    bio='Full-stack developer with 5 years of experience',
    skills='Python, JavaScript, React, AWS, Docker',
    role='employee'
)
```

For user2 (Jane Smith, line 63-71), add `role='employee'`:
```python
user2 = User(
    email='jane@example.com',
    password=hashed_password,
    name='Jane Smith',
    phone='+1-345-678-9012',
    location='New York, NY',
    bio='Data scientist and ML engineer',
    skills='Python, Machine Learning, TensorFlow, SQL, Pandas',
    role='employee'
)
```

For user3 (Tech Company HR, line 73-81), add `role='employer'`:
```python
user3 = User(
    email='employer@company.com',
    password=hashed_password,
    name='Tech Company HR',
    phone='+1-456-789-0123',
    location='Austin, TX',
    bio='Hiring for tech positions',
    skills='Recruitment, HR, Tech',
    role='employer'
)
```

- [ ] **Step 2: Add sample applications to seed data**

After the job creation block (after line 138 `db.session.commit()`), add sample applications so the employer can see applicants:

```python
from models import Application

# Create sample applications so employer can see applicants
app1 = Application(job_id=job1.id, user_id=user1.id, status='pending')
app2 = Application(job_id=job2.id, user_id=user1.id, status='pending')
app3 = Application(job_id=job1.id, user_id=user2.id, status='shortlisted')
app4 = Application(job_id=job3.id, user_id=user2.id, status='pending')

db.session.add_all([app1, app2, app3, app4])

# Update applicant counts on jobs
job1.applicants = 2
job2.applicants = 1
job3.applicants = 1

db.session.commit()

print("\n✓ Sample applications created:")
print(f"  - John Doe applied to {job1.position} (pending)")
print(f"  - John Doe applied to {job2.position} (pending)")
print(f"  - Jane Smith applied to {job1.position} (shortlisted)")
print(f"  - Jane Smith applied to {job3.position} (pending)")
```

Also add the `Application` import at the top of the file. Change line 18:
```python
from models import User, Job
```
to:
```python
from models import User, Job, Application
```

- [ ] **Step 3: Verify the fix**

Run:
```bash
cd "E:/Projects/Intelligent job matching website"
python -c "
from app import app, db
from models import User
with app.app_context():
    db.drop_all()
    db.create_all()
    print('Tables recreated')
"
PYTHONIOENCODING=utf-8 python init_db.py --seed
```

Expected output should include "Sample applications created" and no errors.

Then verify roles are correct:
```bash
python -c "
from app import app, db
from models import User
with app.app_context():
    for u in User.query.all():
        print(f'{u.name}: role={u.role}')
"
```

Expected:
```
John Doe: role=employee
Jane Smith: role=employee
Tech Company HR: role=employer
```

- [ ] **Step 4: Commit**

```bash
git add init_db.py
git commit -m "fix(seed): set explicit roles on seed users and add sample applications

Seed users were created without role field, defaulting all 3 to
'employee'. The employer user could not access any employer endpoints.
Added role='employer' to the HR user and role='employee' to job seekers.
Also added 4 sample applications so the employer dashboard and
applicant list have data to display."
```

---

### Task 2: Add User Profile Refresh on App Mount

**Problem:** `App.jsx` reads `localStorage.getItem('user')` on mount and trusts it forever. If the data is stale from a previous session (different user), the wrong name/role is displayed. The fix is to validate the stored user against the server on mount.

**Files:**
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/api.js`

- [ ] **Step 1: Add a getProfile call to api.js (already exists — verify)**

Read `frontend/src/api.js` and confirm `getProfile()` exists. It does (lines 51-65):
```javascript
export async function getProfile() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/profile', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  handleAuthError(res);
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}
```

This returns `{ user: { id, name, email, role, ... } }`. No changes needed to api.js.

- [ ] **Step 2: Import getProfile in App.jsx**

In `frontend/src/App.jsx` line 18, change:
```javascript
import { fetchUnreadCount, logoutUser } from './api';
```
to:
```javascript
import { fetchUnreadCount, logoutUser, getProfile } from './api';
```

- [ ] **Step 3: Add server validation to the useEffect on mount**

In `frontend/src/App.jsx`, replace the first useEffect (lines 41-57):

```javascript
useEffect(() => {
  // Check if user is already logged in
  const token = localStorage.getItem('token');
  const savedUser = localStorage.getItem('user');

  if (token && savedUser) {
    try {
      setUser(JSON.parse(savedUser));
    } catch (err) {
      console.error('Error parsing saved user:', err);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  }

  setLoading(false);
}, []);
```

with:

```javascript
useEffect(() => {
  async function initUser() {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');

    if (!token) {
      setLoading(false);
      return;
    }

    // Show cached user immediately for fast UI
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        // ignore parse errors, server fetch below will correct
      }
    }

    // Validate against server — this is the source of truth
    try {
      const data = await getProfile();
      const freshUser = data.user;
      localStorage.setItem('user', JSON.stringify(freshUser));
      setUser(freshUser);
    } catch {
      // Token invalid or expired — clear session
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
    }

    setLoading(false);
  }

  initUser();
}, []);
```

**How this fixes the identity bug:**
1. On page load, if a token exists, it immediately shows cached user (fast)
2. Then it calls `GET /api/profile` with the token to get the REAL user from the database
3. If the token belongs to Ester, the server returns Ester's data — replacing any stale "John Doe" in localStorage
4. If the token is expired/invalid, it clears the session and redirects to login

- [ ] **Step 4: Verify the fix**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx webpack --mode development 2>&1 | tail -3`
Expected: Build succeeds.

Run tests: `cd "E:/Projects/Intelligent job matching website/frontend" && npx jest --verbose 2>&1 | tail -10`
Expected: All tests pass (tests mock fetch, so the new getProfile call won't affect them).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "fix(auth): validate user identity against server on page load

On mount, App.jsx now calls GET /api/profile to refresh the user object
from the server instead of blindly trusting localStorage. This fixes the
identity mismatch where logging in as Ester would show John Doe's name
if stale data remained in localStorage from a previous session."
```

---

### Task 3: Fix Profile.jsx Resume Parse — Wrong Object Saved

**Problem:** In `Profile.jsx` line 98, after parsing a resume, the code saves `updatedUser` to localStorage — but `updatedUser` is the full API response `{ user: {...}, extracted_skills: [...], fields_populated: 3 }`, not just the user object. This corrupts localStorage with the wrong shape.

**Files:**
- Modify: `frontend/src/Profile.jsx`

- [ ] **Step 1: Fix the resume parse handler**

In `frontend/src/Profile.jsx` line 98, change:
```javascript
localStorage.setItem('user', JSON.stringify(updatedUser));
```
to:
```javascript
// Note: updatedUser is already data.user (set on line 84), which is the user object
```

Wait — re-reading the code more carefully:

```javascript
// Line 81: const data = await parseResumeText(resumeText);
// Line 84: const updatedUser = data.user;
// Line 98: localStorage.setItem('user', JSON.stringify(updatedUser));
// Line 99: onUpdateProfile(updatedUser);
```

Actually `updatedUser` IS `data.user` — set on line 84. So line 98 saves the correct object.

BUT let's check what `parseResumeText` actually returns. Reading `api.js:190-206`:
```javascript
export async function parseResumeText(resumeText) {
  // ...
  return res.json();
}
```

And the backend endpoint — let me check what it returns:

Read `app.py` to find the `/api/parse-resume-text` endpoint response shape.

- [ ] **Step 2: Read the parse-resume-text endpoint to verify response shape**

Find and read the `/api/parse-resume-text` endpoint in `app.py`. Check what it returns.

If it returns `{ user: {...}, extracted_skills: [...], fields_populated: N }`, then:
- `data = await parseResumeText(resumeText)` → `data` = `{ user: {...}, extracted_skills: [...], fields_populated: N }`
- `const updatedUser = data.user` → `updatedUser` = user object ✓
- `localStorage.setItem('user', JSON.stringify(updatedUser))` → saves just the user ✓

If the response shape is different, fix accordingly.

The code on line 98 appears correct IF `data.user` is a clean user object. The real issue is that the **handleSubmit path** (line 64-65) does:
```javascript
const updatedUser = await updateProfile(payload);
localStorage.setItem('user', JSON.stringify(updatedUser.user));
```

Here `updateProfile()` returns the full `{ user: {...} }` response from `res.json()`, so `updatedUser.user` gets the nested user.

**Both paths look structurally correct** after re-analysis. The identity bug is primarily from Task 2 (stale localStorage on mount).

However, there IS a consistency issue: the two code paths in Profile.jsx use different variable naming conventions which is confusing but not buggy. No code change needed here.

- [ ] **Step 3: Skip — no bug in this path after careful analysis**

Mark this task as "verified — no change needed". The code paths are correct.

---

### Task 4: Fix Withdraw — Set Status Instead of Deleting

**Problem:** `app.py:845` does `db.session.delete(application)` which removes the row entirely. The frontend expects withdrawn applications to still appear with status='withdrawn'. After a refresh, withdrawn applications vanish.

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Change withdraw endpoint to set status instead of deleting**

In `app.py`, find the `withdraw_application` function (lines 829-847). Replace:

```python
@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
def withdraw_application(app_id):
    """Job seeker withdraws an application (not allowed when shortlisted)."""
    user, err = get_current_user_or_401()
    if err:
        return err

    application = Application.query.filter_by(id=app_id, user_id=user.id).first()
    if not application:
        return jsonify({"message": "Application not found"}), 404
    if application.status == 'shortlisted':
        return jsonify({"message": "Cannot withdraw a shortlisted application"}), 400

    job = Job.query.get(application.job_id)
    if job and (job.applicants or 0) > 0:
        job.applicants -= 1
    db.session.delete(application)
    db.session.commit()
    return jsonify({"message": "Application withdrawn"}), 200
```

with:

```python
@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
def withdraw_application(app_id):
    """Job seeker withdraws an application (not allowed when shortlisted)."""
    user, err = get_current_user_or_401()
    if err:
        return err

    application = Application.query.filter_by(id=app_id, user_id=user.id).first()
    if not application:
        return jsonify({"message": "Application not found"}), 404
    if application.status == 'shortlisted':
        return jsonify({"message": "Cannot withdraw a shortlisted application"}), 400
    if application.status == 'withdrawn':
        return jsonify({"message": "Application already withdrawn"}), 400

    job = Job.query.get(application.job_id)
    if job and (job.applicants or 0) > 0:
        job.applicants -= 1
    application.status = 'withdrawn'
    db.session.commit()
    return jsonify({"message": "Application withdrawn", "application": application.to_dict()}), 200
```

Changes:
1. Added guard for already-withdrawn applications
2. Changed `db.session.delete(application)` → `application.status = 'withdrawn'`
3. Return the updated application object in response

- [ ] **Step 2: Verify with existing tests**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v -k withdraw 2>&1 | tail -20`

If there are existing withdraw tests, they should now expect status change instead of deletion. Fix any failing tests to match the new behavior.

If no withdraw tests exist, verify manually:
```bash
python -c "
from app import app, db
from models import Application
with app.app_context():
    a = Application.query.first()
    if a:
        print(f'App {a.id}: status={a.status}')
    else:
        print('No applications found')
"
```

- [ ] **Step 3: Run full backend test suite**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v 2>&1 | tail -20`
Expected: All tests pass (or known pre-existing failures only).

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "fix(withdraw): set application status to 'withdrawn' instead of deleting row

The withdraw endpoint was using db.session.delete() which removed the
application entirely. After page refresh, withdrawn applications would
vanish from the My Applications list. Now sets status='withdrawn' so
the application persists and can be displayed with the correct status."
```

---

### Task 5: Fix Login.jsx — Use Centralized API Function (Optional Cleanup)

**Problem:** `Login.jsx` uses inline `fetch('/api/login')` instead of the `loginUser()` function from `api.js`. This is a consistency issue — not a bug — but it means Login doesn't benefit from the centralized `handleAuthError` handler.

**Files:**
- Modify: `frontend/src/Login.jsx`

- [ ] **Step 1: Update Login.jsx to use api.js loginUser**

In `frontend/src/Login.jsx`, add import at top:
```javascript
import { loginUser } from './api';
```

Replace the fetch block (lines 14-29):
```javascript
async function handleSubmit(e) {
  e.preventDefault();
  setError('');
  setLoading(true);
  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) { setError(data.message || 'Login failed'); return; }
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    onLoginSuccess(data.user);
  } catch {
    setError('Network error. Please try again.');
  } finally {
    setLoading(false);
  }
}
```

with:

```javascript
async function handleSubmit(e) {
  e.preventDefault();
  setError('');
  setLoading(true);
  try {
    const data = await loginUser(email, password);
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));
    onLoginSuccess(data.user);
  } catch (err) {
    setError(err.message || 'Login failed. Please try again.');
  } finally {
    setLoading(false);
  }
}
```

Wait — there's a problem. The current `loginUser` in `api.js` (lines 12-26) doesn't return error messages from the server:
```javascript
export async function loginUser(email, password) {
  const res = await fetch('/api/login', { ... });
  if (!res.ok) {
    throw new Error('Login failed');
  }
  return res.json();
}
```

It throws a generic "Login failed" instead of the server's specific message (like "Invalid email or password"). Fix `loginUser` in api.js first:

In `frontend/src/api.js`, replace lines 12-26:
```javascript
export async function loginUser(email, password) {
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    throw new Error('Login failed');
  }

  return res.json();
}
```

with:

```javascript
export async function loginUser(email, password) {
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.message || 'Login failed');
  }

  return res.json();
}
```

- [ ] **Step 2: Verify the fix**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx webpack --mode development 2>&1 | tail -3`
Expected: Build succeeds.

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx jest --verbose 2>&1 | tail -10`
Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/Login.jsx frontend/src/api.js
git commit -m "refactor(login): use centralized loginUser() from api.js

Login.jsx now uses the shared loginUser() function instead of inline
fetch. Also improved loginUser() to forward server error messages
instead of the generic 'Login failed'."
```

---

### Task 6: End-to-End Verification

**No code changes.** This task verifies the full workflow works.

- [ ] **Step 1: Reset and re-seed the database**

```bash
cd "E:/Projects/Intelligent job matching website"
python -c "
from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
    print('Tables recreated')
"
PYTHONIOENCODING=utf-8 python init_db.py --seed
```

- [ ] **Step 2: Start backend and frontend**

```bash
# Terminal 1:
cd "E:/Projects/Intelligent job matching website"
python app.py

# Terminal 2:
cd "E:/Projects/Intelligent job matching website/frontend"
npm start
```

- [ ] **Step 3: Test identity — login as different users**

1. Open browser, clear localStorage (DevTools → Application → Local Storage → Clear)
2. Login as `john@example.com` / `password123` → should see "John Doe" in navbar
3. Click Logout
4. Login as `jane@example.com` / `password123` → should see "Jane Smith" in navbar (NOT John Doe)
5. Refresh the page → should still show "Jane Smith" (server validates identity)

- [ ] **Step 4: Test employer flow — applicant visibility**

1. Login as `employer@company.com` / `password123`
2. Should land on Dashboard → verify it shows stats (3 jobs, 4 applicants, 1 shortlisted)
3. Navigate to My Jobs → should see 3 job postings
4. Click Applicants on "Senior Python Developer" → should see John Doe (pending) and Jane Smith (shortlisted)
5. Click Applicants on "React Frontend Engineer" → should see John Doe (pending)

- [ ] **Step 5: Test application withdraw**

1. Login as `john@example.com` / `password123`
2. Navigate to My Applications → should see 2 applications (pending)
3. Click Withdraw on one → confirm → should show as "withdrawn" (not disappear)
4. Refresh the page → withdrawn application should still be visible with "withdrawn" status

- [ ] **Step 6: Test new user signup**

1. Logout
2. Click "Create account"
3. Sign up as "Ester Test" / `ester@test.com` / `password123` / Job Seeker
4. Should see "Ester Test" in navbar
5. Navigate to Find Jobs → should see 3 jobs
6. Apply to one → navigate to My Applications → should see 1 pending application
7. Logout, login as `employer@company.com` → go to Applicants for that job → should see Ester Test
