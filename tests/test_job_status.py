def test_create_job_defaults_to_active(client, employer_token):
    res = client.post('/api/job-posts', json={
        'position': 'Dev', 'company': 'Co', 'location': 'BKK',
        'description': 'Build stuff', 'required_skills': 'Python'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 201
    assert res.get_json()['job']['status'] == 'active'

def test_create_draft_job(client, employer_token):
    res = client.post('/api/job-posts', json={
        'position': 'Draft Dev', 'company': 'Co', 'location': 'BKK',
        'description': 'WIP', 'required_skills': 'Python', 'status': 'draft'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 201
    assert res.get_json()['job']['status'] == 'draft'

def test_draft_jobs_hidden_from_public_listing(client, employer_token):
    client.post('/api/job-posts', json={
        'position': 'Active Job', 'company': 'Co', 'location': 'BKK',
        'description': 'Active', 'required_skills': 'Python'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    client.post('/api/job-posts', json={
        'position': 'Draft Job', 'company': 'Co', 'location': 'BKK',
        'description': 'Draft', 'required_skills': 'Python', 'status': 'draft'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    res = client.get('/api/job-posts')
    positions = [j['position'] for j in res.get_json()]
    assert 'Active Job' in positions
    assert 'Draft Job' not in positions

def test_employer_sees_all_statuses(client, employer_token):
    client.post('/api/job-posts', json={
        'position': 'Active Emp', 'company': 'Co', 'location': 'BKK',
        'description': 'Desc', 'required_skills': 'Python'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    client.post('/api/job-posts', json={
        'position': 'Draft Emp', 'company': 'Co', 'location': 'BKK',
        'description': 'Desc', 'required_skills': 'Python', 'status': 'draft'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    res = client.get('/api/employer/jobs', headers={'Authorization': f'Bearer {employer_token}'})
    positions = [j['position'] for j in res.get_json()['jobs']]
    assert 'Active Emp' in positions
    assert 'Draft Emp' in positions

def test_archive_job(client, employer_token):
    res = client.post('/api/job-posts', json={
        'position': 'To Archive', 'company': 'Co', 'location': 'BKK',
        'description': 'Desc', 'required_skills': 'Python'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    job_id = res.get_json()['job']['id']
    res = client.put(f'/api/job-posts/{job_id}', json={'status': 'archived'},
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 200
    assert res.get_json()['job']['status'] == 'archived'
    res = client.get('/api/job-posts')
    positions = [j['position'] for j in res.get_json()]
    assert 'To Archive' not in positions

def test_publish_draft(client, employer_token):
    res = client.post('/api/job-posts', json={
        'position': 'Was Draft', 'company': 'Co', 'location': 'BKK',
        'description': 'Desc', 'required_skills': 'Python', 'status': 'draft'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    job_id = res.get_json()['job']['id']
    client.put(f'/api/job-posts/{job_id}', json={'status': 'active'},
               headers={'Authorization': f'Bearer {employer_token}'})
    res = client.get('/api/job-posts')
    positions = [j['position'] for j in res.get_json()]
    assert 'Was Draft' in positions
