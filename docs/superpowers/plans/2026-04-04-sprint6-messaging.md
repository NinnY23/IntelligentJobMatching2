# Sprint 6: Messaging — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add in-app messaging between job seekers and employers with text, photo, and file attachment support.
**Architecture:** New Message model in MySQL, Flask endpoints for CRUD + file upload, React Messages page with 5-second polling. Access gated by Application existence.
**Tech Stack:** Flask / SQLAlchemy / React 19 / multipart/form-data file upload

---

## Task 6.1: Add Message model to models.py

- [ ] Add the `Message` model to `models.py`:

```python
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True)
    body = db.Column(db.Text, default='')
    attachment_path = db.Column(db.String(500), default='')
    attachment_name = db.Column(db.String(255), default='')
    attachment_type = db.Column(db.String(100), default='')  # MIME type
    read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'job_id': self.job_id,
            'body': self.body,
            'attachment_path': self.attachment_path,
            'attachment_name': self.attachment_name,
            'attachment_type': self.attachment_type,
            'read': self.read,
            'created_at': self.created_at.isoformat()
        }
```

- [ ] Write test `tests/test_messaging.py`:

```python
def test_message_model_exists(app):
    from models import Message
    assert Message.__tablename__ == 'messages'

def test_message_defaults(app):
    from models import Message, db, User
    with app.app_context():
        u = User(email='s@t.com', password='x', name='S', role='employee')
        r = User(email='r@t.com', password='x', name='R', role='employer')
        db.session.add_all([u, r])
        db.session.flush()
        m = Message(sender_id=u.id, receiver_id=r.id, body='Hello')
        db.session.add(m)
        db.session.commit()
        assert m.read == False
        assert m.attachment_path == ''
```

- [ ] Run tests → FAILED → add model → PASSED → commit.

---

## Task 6.2: Add messaging endpoints to app.py

- [ ] Add `import os, uuid` and `from werkzeug.utils import secure_filename` at top of `app.py`.

- [ ] Add helper functions:

```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user(request):
    """Extract user from Bearer token. Returns User or None."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ')[1]
    parts = token.split('_')
    if len(parts) < 2:
        return None
    return User.query.filter_by(email=parts[1]).first()
```

- [ ] Add endpoint — GET /api/messages (list conversations):

```python
@app.route('/api/messages', methods=['GET'])
def get_conversations():
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    # Get all unique conversation partners
    from sqlalchemy import or_
    msgs = Message.query.filter(
        or_(Message.sender_id == user.id, Message.receiver_id == user.id)
    ).order_by(Message.created_at.desc()).all()

    partners = {}
    for m in msgs:
        partner_id = m.receiver_id if m.sender_id == user.id else m.sender_id
        if partner_id not in partners:
            partner = User.query.get(partner_id)
            unread = Message.query.filter_by(
                sender_id=partner_id, receiver_id=user.id, read=False
            ).count()
            partners[partner_id] = {
                'partner_id': partner_id,
                'partner_name': partner.name if partner else 'Unknown',
                'last_message': m.body or f'[{m.attachment_name}]',
                'last_message_at': m.created_at.isoformat(),
                'unread_count': unread
            }
    return jsonify(list(partners.values())), 200
```

- [ ] Add endpoint — GET /api/messages/<user_id> (get thread):

```python
@app.route('/api/messages/<int:other_user_id>', methods=['GET'])
def get_thread(other_user_id):
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    from sqlalchemy import or_, and_
    page = request.args.get('page', 1, type=int)
    after = request.args.get('after')

    query = Message.query.filter(
        or_(
            and_(Message.sender_id == user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == user.id)
        )
    )
    if after:
        from datetime import datetime as dt
        try:
            after_dt = dt.fromisoformat(after)
            query = query.filter(Message.created_at > after_dt)
        except ValueError:
            pass

    messages = query.order_by(Message.created_at.asc()).paginate(
        page=page, per_page=50, error_out=False
    ).items
    return jsonify([m.to_dict() for m in messages]), 200
```

- [ ] Add endpoint — POST /api/messages/<user_id> (send message):

```python
@app.route('/api/messages/<int:other_user_id>', methods=['POST'])
def send_message(other_user_id):
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    receiver = User.query.get(other_user_id)
    if not receiver:
        return jsonify({"message": "Recipient not found"}), 404

    # Access control: must have a connection via application
    from sqlalchemy import or_
    has_connection = Application.query.filter(
        or_(
            Application.user_id == user.id,
            Application.user_id == other_user_id
        )
    ).join(Job).filter(
        or_(
            Job.employer_id == user.id,
            Job.employer_id == other_user_id
        )
    ).first()
    if not has_connection:
        return jsonify({"message": "You can only message users connected through a job application"}), 403

    body = request.form.get('body', '')
    attachment_path = ''
    attachment_name = ''
    attachment_type = ''

    if 'attachment' in request.files:
        file = request.files['attachment']
        if file and file.filename and allowed_file(file.filename):
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            if size > MAX_FILE_SIZE:
                return jsonify({"message": "File too large. Max 10MB."}), 400
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'messages', str(user.id))
            os.makedirs(upload_dir, exist_ok=True)
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            attachment_path = f"messages/{user.id}/{filename}"
            attachment_name = secure_filename(file.filename)
            attachment_type = file.content_type or f"application/{ext}"

    if not body and not attachment_path:
        return jsonify({"message": "Message must have text or attachment"}), 400

    msg = Message(
        sender_id=user.id,
        receiver_id=other_user_id,
        body=body,
        attachment_path=attachment_path,
        attachment_name=attachment_name,
        attachment_type=attachment_type
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"message": "Sent", "data": msg.to_dict()}), 201
```

- [ ] Add endpoint — PATCH /api/messages/<user_id>/read (mark as read):

```python
@app.route('/api/messages/<int:other_user_id>/read', methods=['PATCH'])
def mark_read(other_user_id):
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401
    Message.query.filter_by(
        sender_id=other_user_id, receiver_id=user.id, read=False
    ).update({'read': True})
    db.session.commit()
    return jsonify({"message": "Marked as read"}), 200
```

- [ ] Add endpoint — GET /api/uploads/messages/<path> (serve uploaded files):

```python
@app.route('/api/uploads/messages/<path:filepath>', methods=['GET'])
def serve_message_file(filepath):
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401
    # Security: only sender or receiver can access
    parts = filepath.split('/')
    if len(parts) >= 1:
        try:
            sender_id = int(parts[0])
            if sender_id != user.id:
                msg = Message.query.filter_by(
                    attachment_path=f"messages/{filepath}", receiver_id=user.id
                ).first()
                if not msg:
                    return jsonify({"message": "Forbidden"}), 403
        except (ValueError, IndexError):
            return jsonify({"message": "Invalid path"}), 400
    from flask import send_from_directory
    upload_folder = app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filepath)
```

- [ ] Write tests:

```python
def test_send_message_requires_auth(client):
    res = client.post('/api/messages/1', data={'body': 'hi'})
    assert res.status_code == 401

def test_get_conversations_empty(client, seeker_token):
    res = client.get('/api/messages', headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    assert res.get_json() == []

def test_cannot_message_without_connection(client, seeker_token):
    # signup a stranger
    client.post('/api/signup', json={'email':'stranger@t.com','password':'p','name':'S','role':'employer'})
    login = client.post('/api/login', json={'email':'stranger@t.com','password':'p'})
    stranger_id = login.get_json().get('user', {}).get('id', 999)
    res = client.post(f'/api/messages/{stranger_id}',
                      data={'body': 'hello'},
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 403
```

- [ ] Run tests → PASSED → commit.

---

## Task 6.3: Add api.js messaging functions

- [ ] Add to `frontend/src/api.js`:

```js
export async function fetchConversations() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/messages', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function fetchThread(userId, after = null) {
  const token = localStorage.getItem('token');
  const url = after ? `/api/messages/${userId}?after=${encodeURIComponent(after)}` : `/api/messages/${userId}`;
  const res = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch messages');
  return res.json();
}

export async function sendMessage(userId, body, attachmentFile = null) {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  if (body) formData.append('body', body);
  if (attachmentFile) formData.append('attachment', attachmentFile);
  const res = await fetch(`/api/messages/${userId}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  return { ok: res.ok, status: res.status, data: await res.json() };
}

export async function markThreadRead(userId) {
  const token = localStorage.getItem('token');
  await fetch(`/api/messages/${userId}/read`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

export async function fetchUnreadCount() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/messages', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) return 0;
  const convos = await res.json();
  return convos.reduce((sum, c) => sum + (c.unread_count || 0), 0);
}
```

---

## Task 6.4: Create frontend/src/pages/Messages.jsx

- [ ] Create `frontend/src/pages/Messages.jsx`:

```jsx
import React, { useState, useEffect, useRef } from 'react';
import { fetchConversations, fetchThread, sendMessage, markThreadRead } from '../api';
import './Messages.css';

export default function Messages({ user }) {
  const [conversations, setConversations] = useState([]);
  const [activePartnerId, setActivePartnerId] = useState(null);
  const [thread, setThread] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [attachment, setAttachment] = useState(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);
  const pollRef = useRef(null);
  const lastTimestampRef = useRef(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (activePartnerId) {
      loadThread(activePartnerId);
      markThreadRead(activePartnerId);
      startPolling(activePartnerId);
    }
    return () => clearInterval(pollRef.current);
  }, [activePartnerId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [thread]);

  async function loadConversations() {
    try {
      const convos = await fetchConversations();
      setConversations(convos);
    } catch (e) {
      setError('Failed to load conversations.');
    }
  }

  async function loadThread(partnerId) {
    const msgs = await fetchThread(partnerId);
    setThread(msgs);
    if (msgs.length > 0) {
      lastTimestampRef.current = msgs[msgs.length - 1].created_at;
    }
  }

  function startPolling(partnerId) {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const newMsgs = await fetchThread(partnerId, lastTimestampRef.current);
      if (newMsgs.length > 0) {
        setThread(prev => [...prev, ...newMsgs]);
        lastTimestampRef.current = newMsgs[newMsgs.length - 1].created_at;
        loadConversations();
      }
    }, 5000);
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!messageText.trim() && !attachment) return;
    setSending(true);
    const result = await sendMessage(activePartnerId, messageText, attachment);
    if (result.ok) {
      setMessageText('');
      setAttachment(null);
      await loadThread(activePartnerId);
      loadConversations();
    } else {
      setError(result.data.message || 'Failed to send message.');
    }
    setSending(false);
  }

  function isImage(mimeType) {
    return mimeType && mimeType.startsWith('image/');
  }

  return (
    <div className="messages-page">
      <div className="conversations-panel">
        <div className="conversations-header"><h3>Messages</h3></div>
        {conversations.length === 0 && (
          <div className="empty-state-sm">No conversations yet.</div>
        )}
        {conversations.map(c => (
          <div
            key={c.partner_id}
            className={`conversation-item ${activePartnerId === c.partner_id ? 'active' : ''}`}
            onClick={() => setActivePartnerId(c.partner_id)}
          >
            <div className="convo-avatar">
              {c.partner_name.slice(0, 2).toUpperCase()}
            </div>
            <div className="convo-info">
              <div className="convo-name">
                {c.partner_name}
                {c.unread_count > 0 && <span className="unread-badge">{c.unread_count}</span>}
              </div>
              <div className="convo-preview">{c.last_message}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="thread-panel">
        {!activePartnerId ? (
          <div className="thread-empty">Select a conversation to start messaging.</div>
        ) : (
          <>
            <div className="thread-messages">
              {thread.map(msg => {
                const isMine = msg.sender_id === user.id;
                return (
                  <div key={msg.id} className={`message-bubble ${isMine ? 'mine' : 'theirs'}`}>
                    {msg.body && <p>{msg.body}</p>}
                    {msg.attachment_path && isImage(msg.attachment_type) && (
                      <img
                        src={`/api/uploads/${msg.attachment_path}`}
                        alt={msg.attachment_name}
                        className="msg-image"
                        onClick={() => window.open(`/api/uploads/${msg.attachment_path}`)}
                      />
                    )}
                    {msg.attachment_path && !isImage(msg.attachment_type) && (
                      <a
                        href={`/api/uploads/${msg.attachment_path}`}
                        target="_blank"
                        rel="noreferrer"
                        className="msg-file-link"
                      >
                        📎 {msg.attachment_name}
                      </a>
                    )}
                    <span className="msg-time">
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>

            {error && <div className="error-banner">{error}</div>}

            <form className="message-input-bar" onSubmit={handleSend}>
              {attachment && (
                <div className="attachment-preview">
                  📎 {attachment.name}
                  <button type="button" onClick={() => setAttachment(null)}>✕</button>
                </div>
              )}
              <input
                type="text"
                placeholder="Type a message..."
                value={messageText}
                onChange={e => setMessageText(e.target.value)}
              />
              <label className="attach-btn" title="Attach file">
                📎
                <input
                  type="file"
                  accept="image/*,.pdf,.doc,.docx"
                  style={{ display: 'none' }}
                  onChange={e => setAttachment(e.target.files[0] || null)}
                />
              </label>
              <button type="submit" className="btn-primary" disabled={sending || (!messageText.trim() && !attachment)}>
                {sending ? '...' : 'Send'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
```

- [ ] Create `frontend/src/pages/Messages.css`:

```css
.messages-page { display: grid; grid-template-columns: 280px 1fr; height: calc(100vh - 60px); }
.conversations-panel { border-right: 1px solid var(--color-border); background: #fff; overflow-y: auto; }
.conversations-header { padding: 20px; border-bottom: 1px solid var(--color-border); }
.conversations-header h3 { font-size: 16px; font-weight: 700; }
.conversation-item { display: flex; align-items: center; gap: 12px; padding: 14px 16px; cursor: pointer; border-bottom: 1px solid var(--color-border); transition: background 0.1s; }
.conversation-item:hover, .conversation-item.active { background: var(--color-bg); }
.conversation-item.active { border-left: 3px solid var(--color-primary); }
.convo-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--color-primary-light); color: var(--color-primary-dark); font-weight: 700; font-size: 13px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.convo-name { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.unread-badge { background: #ef4444; color: #fff; font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 700; }
.convo-preview { font-size: 12px; color: var(--color-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px; margin-top: 2px; }
.empty-state-sm { padding: 24px; text-align: center; color: var(--color-muted); font-size: 13px; }
.thread-panel { display: flex; flex-direction: column; background: var(--color-bg); }
.thread-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--color-muted); font-size: 14px; }
.thread-messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.message-bubble { max-width: 60%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
.message-bubble.mine { align-self: flex-end; background: var(--color-primary); color: #fff; border-bottom-right-radius: 4px; }
.message-bubble.theirs { align-self: flex-start; background: #fff; color: var(--color-text); border-bottom-left-radius: 4px; box-shadow: var(--shadow); }
.msg-time { display: block; font-size: 10px; opacity: 0.7; margin-top: 4px; text-align: right; }
.msg-image { max-width: 200px; max-height: 200px; border-radius: 8px; cursor: pointer; display: block; margin-top: 6px; }
.msg-file-link { display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.2); padding: 6px 10px; border-radius: 8px; text-decoration: none; font-size: 13px; margin-top: 6px; }
.message-bubble.theirs .msg-file-link { color: var(--color-primary); background: var(--color-primary-light); }
.message-input-bar { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: #fff; border-top: 1px solid var(--color-border); }
.message-input-bar input { flex: 1; padding: 10px 14px; border: 1.5px solid var(--color-border); border-radius: 20px; font-size: 14px; font-family: var(--font); outline: none; }
.message-input-bar input:focus { border-color: var(--color-primary); }
.attach-btn { font-size: 18px; cursor: pointer; padding: 6px; }
.attachment-preview { display: flex; align-items: center; gap: 8px; background: var(--color-primary-light); padding: 6px 12px; border-radius: 8px; font-size: 12px; color: var(--color-primary-dark); margin-bottom: 8px; width: 100%; }
.attachment-preview button { background: none; border: none; cursor: pointer; color: var(--color-muted); }
```

---

## Task 6.5: Add unread badge polling to App.jsx

- [ ] In `App.jsx`, add state and effect for unread message polling:

```jsx
const [unreadMessages, setUnreadMessages] = useState(0);

useEffect(() => {
  if (!user) return;
  async function checkUnread() {
    try {
      const count = await fetchUnreadCount();
      setUnreadMessages(count);
    } catch {}
  }
  checkUnread();
  const interval = setInterval(checkUnread, 30000);
  return () => clearInterval(interval);
}, [user]);
// Pass to Navbar: <Navbar user={user} onLogout={handleLogout} unreadMessages={unreadMessages} />
```

---

## Task 6.6: Add /messages route to App.jsx + commit

- [ ] Import `Messages` component and add route in `App.jsx`:

```jsx
import Messages from './pages/Messages';
// In Routes:
<Route path="/messages" element={
  <>
    <Navbar user={user} onLogout={handleLogout} unreadMessages={unreadMessages} />
    <Messages user={user} />
  </>
} />
```

- [ ] Final commit:

```bash
git add models.py app.py frontend/src/api.js frontend/src/pages/Messages.jsx frontend/src/pages/Messages.css frontend/src/App.jsx
git commit -m "feat: sprint 6 - in-app messaging with file/photo attachment support"
```
