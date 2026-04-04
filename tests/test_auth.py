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
