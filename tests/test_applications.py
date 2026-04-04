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
