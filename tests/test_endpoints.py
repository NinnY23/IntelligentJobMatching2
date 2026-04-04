def test_debug_users_endpoint_is_removed(client):
    res = client.get('/api/debug/users')
    assert res.status_code == 404, \
        f"Expected 404 but got {res.status_code} — debug endpoint must be deleted"


def test_debug_jobs_endpoint_is_removed(client):
    res = client.get('/api/debug/jobs')
    assert res.status_code == 404, \
        f"Expected 404 but got {res.status_code} — debug endpoint must be deleted"


def test_jobs_alias_returns_200(client):
    """GET /api/jobs must return 200 (the alias route)."""
    res = client.get('/api/jobs')
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
