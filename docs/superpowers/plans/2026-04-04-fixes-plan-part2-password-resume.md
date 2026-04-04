# Part 2: Forgot Password & Resume Auto-Populate

[Back to plan index](2026-04-04-fixes-and-features-plan-index.md)

---

## Task 3: Implement Forgot / Reset Password Flow

**Files:**
- Modify: `app.py:273-295` (forgot_password endpoint)
- Modify: `frontend/src/ForgotPassword.jsx`
- Modify: `frontend/src/App.jsx`
- Create: `frontend/src/pages/ResetPassword.jsx`
- Create: `tests/test_password_reset.py`

### Step 1: Write failing tests for password reset

- [ ] **Create tests/test_password_reset.py**

```python
import json


def test_forgot_password_generates_token(client):
    """POST /api/forgot-password should log a reset token for existing user."""
    # Create user first
    client.post('/api/signup', json={
        'email': 'reset@test.com', 'password': 'oldpass',
        'name': 'Reset User', 'role': 'employee'
    })
    res = client.post('/api/forgot-password', json={'email': 'reset@test.com'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'message' in data
    # Response should include the token in dev mode
    assert 'reset_token' in data


def test_forgot_password_nonexistent_email(client):
    """Should return 200 even for unknown email (security best practice)."""
    res = client.post('/api/forgot-password', json={'email': 'nobody@test.com'})
    assert res.status_code == 200
    assert 'reset_token' not in res.get_json()


def test_reset_password_success(client):
    """POST /api/reset-password with valid token should change password."""
    # Create user
    client.post('/api/signup', json={
        'email': 'reset2@test.com', 'password': 'oldpass',
        'name': 'Reset User 2', 'role': 'employee'
    })
    # Request reset
    res = client.post('/api/forgot-password', json={'email': 'reset2@test.com'})
    token = res.get_json()['reset_token']

    # Reset password
    res = client.post('/api/reset-password', json={
        'token': token,
        'new_password': 'newpass123'
    })
    assert res.status_code == 200

    # Login with new password should succeed
    res = client.post('/api/login', json={
        'email': 'reset2@test.com', 'password': 'newpass123'
    })
    assert res.status_code == 200

    # Login with old password should fail
    res = client.post('/api/login', json={
        'email': 'reset2@test.com', 'password': 'oldpass'
    })
    assert res.status_code == 401


def test_reset_password_invalid_token(client):
    """Invalid token should return 400."""
    res = client.post('/api/reset-password', json={
        'token': 'bogus-token',
        'new_password': 'newpass'
    })
    assert res.status_code == 400


def test_reset_token_single_use(client):
    """Token should be invalidated after use."""
    client.post('/api/signup', json={
        'email': 'reset3@test.com', 'password': 'oldpass',
        'name': 'Reset User 3', 'role': 'employee'
    })
    res = client.post('/api/forgot-password', json={'email': 'reset3@test.com'})
    token = res.get_json()['reset_token']

    # First use — success
    res = client.post('/api/reset-password', json={
        'token': token, 'new_password': 'newpass1'
    })
    assert res.status_code == 200

    # Second use — should fail
    res = client.post('/api/reset-password', json={
        'token': token, 'new_password': 'newpass2'
    })
    assert res.status_code == 400
```

- [ ] **Run tests to verify they fail**

```bash
pytest tests/test_password_reset.py -v
```

Expected: FAIL — `/api/reset-password` endpoint doesn't exist, forgot-password doesn't return `reset_token`.

### Step 2: Implement backend password reset

- [ ] **Add password_resets storage near the top of app.py**

After the `EDUCATION_KEYWORDS` list (around line 36), add:

```python
# In-memory store for password reset tokens {token: {email, expires_at}}
password_resets = {}
```

- [ ] **Replace the forgot_password endpoint**

Replace the entire `forgot_password` function (lines 273-295) with:

```python
@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.json
        email = data.get('email')

        if not email:
            return jsonify({"message": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            # Don't reveal if email exists
            return jsonify({"message": "If the email exists, a reset link has been sent"}), 200

        # Generate secure reset token with 1-hour expiry
        import secrets
        reset_token = secrets.token_urlsafe(32)
        password_resets[reset_token] = {
            'email': email,
            'expires_at': datetime.utcnow() + timedelta(hours=1)
        }

        # Log token to console (simulated email in dev mode)
        print(f"\n{'='*50}")
        print(f"PASSWORD RESET TOKEN for {email}")
        print(f"Token: {reset_token}")
        print(f"Reset URL: http://localhost:3000/reset-password?token={reset_token}")
        print(f"Expires: {password_resets[reset_token]['expires_at'].isoformat()}")
        print(f"{'='*50}\n")

        return jsonify({
            "message": "If the email exists, a reset link has been sent",
            "reset_token": reset_token  # Included for dev/testing — remove in production
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
```

- [ ] **Add the reset-password endpoint**

Add this new endpoint right after the `forgot_password` function:

```python
@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('new_password')

        if not token or not new_password:
            return jsonify({"message": "Token and new password are required"}), 400

        if len(new_password) < 4:
            return jsonify({"message": "Password must be at least 4 characters"}), 400

        # Validate token
        reset_data = password_resets.get(token)
        if not reset_data:
            return jsonify({"message": "Invalid or expired reset token"}), 400

        if datetime.utcnow() > reset_data['expires_at']:
            del password_resets[token]
            return jsonify({"message": "Reset token has expired"}), 400

        # Find user and update password
        user = User.query.filter_by(email=reset_data['email']).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        user.password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        db.session.commit()

        # Invalidate token (single use)
        del password_resets[token]

        return jsonify({"message": "Password reset successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
```

- [ ] **Run tests**

```bash
pytest tests/test_password_reset.py -v
```

Expected: All 5 tests PASS.

### Step 3: Update frontend ForgotPassword.jsx

- [ ] **Update ForgotPassword.jsx success message**

In `frontend/src/ForgotPassword.jsx`, change the hardcoded URL on line 18 from:
```javascript
const response = await fetch('http://localhost:5000/api/forgot-password', {
```
to:
```javascript
const response = await fetch('/api/forgot-password', {
```

And change the success message on line 40 from:
```javascript
setSuccess('Password reset link has been sent to your email. Please check your inbox.');
```
to:
```javascript
setSuccess('Password reset link has been generated. In development mode, check the server console for the reset URL.');
```

### Step 4: Create ResetPassword.jsx

- [ ] **Create frontend/src/pages/ResetPassword.jsx**

```jsx
// src/pages/ResetPassword.jsx
import React, { useState } from 'react';
import '../components/AuthCard.css';

export default function ResetPassword({ onSwitchToLogin }) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // Get token from URL query params
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!token) {
      setError('Missing reset token. Please use the link from the reset email.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 4) {
      setError('Password must be at least 4 characters.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || 'Reset failed');
      }

      setSuccess('Password reset successfully! You can now sign in with your new password.');
      setPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(err.message || 'Failed to reset password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">JobMatch<span>AI</span></div>
        <h2 className="auth-title">Set New Password</h2>
        <p className="auth-subtitle">Enter your new password below</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="password">New Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter new password"
              required
              minLength={4}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirm-password">Confirm Password</label>
            <input
              id="confirm-password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              required
              minLength={4}
            />
          </div>

          {error && <p className="form-error" role="alert">{error}</p>}
          {success && (
            <p className="form-error" style={{ color: 'var(--color-success, #16a34a)', background: 'var(--color-success-light, #f0fdf4)' }} role="status">
              {success}
            </p>
          )}

          <button type="submit" disabled={loading} className="btn-primary auth-submit">
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>

        <div className="auth-footer">
          <button onClick={onSwitchToLogin}>Back to Sign In</button>
        </div>
      </div>
    </div>
  );
}
```

### Step 5: Add route to App.jsx

- [ ] **Add ResetPassword import and route**

In `frontend/src/App.jsx`, add import after the ForgotPassword import (line 8):
```javascript
import ResetPassword from './pages/ResetPassword';
```

In the unauthenticated routes block (around line 109), add before the `<Route path="*"` catch-all:
```jsx
<Route path="/reset-password" element={<ResetPassword onSwitchToLogin={() => navigate('/login')} />} />
```

### Step 6: Commit

- [ ] **Commit password reset feature**

```bash
cd "E:/Projects/Intelligent job matching website"
git add app.py tests/test_password_reset.py frontend/src/ForgotPassword.jsx frontend/src/pages/ResetPassword.jsx frontend/src/App.jsx
git commit -m "feat: implement forgot/reset password flow

Simulated flow: generates secure token, logs reset URL to console.
Token expires in 1 hour and is single-use. Adds ResetPassword page."
```

---

## Task 4: Resume Auto-Populate Profile

**Files:**
- Modify: `app.py:365-426` (upload_resume endpoint)
- Modify: `frontend/src/Profile.jsx`

### Step 1: Write failing test for resume auto-populate

- [ ] **Add test to tests/test_profile.py** (create if not exists)

```python
import io


def test_resume_upload_populates_profile_fields(client, seeker_token):
    """Resume upload should populate empty profile fields, not just skills."""
    # Create a fake PDF-like content (the test won't actually parse PDF,
    # but we test the profile update logic via parse-resume-text endpoint)
    res = client.post('/api/parse-resume-text', json={
        'resumeText': '''John Smith
john@example.com
+1-555-123-4567
Bachelor of Science in Computer Science from KMITL
3 years experience in Python, Flask, React development
Skills: Python, JavaScript, React, Flask, SQL'''
    }, headers={'Authorization': f'Bearer {seeker_token}'})

    assert res.status_code == 200
    data = res.get_json()

    # Check that profile was populated
    user = data['user']
    assert 'python' in user['skills'].lower() or 'Python' in user['skills']

    # Now fetch profile to verify fields were saved
    profile_res = client.get('/api/profile',
                             headers={'Authorization': f'Bearer {seeker_token}'})
    profile = profile_res.get_json()['user']

    # Fields populated count should be in response
    assert 'fields_populated' in data
```

- [ ] **Run test to verify it fails**

```bash
pytest tests/test_profile.py::test_resume_upload_populates_profile_fields -v
```

Expected: FAIL — `fields_populated` not in response.

### Step 2: Update upload_resume endpoint to save profile fields

- [ ] **Modify the upload_resume endpoint in app.py**

Find the section in `upload_resume` (around line 405-410) where it currently only updates skills:

```python
        # Update user's skills
        existing_skills = user.get_skills_list()
        all_skills = list(set(existing_skills + extracted_skills))
        user.set_skills_list(all_skills)

        db.session.commit()
```

Replace with:

```python
        # Update user's skills
        existing_skills = user.get_skills_list()
        all_skills = list(set(existing_skills + extracted_skills))
        user.set_skills_list(all_skills)

        # Auto-populate empty profile fields from resume
        fields_populated = 0
        if extracted_name and not user.name.strip():
            user.name = extracted_name
            fields_populated += 1
        if extracted_phone and not user.phone.strip():
            user.phone = str(extracted_phone)
            fields_populated += 1
        if extracted_education and not user.education.strip():
            user.education = '; '.join(extracted_education)
            fields_populated += 1

        db.session.commit()
```

And update the return jsonify to include `fields_populated`:

```python
        return jsonify({
            "message": "Resume parsed successfully",
            "resume_data": {
                "name": extracted_name,
                "email": extracted_email,
                "phone": extracted_phone,
                "skills": extracted_skills,
                "education": extracted_education
            },
            "extracted_skills": extracted_skills,
            "fields_populated": fields_populated,
            "user": user.to_dict()
        }), 200
```

- [ ] **Do the same for parse_resume_text endpoint**

Find the same pattern in `parse_resume_text` (around line 460-466) and apply the identical changes:

```python
        # Update user's skills
        existing_skills = user.get_skills_list()
        all_skills = list(set(existing_skills + extracted_skills))
        user.set_skills_list(all_skills)

        # Auto-populate empty profile fields from resume
        fields_populated = 0
        if extracted_name and not user.name.strip():
            user.name = extracted_name
            fields_populated += 1
        if extracted_phone and not user.phone.strip():
            user.phone = str(extracted_phone)
            fields_populated += 1
        if extracted_education and not user.education.strip():
            user.education = '; '.join(extracted_education)
            fields_populated += 1

        db.session.commit()

        return jsonify({
            "message": "Resume text parsed successfully",
            "resume_data": {
                "name": extracted_name,
                "email": extracted_email,
                "phone": extracted_phone,
                "skills": extracted_skills,
                "education": extracted_education
            },
            "extracted_skills": extracted_skills,
            "fields_populated": fields_populated,
            "user": user.to_dict()
        }), 200
```

### Step 3: Run tests

- [ ] **Run tests**

```bash
pytest tests/test_profile.py -v
```

Expected: PASS.

### Step 4: Update Profile.jsx to refresh after resume upload

- [ ] **Update Profile.jsx resume upload handler**

In `frontend/src/Profile.jsx`, find the resume upload handler. Look for any section that calls `/api/upload-resume` or `/api/parse-resume-text`. After a successful response, add logic to refresh form fields:

Find the existing fetch call for resume upload (search for `upload-resume` in Profile.jsx). After the success response, add:

```javascript
      // Refresh form fields from populated profile
      const updatedUser = data.user;
      setFormData({
        name: updatedUser.name || '',
        email: updatedUser.email || '',
        phone: updatedUser.phone || '',
        location: updatedUser.location || '',
        bio: updatedUser.bio || '',
        profilePicture: updatedUser.profilePicture || '',
        education: updatedUser.education || '',
        experience: updatedUser.experience || '',
      });
      if (updatedUser.skills) {
        setSkills(updatedUser.skills.split(',').map(s => s.trim()).filter(Boolean));
      }
      localStorage.setItem('user', JSON.stringify(updatedUser));
      onUpdateProfile(updatedUser);

      const populated = data.fields_populated || 0;
      setSuccess(`Resume parsed! ${data.extracted_skills.length} skills found. ${populated > 0 ? `${populated} profile field(s) auto-populated.` : ''}`);
```

Note: If the resume upload UI doesn't exist yet in Profile.jsx, the user already has it — look for the file input with `accept=".pdf"`. The response handling just needs the refresh logic above added after the successful fetch.

### Step 5: Commit

- [ ] **Commit resume auto-populate**

```bash
cd "E:/Projects/Intelligent job matching website"
git add app.py frontend/src/Profile.jsx tests/test_profile.py
git commit -m "feat: auto-populate profile fields from resume upload

Resume parsing now saves name, phone, and education to the user
profile if those fields are currently empty. Addresses PDF req 2.1.1 #3."
```
