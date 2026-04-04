import os
os.environ['DB_URI'] = 'sqlite:///:memory:'

import pytest
from app import app as flask_app, db
from models import Message


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


def test_message_model_exists(app):
    """Message model can be imported and has expected columns."""
    with app.app_context():
        cols = [c.name for c in Message.__table__.columns]
        assert 'id' in cols
        assert 'sender_id' in cols
        assert 'receiver_id' in cols
        assert 'body' in cols
        assert 'read' in cols
        assert 'created_at' in cols


def test_message_defaults(app):
    """Message.to_dict() returns expected keys with defaults."""
    from models import User
    with app.app_context():
        u1 = User(email='a@b.com', password='x', name='A', role='employee')
        u2 = User(email='c@d.com', password='x', name='B', role='employer')
        db.session.add_all([u1, u2])
        db.session.flush()
        msg = Message(sender_id=u1.id, receiver_id=u2.id, body='hello')
        db.session.add(msg)
        db.session.commit()
        d = msg.to_dict()
        assert d['body'] == 'hello'
        assert d['read'] == False
        assert 'created_at' in d
        assert d['sender_id'] == u1.id
