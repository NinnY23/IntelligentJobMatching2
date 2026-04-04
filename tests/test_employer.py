# tests/test_employer.py
import pytest


# ── PUT /api/job-posts/<id> ────────────────────────────────────────────────

def test_update_own_job(client, employer_token, sample_job):
    res = client.put(
        f'/api/job-posts/{sample_job["id"]}',
        json={'position': 'Senior Python Dev'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    assert res.get_json()['job']['position'] == 'Senior Python Dev'


def test_update_partial_fields(client, employer_token, sample_job):
    res = client.put(
        f'/api/job-posts/{sample_job["id"]}',
        json={'salary_min': '60000', 'salary_max': '90000'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    job = res.get_json()['job']
    assert job['salary_min'] == '60000'
    assert job['position'] == 'Python Dev'   # unchanged


def test_cannot_update_other_employers_job(client, sample_job):
    # Create a second employer
    client.post('/api/signup', json={
        'email': 'emp2@t.com', 'password': 'p',
        'name': 'E2', 'role': 'employer'
    })
    res2 = client.post('/api/login', json={'email': 'emp2@t.com', 'password': 'p'})
    token2 = res2.get_json()['token']

    res = client.put(
        f'/api/job-posts/{sample_job["id"]}',
        json={'position': 'Hacked'},
        headers={'Authorization': f'Bearer {token2}'}
    )
    assert res.status_code == 404


def test_update_requires_employer_role(client, seeker_token, sample_job):
    res = client.put(
        f'/api/job-posts/{sample_job["id"]}',
        json={'position': 'Hacked'},
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 403


# ── DELETE /api/job-posts/<id> ─────────────────────────────────────────────

def test_delete_own_job(client, employer_token, sample_job):
    res = client.delete(
        f'/api/job-posts/{sample_job["id"]}',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200

    # Verify the job is actually gone
    list_res = client.get('/api/job-posts')
    jobs = list_res.get_json()
    assert not any(j['id'] == sample_job['id'] for j in jobs)


def test_cannot_delete_other_employers_job(client, sample_job):
    client.post('/api/signup', json={
        'email': 'emp3@t.com', 'password': 'p',
        'name': 'E3', 'role': 'employer'
    })
    r = client.post('/api/login', json={'email': 'emp3@t.com', 'password': 'p'})
    token3 = r.get_json()['token']

    res = client.delete(
        f'/api/job-posts/{sample_job["id"]}',
        headers={'Authorization': f'Bearer {token3}'}
    )
    assert res.status_code == 404


def test_seeker_cannot_delete_job(client, seeker_token, sample_job):
    res = client.delete(
        f'/api/job-posts/{sample_job["id"]}',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 403


def test_delete_nonexistent_job(client, employer_token):
    res = client.delete(
        '/api/job-posts/99999',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 404
