import os
import pytest

# Set DB_URI to SQLite BEFORE importing app so Flask-SQLAlchemy uses it
os.environ['DB_URI'] = 'sqlite:///:memory:'

from app import app as flask_app, db


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeker_token(client):
    client.post('/api/signup', json={
        'email': 'seeker@t.com', 'password': 'pass',
        'name': 'Seeker', 'role': 'employee'
    })
    res = client.post('/api/login', json={'email': 'seeker@t.com', 'password': 'pass'})
    return res.get_json()['token']


@pytest.fixture
def employer_token(client):
    client.post('/api/signup', json={
        'email': 'emp@t.com', 'password': 'pass',
        'name': 'Employer', 'role': 'employer'
    })
    res = client.post('/api/login', json={'email': 'emp@t.com', 'password': 'pass'})
    return res.get_json()['token']


@pytest.fixture
def sample_job(client, employer_token):
    res = client.post('/api/job-posts', json={
        'position': 'Python Dev',
        'company': 'TechCo',
        'location': 'Bangkok',
        'description': 'Build APIs',
        'required_skills': 'Python,Flask',
        'preferred_skills': 'Docker',
        'salary_min': '50000',
        'salary_max': '80000',
        'job_type': 'Full-time',
        'openings': 2,
        'deadline': '2026-12-31'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    return res.get_json()['job']
