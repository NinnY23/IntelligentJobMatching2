import json
import jwt


def test_signup_returns_jwt(client):
    res = client.post('/api/signup', json={
        'email': 'jwt@test.com', 'password': 'pass123',
        'name': 'JWT User', 'role': 'employee'
    })
    assert res.status_code == 201
    data = res.get_json()
    token = data['token']
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert decoded['email'] == 'jwt@test.com'
    assert decoded['role'] == 'employee'
    assert 'user_id' in decoded
    assert 'exp' in decoded


def test_login_returns_jwt(client):
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
    import jwt as pyjwt
    from datetime import datetime, timedelta
    from app import app as flask_app
    secret = flask_app.config['SECRET_KEY']
    expired_token = pyjwt.encode(
        {'user_id': 999, 'email': 'x@x.com', 'role': 'employee',
         'exp': datetime.utcnow() - timedelta(hours=1)},
        secret,
        algorithm='HS256'
    )
    res = client.get('/api/profile',
                     headers={'Authorization': f'Bearer {expired_token}'})
    assert res.status_code == 401
    assert 'expired' in res.get_json()['message'].lower()


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
