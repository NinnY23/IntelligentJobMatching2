def test_forgot_password_generates_token(client):
    client.post('/api/signup', json={
        'email': 'reset@test.com', 'password': 'oldpass',
        'name': 'Reset User', 'role': 'employee'
    })
    res = client.post('/api/forgot-password', json={'email': 'reset@test.com'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'reset_token' in data

def test_forgot_password_nonexistent_email(client):
    res = client.post('/api/forgot-password', json={'email': 'nobody@test.com'})
    assert res.status_code == 200
    assert 'reset_token' not in res.get_json()

def test_reset_password_success(client):
    client.post('/api/signup', json={
        'email': 'reset2@test.com', 'password': 'oldpass',
        'name': 'Reset User 2', 'role': 'employee'
    })
    res = client.post('/api/forgot-password', json={'email': 'reset2@test.com'})
    token = res.get_json()['reset_token']
    res = client.post('/api/reset-password', json={
        'token': token, 'new_password': 'newpass123'
    })
    assert res.status_code == 200
    res = client.post('/api/login', json={
        'email': 'reset2@test.com', 'password': 'newpass123'
    })
    assert res.status_code == 200
    res = client.post('/api/login', json={
        'email': 'reset2@test.com', 'password': 'oldpass'
    })
    assert res.status_code == 401

def test_reset_password_invalid_token(client):
    res = client.post('/api/reset-password', json={
        'token': 'bogus-token', 'new_password': 'newpass'
    })
    assert res.status_code == 400

def test_reset_token_single_use(client):
    client.post('/api/signup', json={
        'email': 'reset3@test.com', 'password': 'oldpass',
        'name': 'Reset User 3', 'role': 'employee'
    })
    res = client.post('/api/forgot-password', json={'email': 'reset3@test.com'})
    token = res.get_json()['reset_token']
    res = client.post('/api/reset-password', json={
        'token': token, 'new_password': 'newpass1'
    })
    assert res.status_code == 200
    res = client.post('/api/reset-password', json={
        'token': token, 'new_password': 'newpass2'
    })
    assert res.status_code == 400
