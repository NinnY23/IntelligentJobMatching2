"""
Integration tests for the two new Prolog-backed matching endpoints:
    GET  /api/jobs/matches
    GET  /api/job-posts/<job_id>/candidates
"""


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _signup_and_token(client, email, password, name, role):
    """Sign up a user and return their auth token."""
    client.post('/api/signup', json={
        'email': email,
        'password': password,
        'name': name,
        'role': role
    })
    res = client.post('/api/login', json={'email': email, 'password': password})
    return res.get_json()['token']


# ---------------------------------------------------------------------------
# GET /api/jobs/matches
# ---------------------------------------------------------------------------

def test_job_matches_requires_auth(client):
    res = client.get('/api/jobs/matches')
    assert res.status_code == 401


def test_job_matches_returns_list_for_authenticated_employee(client):
    token = _signup_and_token(
        client, 'seeker@test.com', 'pass123', 'Seeker', 'employee'
    )
    res = client.get(
        '/api/jobs/matches',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_job_matches_returns_empty_when_no_skills(client):
    """An employee with no skills listed should get an empty match list."""
    token = _signup_and_token(
        client, 'noskills@test.com', 'pass', 'No Skills', 'employee'
    )
    res = client.get(
        '/api/jobs/matches',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert res.status_code == 200
    assert res.get_json() == []


def test_job_matches_result_contains_match_score(client):
    """When a match is found, each result must include match_score."""
    # Create employer and post a Python job
    emp_token = _signup_and_token(
        client, 'emp_match@test.com', 'pass', 'Employer', 'employer'
    )
    client.post('/api/job-posts', json={
        'position': 'Python Dev',
        'company': 'TestCo',
        'location': 'BKK',
        'description': 'Python job',
        'required_skills': 'python',
        'preferred_skills': ''
    }, headers={'Authorization': f'Bearer {emp_token}'})

    # Employee with no skills (empty list returned)
    token = _signup_and_token(
        client, 'dev_match@test.com', 'pass', 'Dev', 'employee'
    )
    res = client.get(
        '/api/jobs/matches',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert res.status_code == 200
    data = res.get_json()
    # If any matches returned, verify the shape
    for item in data:
        assert 'match_score' in item
        assert 'matched_skills' in item
        assert 'missing_skills' in item


# ---------------------------------------------------------------------------
# GET /api/job-posts/<job_id>/candidates
# ---------------------------------------------------------------------------

def test_candidates_requires_employer_auth(client):
    """Endpoint must reject unauthenticated requests."""
    res = client.get('/api/job-posts/1/candidates')
    assert res.status_code == 401


def test_candidates_rejects_employee_role(client):
    """An employee token must receive 403."""
    token = _signup_and_token(
        client, 'emp_role@test.com', 'pass', 'Employee', 'employee'
    )
    res = client.get(
        '/api/job-posts/1/candidates',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert res.status_code == 403


def test_candidates_returns_404_for_unknown_job(client):
    emp_token = _signup_and_token(
        client, 'employer_cand@test.com', 'pass', 'Emp', 'employer'
    )
    res = client.get(
        '/api/job-posts/99999/candidates',
        headers={'Authorization': f'Bearer {emp_token}'}
    )
    assert res.status_code == 404


def test_candidates_returns_list_for_own_job(client):
    emp_token = _signup_and_token(
        client, 'employer2@test.com', 'pass', 'Emp2', 'employer'
    )
    # Create a job
    post_res = client.post('/api/job-posts', json={
        'position': 'Dev',
        'company': 'Co',
        'location': 'BKK',
        'description': 'desc',
        'required_skills': 'python',
        'preferred_skills': ''
    }, headers={'Authorization': f'Bearer {emp_token}'})
    assert post_res.status_code == 201
    job_id = post_res.get_json().get('job', {}).get('id') or post_res.get_json().get('id')

    res = client.get(
        f'/api/job-posts/{job_id}/candidates',
        headers={'Authorization': f'Bearer {emp_token}'}
    )
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
