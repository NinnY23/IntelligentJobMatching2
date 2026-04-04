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
