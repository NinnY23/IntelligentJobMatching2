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


def test_delete_job_cascades_to_applications(client, employer_token, seeker_token, sample_job):
    # Seeker applies for the job
    client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    # Employer deletes the job
    client.delete(
        f'/api/job-posts/{sample_job["id"]}',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    # Seeker's application list should now be empty
    res = client.get('/api/applications',
                     headers={'Authorization': f'Bearer {seeker_token}'})
    apps = res.get_json()
    assert not any(a['job_id'] == sample_job['id'] for a in apps)


# ── GET /api/job-posts/<id>/applicants ─────────────────────────────────────

def test_employer_can_view_applicants(client, employer_token, seeker_token, sample_job):
    # Seeker applies
    client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    res = client.get(
        f'/api/job-posts/{sample_job["id"]}/applicants',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    applicants = res.get_json()
    assert len(applicants) == 1
    assert applicants[0]['name'] == 'Seeker'


def test_applicants_response_includes_match_fields(client, employer_token, seeker_token, sample_job):
    client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    res = client.get(
        f'/api/job-posts/{sample_job["id"]}/applicants',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    a = res.get_json()[0]
    for field in ('application_id', 'status', 'applied_at', 'name', 'email',
                  'match_score', 'matched_skills', 'missing_skills'):
        assert field in a, f"Missing field: {field}"


def test_applicants_sorted_by_match_score_descending(client, employer_token, sample_job):
    # Create two seekers with different skills
    client.post('/api/signup', json={
        'email': 'high@t.com', 'password': 'p', 'name': 'High',
        'role': 'employee'
    })
    client.post('/api/signup', json={
        'email': 'low@t.com', 'password': 'p', 'name': 'Low',
        'role': 'employee'
    })
    # Give high-match seeker skills matching the job
    high_login = client.post('/api/login', json={'email': 'high@t.com', 'password': 'p'})
    high_token = high_login.get_json()['token']
    client.put('/api/profile', json={'skills': 'Python,Flask,Docker'},
               headers={'Authorization': f'Bearer {high_token}'})

    low_login = client.post('/api/login', json={'email': 'low@t.com', 'password': 'p'})
    low_token = low_login.get_json()['token']
    # low seeker has no matching skills

    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {high_token}'})
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {low_token}'})

    res = client.get(f'/api/job-posts/{sample_job["id"]}/applicants',
                     headers={'Authorization': f'Bearer {employer_token}'})
    applicants = res.get_json()
    assert applicants[0]['match_score'] >= applicants[-1]['match_score']


def test_seeker_cannot_view_applicants(client, seeker_token, sample_job):
    res = client.get(
        f'/api/job-posts/{sample_job["id"]}/applicants',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 403


# ── PATCH /api/applications/<id>/status ───────────────────────────────────

def test_employer_can_shortlist(client, employer_token, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']

    res = client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'shortlisted'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    assert res.get_json()['application']['status'] == 'shortlisted'


def test_employer_can_unshortlist(client, employer_token, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']
    # Shortlist first
    client.patch(f'/api/applications/{app_id}/status',
                 json={'status': 'shortlisted'},
                 headers={'Authorization': f'Bearer {employer_token}'})
    # Then revert to pending
    res = client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'pending'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 200
    assert res.get_json()['application']['status'] == 'pending'


def test_invalid_status_rejected(client, employer_token, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']
    res = client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'hired'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 400


def test_employer_cannot_change_status_of_other_employers_application(
        client, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']

    # Second employer tries to shortlist
    client.post('/api/signup', json={
        'email': 'emp4@t.com', 'password': 'p', 'name': 'E4', 'role': 'employer'
    })
    r = client.post('/api/login', json={'email': 'emp4@t.com', 'password': 'p'})
    token4 = r.get_json()['token']

    res = client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'shortlisted'},
        headers={'Authorization': f'Bearer {token4}'}
    )
    assert res.status_code == 403


# ── GET /api/employer/dashboard ────────────────────────────────────────────

def test_dashboard_returns_stats(client, employer_token, sample_job):
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 200
    data = res.get_json()
    for key in ('total_jobs', 'total_applicants', 'total_shortlisted', 'recent_applications'):
        assert key in data, f"Missing key: {key}"


def test_dashboard_counts_jobs(client, employer_token, sample_job):
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.get_json()['total_jobs'] == 1


def test_dashboard_counts_applicants(client, employer_token, seeker_token, sample_job):
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {seeker_token}'})
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.get_json()['total_applicants'] == 1


def test_dashboard_counts_shortlisted(client, employer_token, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']
    client.patch(f'/api/applications/{app_id}/status',
                 json={'status': 'shortlisted'},
                 headers={'Authorization': f'Bearer {employer_token}'})

    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.get_json()['total_shortlisted'] == 1


def test_dashboard_recent_applications_structure(client, employer_token, seeker_token, sample_job):
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {seeker_token}'})
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {employer_token}'})
    recent = res.get_json()['recent_applications']
    assert len(recent) == 1
    for key in ('applicant_name', 'job_position', 'applied_at', 'status'):
        assert key in recent[0], f"Missing key in recent_applications: {key}"


def test_dashboard_requires_employer_role(client, seeker_token):
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 403


def test_dashboard_empty_for_new_employer(client):
    client.post('/api/signup', json={
        'email': 'fresh@t.com', 'password': 'p',
        'name': 'Fresh', 'role': 'employer'
    })
    r = client.post('/api/login', json={'email': 'fresh@t.com', 'password': 'p'})
    token = r.get_json()['token']
    res = client.get('/api/employer/dashboard',
                     headers={'Authorization': f'Bearer {token}'})
    data = res.get_json()
    assert data['total_jobs'] == 0
    assert data['total_applicants'] == 0
    assert data['total_shortlisted'] == 0
    assert data['recent_applications'] == []


def test_applicants_response_includes_profile_fields(client, employer_token, seeker_token, sample_job):
    """GET /api/job-posts/<id>/applicants returns bio, education, experience per applicant."""
    # Seeker applies for the job
    client.post(f'/api/jobs/{sample_job["id"]}/apply',
                headers={'Authorization': f'Bearer {seeker_token}'})
    # Employer views applicants
    res = client.get(f'/api/job-posts/{sample_job["id"]}/applicants',
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    applicant = data[0]
    assert 'bio' in applicant
    assert 'education' in applicant
    assert 'experience' in applicant
