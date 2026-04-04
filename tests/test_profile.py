# tests/test_profile.py
import pytest


def test_user_has_education_experience_fields(app):
    """User model must have education and experience columns."""
    from models import User
    with app.app_context():
        cols = [c.name for c in User.__table__.columns]
        assert 'education' in cols
        assert 'experience' in cols


def test_profile_update_saves_education_experience(client, seeker_token):
    """PUT /api/profile persists education and experience."""
    res = client.put('/api/profile', json={
        'education': 'B.Eng Computer Engineering, KMITL 2024',
        'experience': '1 year intern at TechCorp',
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['user']['education'] == 'B.Eng Computer Engineering, KMITL 2024'
    assert data['user']['experience'] == '1 year intern at TechCorp'


def test_profile_get_returns_education_experience(client, seeker_token):
    """GET /api/profile returns education and experience after save."""
    client.put('/api/profile', json={
        'education': 'Masters in AI',
        'experience': '3 years at StartupX',
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    res = client.get('/api/profile', headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    user = res.get_json()['user']
    assert user['education'] == 'Masters in AI'
    assert user['experience'] == '3 years at StartupX'
