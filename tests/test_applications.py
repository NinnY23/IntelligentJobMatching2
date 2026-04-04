import pytest


def test_application_model_exists(app):
    from models import Application
    assert Application.__tablename__ == 'applications'


def test_application_to_dict_keys(app):
    from models import Application
    from datetime import datetime
    a = Application(job_id=1, user_id=1, status='pending')
    a.created_at = datetime(2026, 4, 4, 12, 0, 0)
    d = a.to_dict()
    for key in ('id', 'job_id', 'user_id', 'status', 'created_at'):
        assert key in d, f"Missing key: {key}"


def test_apply_for_job(client, seeker_token, sample_job):
    res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data['application']['status'] == 'pending'
    assert data['application']['job_id'] == sample_job['id']


def test_application_unique_constraint(client, seeker_token, sample_job):
    res1 = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res1.status_code == 201
    res2 = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res2.status_code == 409


def test_get_my_applications(client, seeker_token, sample_job):
    client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    res = client.get('/api/applications', headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    apps = res.get_json()
    assert len(apps) == 1
    assert apps[0]['job']['position'] == 'Python Dev'


def test_withdraw_application(client, seeker_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']
    del_res = client.delete(
        f'/api/applications/{app_id}',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert del_res.status_code == 200
    list_res = client.get('/api/applications', headers={'Authorization': f'Bearer {seeker_token}'})
    assert len(list_res.get_json()) == 0


def test_employer_cannot_apply(client, employer_token, sample_job):
    res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {employer_token}'}
    )
    assert res.status_code == 403


def test_apply_nonexistent_job(client, seeker_token):
    res = client.post(
        '/api/jobs/99999/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert res.status_code == 404


def test_apply_requires_auth(client, sample_job):
    res = client.post(f'/api/jobs/{sample_job["id"]}/apply')
    assert res.status_code == 401


def test_withdraw_shortlisted_application_blocked(client, seeker_token, employer_token, sample_job):
    apply_res = client.post(
        f'/api/jobs/{sample_job["id"]}/apply',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    app_id = apply_res.get_json()['application']['id']

    client.patch(
        f'/api/applications/{app_id}/status',
        json={'status': 'shortlisted'},
        headers={'Authorization': f'Bearer {employer_token}'}
    )

    del_res = client.delete(
        f'/api/applications/{app_id}',
        headers={'Authorization': f'Bearer {seeker_token}'}
    )
    assert del_res.status_code == 400
