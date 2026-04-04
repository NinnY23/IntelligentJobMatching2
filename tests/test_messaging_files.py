import pytest
import os
import shutil


def test_serve_attachment_with_query_token(client, app):
    """File serving endpoint should accept JWT token as query parameter."""
    import jwt as pyjwt
    from datetime import datetime, timedelta
    from models import User, Message, db
    import bcrypt

    with app.app_context():
        pw = bcrypt.hashpw(b'pass123', bcrypt.gensalt()).decode('utf-8')
        sender = User(email='sender@test.com', password=pw, name='Sender', role='employee')
        receiver = User(email='receiver@test.com', password=pw, name='Receiver', role='employee')
        db.session.add_all([sender, receiver])
        db.session.commit()

        msg = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            body='test file',
            attachment_path='messages/1/testfile.txt',
            attachment_name='testfile.txt',
            attachment_type='text/plain'
        )
        db.session.add(msg)
        db.session.commit()

        token = pyjwt.encode({
            'user_id': sender.id,
            'email': sender.email,
            'role': sender.role,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        # Without any token → 401
        res_no_token = client.get('/api/uploads/messages/1/testfile.txt')
        assert res_no_token.status_code == 401

        # With token in query param → should NOT be 401
        res_query = client.get(f'/api/uploads/messages/1/testfile.txt?token={token}')
        assert res_query.status_code != 401, \
            f"Query param token should authenticate, got {res_query.status_code}"


def test_serve_attachment_rejects_invalid_query_token(client, app):
    """File serving endpoint should reject invalid query tokens."""
    res = client.get('/api/uploads/messages/1/fake.pdf?token=invalid.token.here')
    assert res.status_code == 401


def test_serve_attachment_returns_file_content(client, app):
    """File serving endpoint should return actual file content when file exists on disk."""
    import jwt as pyjwt
    from datetime import datetime, timedelta
    from models import User, Message, db
    import bcrypt

    with app.app_context():
        pw = bcrypt.hashpw(b'pass123', bcrypt.gensalt()).decode('utf-8')
        sender = User(email='filesender@test.com', password=pw, name='FileSender', role='employee')
        receiver = User(email='filereceiver@test.com', password=pw, name='FileReceiver', role='employee')
        db.session.add_all([sender, receiver])
        db.session.commit()

        # Create actual file on disk
        upload_folder = app.config['UPLOAD_FOLDER']
        file_dir = os.path.join(upload_folder, 'messages', str(sender.id))
        os.makedirs(file_dir, exist_ok=True)
        file_path = os.path.join(file_dir, 'realfile.txt')
        with open(file_path, 'w') as f:
            f.write('hello from test')

        try:
            msg = Message(
                sender_id=sender.id,
                receiver_id=receiver.id,
                body='real file',
                attachment_path=f'messages/{sender.id}/realfile.txt',
                attachment_name='realfile.txt',
                attachment_type='text/plain'
            )
            db.session.add(msg)
            db.session.commit()

            token = pyjwt.encode({
                'user_id': sender.id,
                'email': sender.email,
                'role': sender.role,
                'exp': datetime.utcnow() + timedelta(hours=1)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            # With header token
            res = client.get(
                f'/api/uploads/messages/{sender.id}/realfile.txt',
                headers={'Authorization': f'Bearer {token}'}
            )
            assert res.status_code == 200, f"Expected 200, got {res.status_code}"
            assert b'hello from test' in res.data

            # With query param token
            res_q = client.get(f'/api/uploads/messages/{sender.id}/realfile.txt?token={token}')
            assert res_q.status_code == 200, f"Expected 200, got {res_q.status_code}"
            assert b'hello from test' in res_q.data
        finally:
            shutil.rmtree(os.path.join(upload_folder, 'messages', str(sender.id)), ignore_errors=True)
