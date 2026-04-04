# Part 1: JWT Authentication & Credentials to .env

[Back to plan index](2026-04-04-fixes-and-features-plan-index.md)

---

## Task 1: Replace Custom Tokens with JWT

**Files:**
- Modify: `requirements.txt`
- Modify: `app.py:1-20` (imports), `app.py:132-166` (require_role), `app.py:230-233` (signup token), `app.py:260-263` (login token), `app.py:297-322` (get_profile), `app.py:324-363` (update_profile), `app.py:365-426` (upload_resume), `app.py:428-482` (parse_resume_text), `app.py:488-543` (create_job_post), `app.py:562-610` (get_job_matches), `app.py:760-838` (applications), `app.py:979-989` (get_current_user)
- Test: `tests/conftest.py`, `tests/test_auth.py`

### Step 1: Add PyJWT to requirements.txt

- [ ] **Add PyJWT dependency**

Open `requirements.txt` and add after `bcrypt==4.0.1`:

```
PyJWT==2.8.0
```

Run:
```bash
pip install PyJWT==2.8.0
```

### Step 2: Write failing test for JWT token generation

- [ ] **Create test for JWT signup/login**

Add to `tests/test_auth.py` (or create if needed):

```python
import jwt

def test_signup_returns_jwt(client):
    res = client.post('/api/signup', json={
        'email': 'jwt@test.com', 'password': 'pass123',
        'name': 'JWT User', 'role': 'employee'
    })
    assert res.status_code == 201
    data = res.get_json()
    token = data['token']
    # Should be decodable as JWT
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded['email'] == 'jwt@test.com'
    assert decoded['role'] == 'employee'
    assert 'user_id' in decoded
    assert 'exp' in decoded


def test_login_returns_jwt(client):
    # First signup
    client.post('/api/signup', json={
        'email': 'jwt2@test.com', 'password': 'pass123',
        'name': 'JWT User 2', 'role': 'employee'
    })
    res = client.post('/api/login', json={
        'email': 'jwt2@test.com', 'password': 'pass123'
    })
    assert res.status_code == 200
    data = res.get_json()
    token = data['token']
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded['email'] == 'jwt2@test.com'
    assert 'exp' in decoded


def test_expired_token_returns_401(client):
    """Expired JWT should return 401 with 'Token expired' message."""
    import jwt as pyjwt
    from datetime import datetime, timedelta
    expired_token = pyjwt.encode(
        {'user_id': 999, 'email': 'x@x.com', 'role': 'employee',
         'exp': datetime.utcnow() - timedelta(hours=1)},
        'dev-secret',
        algorithm='HS256'
    )
    res = client.get('/api/profile',
                     headers={'Authorization': f'Bearer {expired_token}'})
    assert res.status_code == 401
    assert 'expired' in res.get_json()['message'].lower()
```

- [ ] **Run test to verify it fails**

```bash
cd "E:/Projects/Intelligent job matching website"
pytest tests/test_auth.py -v -k "jwt or expired"
```

Expected: FAIL — current tokens are not JWTs.

### Step 3: Implement JWT token generation and validation

- [ ] **Update imports in app.py**

At the top of `app.py`, after `import bcrypt`, add:

```python
import jwt as pyjwt
from datetime import timedelta
```

- [ ] **Replace generate_token with JWT encoding**

In `app.py`, find the signup endpoint (around line 233) where it says:
```python
        # Generate fake token
        token = f"token_{email}_{datetime.now().timestamp()}"
```

Replace with:
```python
        # Generate JWT token (24-hour expiry)
        token = pyjwt.encode(
            {
                'user_id': new_user.id,
                'email': new_user.email,
                'role': new_user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
```

- [ ] **Do the same for login endpoint**

In `app.py`, find the login endpoint (around line 263) where it says:
```python
        # Generate fake token
        token = f"token_{email}_{datetime.now().timestamp()}"
```

Replace with:
```python
        # Generate JWT token (24-hour expiry)
        token = pyjwt.encode(
            {
                'user_id': user.id,
                'email': user.email,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
```

- [ ] **Replace get_current_user to decode JWT**

In `app.py`, find `get_current_user` (around line 979-989) and replace the entire function:

```python
def get_current_user(request):
    """Extract user from JWT Bearer token. Returns User or None."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ')[1]
    try:
        payload = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return User.query.get(payload['user_id'])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None
```

- [ ] **Replace require_role decorator to decode JWT**

In `app.py`, find `require_role` (around line 138-166) and replace the inner function body:

```python
def require_role(required_role):
    """Decorator to restrict endpoint access by user role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"message": "Unauthorized"}), 401

            token = auth_header.split(' ')[1]
            try:
                payload = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            except pyjwt.ExpiredSignatureError:
                return jsonify({"message": "Token expired"}), 401
            except pyjwt.InvalidTokenError:
                return jsonify({"message": "Invalid token"}), 401

            user = User.query.get(payload.get('user_id'))
            if not user:
                return jsonify({"message": "User not found"}), 404

            if user.role != required_role:
                return jsonify({"message": f"Access denied. This endpoint requires '{required_role}' role"}), 403

            return f(user, *args, **kwargs)
        return decorated_function
    return decorator
```

- [ ] **Create a helper function for JWT decoding used by non-decorated endpoints**

Add this function right after `get_current_user`:

```python
def get_current_user_or_401():
    """Extract user from JWT. Returns (user, None) or (None, error_response)."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None, (jsonify({"message": "Unauthorized"}), 401)
    token = auth.split(' ')[1]
    try:
        payload = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except pyjwt.ExpiredSignatureError:
        return None, (jsonify({"message": "Token expired"}), 401)
    except pyjwt.InvalidTokenError:
        return None, (jsonify({"message": "Invalid token"}), 401)
    user = User.query.get(payload.get('user_id'))
    if not user:
        return None, (jsonify({"message": "User not found"}), 404)
    return user, None
```

- [ ] **Update all non-decorated endpoints that parse tokens manually**

Every endpoint that currently does this pattern:
```python
auth_header = request.headers.get('Authorization')
...
parts = token.split('_')
email = '_'.join(parts[1:-1])
user = User.query.filter_by(email=email).first()
```

Must be replaced with:
```python
user, err = get_current_user_or_401()
if err:
    return err
```

Endpoints to update (search for `parts = token.split('_')` in app.py):
1. `get_profile` (line ~300)
2. `update_profile` (line ~330)
3. `upload_resume` (line ~370)
4. `parse_resume_text` (line ~435)
5. `create_job_post` (line ~495)
6. `get_job_matches` (line ~565)
7. `apply_for_job` (line ~765)
8. `get_my_applications` (line ~795)
9. `withdraw_application` (line ~820)

For each one, replace the auth header parsing block (typically 8-12 lines) with the 3-line helper call shown above.

### Step 4: Update test fixtures for JWT

- [ ] **Update conftest.py**

The `seeker_token` and `employer_token` fixtures in `tests/conftest.py` already work — they call `/api/signup` then `/api/login` and extract the token from the response. Since signup/login now return JWTs, these fixtures will automatically return JWTs. No changes needed to conftest.py.

- [ ] **Run all tests to verify JWT changes work**

```bash
cd "E:/Projects/Intelligent job matching website"
pytest tests/ -v
```

Expected: All existing tests PASS (they get tokens from signup/login which now return JWTs).

### Step 5: Commit

- [ ] **Commit JWT authentication**

```bash
cd "E:/Projects/Intelligent job matching website"
git add app.py requirements.txt tests/test_auth.py
git commit -m "feat: replace custom tokens with JWT authentication

Implements PDF requirement 2.2.2 #10. Tokens now use HS256 signing
with 24-hour expiration. All endpoints updated to decode JWT."
```

---

## Task 2: Move Hardcoded Credentials to .env

**Files:**
- Modify: `app.py:119-125`
- Modify: `.env.example`

### Step 1: Verify .env loading already works

- [ ] **Check current state**

`app.py` already has `from dotenv import load_dotenv` and `load_dotenv()` at the top, and uses `os.environ.get('DB_URI', ...)` for the database URI. The `.env` file already exists with real values. `.gitignore` already excludes `.env`.

The default fallback in `app.py` line 122 still shows a MySQL connection string with `root:password`. This is the hardcoded credential to remove.

### Step 2: Update the fallback default to SQLite

- [ ] **Change the DB_URI fallback**

In `app.py`, find (around line 120-124):
```python
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DB_URI',
    'mysql+pymysql://root:password@localhost:3306/intelligent_job_matching'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
```

Replace with:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DB_URI',
    'sqlite:///dev.db'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
```

### Step 3: Update .env.example

- [ ] **Update .env.example with documentation**

Replace the contents of `.env.example`:
```
# Database connection URI
# MySQL (production): mysql+pymysql://user:password@localhost:3306/intelligent_job_matching
# SQLite (development): sqlite:///dev.db
DB_URI=mysql+pymysql://user:password@localhost:3306/intelligent_job_matching

# Secret key for JWT signing — CHANGE THIS in production
SECRET_KEY=your-secret-key-here

# Flask environment
FLASK_ENV=development

# File upload directory
UPLOAD_FOLDER=uploads

# SWI-Prolog installation directory
SWI_HOME_DIR=C:/Program Files/swipl
```

### Step 4: Run tests

- [ ] **Run tests to verify nothing breaks**

```bash
cd "E:/Projects/Intelligent job matching website"
pytest tests/ -v
```

Expected: PASS — tests use `os.environ['DB_URI'] = 'sqlite:///:memory:'` in conftest.py, so the default fallback doesn't affect them.

### Step 5: Commit

- [ ] **Commit .env changes**

```bash
cd "E:/Projects/Intelligent job matching website"
git add app.py .env.example
git commit -m "fix: remove hardcoded database credentials from app.py

Default fallback now uses SQLite for development. Production credentials
must be set via .env file."
```
