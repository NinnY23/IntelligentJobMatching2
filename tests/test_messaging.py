from models import Message
from models import User
from app import db


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
