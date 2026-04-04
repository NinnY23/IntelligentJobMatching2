# Messaging — File Access Fix & UI/UX Polish Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the "Unauthorized" error when accessing message attachments (images/PDFs), and polish the messaging UI for consistency with the design system used across the rest of the site.

**Architecture:** The file access bug is caused by the browser making direct HTTP requests to `/api/uploads/...` without the JWT Bearer header — `<img src>` and `<a href>` don't send Authorization headers. The fix adds query-parameter token support to the backend file serving endpoint and appends the token to attachment URLs in the frontend. The UI/UX fixes bring the Messages page in line with the design system (CSS variables, SVG icons, thread header, consistent spacing).

**Tech Stack:** Flask backend (file serving), React 19 frontend, CSS with design system variables

---

## Root Cause Analysis

### Bug A: "Unauthorized" When Accessing Attachments (Critical)

**Root cause chain:**
1. User sends a message with an attachment (image or PDF)
2. Backend stores file at `uploads/messages/{user_id}/{uuid}.ext` and saves `attachment_path` in DB
3. Frontend renders the attachment:
   - Images: `<img src="/api/uploads/messages/1/abc.png" />` (line 141 of Messages.jsx)
   - Files: `<a href="/api/uploads/messages/1/abc.pdf">` (line 149 of Messages.jsx)
   - Click-to-open: `window.open("/api/uploads/messages/1/abc.png")` (line 144)
4. **The browser makes a direct HTTP GET request** — no JavaScript involved, no fetch(), no opportunity to add headers
5. Backend `serve_message_file()` (app.py:1301) calls `get_current_user(request)` which reads `request.headers.get('Authorization')` — this is **empty** on direct browser requests
6. Returns `{"message": "Unauthorized"}`, 401

**The fundamental problem:** JWT Bearer tokens only work with fetch/XHR requests where code can inject the Authorization header. Direct browser navigation (`<img src>`, `<a href>`, `window.open()`) cannot attach headers.

**Fix:** Accept the JWT token as a query parameter (`?token=xxx`) as a fallback in the file serving endpoint. The frontend appends the token to all attachment URLs. This is a standard pattern for JWT-protected file serving.

### Bug B: UI/UX Inconsistencies (Medium)

From the screenshots, the messaging page has these issues:

| # | Issue | Location |
|---|-------|----------|
| 1 | No thread header — can't see who you're talking to | Messages.jsx thread panel |
| 2 | Hardcoded `#ef4444` for unread badge | Messages.css line 65 |
| 3 | Emoji `📎` for attach button — inconsistent with SVG icons elsewhere | Messages.jsx line 183 |
| 4 | No file type icon differentiation (PDFs vs images) | Messages.jsx lines 147-155 |
| 5 | Error banner has no styling class defined | Messages.jsx line 167 |
| 6 | The "Send" button text changes to "..." when sending — should show a word | Messages.jsx line 196 |

---

## Summary of All Issues

| # | Bug | File(s) | Severity |
|---|-----|---------|----------|
| 1 | Attachment URLs don't include auth token — browser gets 401 | `app.py`, `Messages.jsx` | Critical |
| 2 | No thread header showing partner name/avatar | `Messages.jsx`, `Messages.css` | Medium |
| 3 | Hardcoded colors instead of CSS variables | `Messages.css` | Low |
| 4 | Emoji icons instead of SVG, inconsistent file type display | `Messages.jsx`, `Messages.css` | Low |
| 5 | Missing error banner CSS + minor polish | `Messages.jsx`, `Messages.css` | Low |

---

### Task 1: Fix File Access — Add Query-Param Token Support to Backend

**Problem:** The `/api/uploads/messages/<path>` endpoint only accepts JWT from the Authorization header. Browser-initiated requests (`<img src>`, `<a href>`) can't send headers.

**Files:**
- Modify: `app.py:1301-1321`
- Modify: `tests/test_profile.py` (or create `tests/test_messaging_files.py`)

- [ ] **Step 1: Write failing test for token-in-query-param**

Create a new test file `tests/test_messaging_files.py`:

```python
import pytest
import io


def test_serve_attachment_with_query_token(client, app):
    """File serving endpoint should accept JWT token as query parameter."""
    import pyjwt
    from datetime import datetime, timedelta
    from models import User, Message, db

    with app.app_context():
        # Create two users
        import bcrypt
        pw = bcrypt.hashpw(b'pass123', bcrypt.gensalt()).decode('utf-8')
        sender = User(email='sender@test.com', password=pw, name='Sender')
        receiver = User(email='receiver@test.com', password=pw, name='Receiver')
        db.session.add_all([sender, receiver])
        db.session.commit()

        # Create a message with an attachment path
        msg = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            body='test file',
            attachment_path='messages/test/testfile.txt',
            attachment_name='testfile.txt',
            attachment_type='text/plain'
        )
        db.session.add(msg)
        db.session.commit()

        # Generate a token for the sender
        token = pyjwt.encode({
            'user_id': sender.id,
            'email': sender.email,
            'role': sender.role,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        # Without any token → 401
        res_no_token = client.get('/api/uploads/messages/test/testfile.txt')
        assert res_no_token.status_code == 401

        # With token in query param → should not be 401
        # (Will be 404 because the file doesn't exist on disk, but NOT 401)
        res_query = client.get(f'/api/uploads/messages/test/testfile.txt?token={token}')
        # The endpoint should authenticate successfully but may return 404 (file not on disk)
        # The key assertion: it should NOT return 401 (Unauthorized)
        assert res_query.status_code != 401, \
            f"Query param token should authenticate, got {res_query.status_code}"


def test_serve_attachment_rejects_invalid_query_token(client, app):
    """File serving endpoint should reject invalid query tokens."""
    res = client.get('/api/uploads/messages/1/fake.pdf?token=invalid.token.here')
    assert res.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_messaging_files.py -v`

Expected: `test_serve_attachment_with_query_token` FAILS — query param token returns 401.

- [ ] **Step 3: Update `serve_message_file()` to accept token from query param**

In `app.py`, replace the `serve_message_file` function (lines 1301-1321):

```python
@app.route('/api/uploads/messages/<path:filepath>', methods=['GET'])
def serve_message_file(filepath):
    # Accept token from Authorization header OR query parameter
    user = get_current_user(request)
    if not user:
        # Fallback: check for token in query string (for <img src>, <a href>)
        query_token = request.args.get('token')
        if query_token:
            try:
                payload = pyjwt.decode(query_token, app.config['SECRET_KEY'], algorithms=['HS256'])
                user = User.query.get(payload.get('user_id'))
            except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
                pass
    if not user:
        return jsonify({"message": "Unauthorized"}), 401
    parts_path = filepath.split('/')
    if len(parts_path) >= 1:
        try:
            int(parts_path[0])
        except (ValueError, IndexError):
            return jsonify({"message": "Invalid path"}), 400
    msg = Message.query.filter_by(
        attachment_path=f"messages/{filepath}"
    ).filter(
        or_(Message.sender_id == user.id, Message.receiver_id == user.id)
    ).first()
    if not msg:
        return jsonify({"message": "Forbidden"}), 403
    from flask import send_from_directory
    upload_folder = app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filepath)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_messaging_files.py -v`

Expected: Both tests PASS.

- [ ] **Step 5: Run all tests**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v 2>&1 | tail -10`

Expected: All pass.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_messaging_files.py
git commit -m "fix: accept JWT from query param in file serving endpoint

Browser-initiated requests (img src, a href, window.open) cannot
send Authorization headers. The file serving endpoint now checks
request.args.get('token') as a fallback when the header is missing."
```

---

### Task 2: Fix Frontend — Append Token to Attachment URLs

**Problem:** The frontend renders attachment URLs without the JWT token, so the browser gets 401.

**Files:**
- Modify: `frontend/src/pages/Messages.jsx`

- [ ] **Step 1: Add a helper function for authenticated attachment URLs**

In `Messages.jsx`, add this helper inside the component (after line 88, after the `isImage` function):

```javascript
  function attachUrl(path) {
    const token = localStorage.getItem('token');
    return `/api/uploads/${path}${token ? `?token=${token}` : ''}`;
  }
```

- [ ] **Step 2: Replace all attachment URL references**

Replace the three places that build attachment URLs:

**Line 141** (image src):
```jsx
                        src={`/api/uploads/${msg.attachment_path}`}
```
becomes:
```jsx
                        src={attachUrl(msg.attachment_path)}
```

**Line 144** (image click-to-open):
```jsx
                        onClick={() => window.open(`/api/uploads/${msg.attachment_path}`)}
```
becomes:
```jsx
                        onClick={() => window.open(attachUrl(msg.attachment_path))}
```

**Line 149** (file download link):
```jsx
                        href={`/api/uploads/${msg.attachment_path}`}
```
becomes:
```jsx
                        href={attachUrl(msg.attachment_path)}
```

- [ ] **Step 3: Verify build**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx webpack --mode development 2>&1 | tail -3`

Expected: compiled successfully

- [ ] **Step 4: Run frontend tests**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx jest --verbose 2>&1 | tail -10`

Expected: 15/15 pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Messages.jsx
git commit -m "fix: append JWT token to attachment URLs for browser access

Browser-initiated requests (img src, a href) cannot send Authorization
headers. Adds attachUrl() helper that appends ?token=xxx to all
attachment URLs so the backend can authenticate file downloads."
```

---

### Task 3: Add Thread Header with Partner Info

**Problem:** When a conversation is open, there's no header showing who you're talking to. Users lose context, especially on mobile.

**Files:**
- Modify: `frontend/src/pages/Messages.jsx`
- Modify: `frontend/src/pages/Messages.css`

- [ ] **Step 1: Add thread header JSX**

In `Messages.jsx`, find the thread panel rendering (inside the `activePartnerId` branch). Currently it starts with the back button. After the back button (line 132, after `</button>`), add:

```jsx
            <div className="thread-header">
              <button
                className="thread-back-btn"
                onClick={() => setActivePartnerId(null)}
                aria-label="Back to conversations"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>
              <div className="thread-header-avatar">
                {(conversations.find(c => c.partner_id === activePartnerId)?.partner_name || '??').slice(0, 2).toUpperCase()}
              </div>
              <span className="thread-header-name">
                {conversations.find(c => c.partner_id === activePartnerId)?.partner_name || 'Unknown'}
              </span>
            </div>
```

And **remove** the old standalone back button (lines 126-132):
```jsx
            <button
              className="thread-back-btn"
              onClick={() => setActivePartnerId(null)}
              aria-label="Back to conversations"
            >
              ← Back
            </button>
```

- [ ] **Step 2: Add thread header CSS**

Add to `Messages.css`, before the `@media` query:

```css
/* Thread header */
.thread-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.thread-header-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary-light);
  color: var(--color-primary-dark);
  font-weight: 700;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.thread-header-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text);
}
```

Update the `.thread-back-btn` rule. Replace the existing desktop rule (line 228-230):
```css
.thread-back-btn {
  display: none;
}
```
with:
```css
.thread-back-btn {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-primary);
  padding: 4px;
  border-radius: 6px;
  line-height: 1;
}
.thread-back-btn:hover {
  background: var(--color-primary-light);
}
```

And in the `@media (max-width: 768px)` section, replace the `.thread-back-btn` block:
```css
  .thread-back-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
    border: none;
    background: #fff;
    border-bottom: 1px solid var(--color-border);
    font-size: 14px;
    font-weight: 600;
    color: var(--color-primary);
    cursor: pointer;
    font-family: var(--font);
  }
```
with:
```css
  .thread-back-btn {
    display: flex;
  }
```

- [ ] **Step 3: Verify build**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx webpack --mode development 2>&1 | tail -3`

Expected: compiled successfully

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Messages.jsx frontend/src/pages/Messages.css
git commit -m "feat: add thread header with partner name and avatar

Shows who you're talking to at the top of the message thread.
Includes back button on mobile with a chevron SVG icon."
```

---

### Task 4: Fix Design System Consistency — CSS Variables, Icons, and Polish

**Problem:** The Messages page has hardcoded colors, emoji icons, and missing error styling.

**Files:**
- Modify: `frontend/src/pages/Messages.jsx`
- Modify: `frontend/src/pages/Messages.css`

- [ ] **Step 1: Fix hardcoded unread badge color**

In `Messages.css` line 65, change:
```css
  background: #ef4444;
```
to:
```css
  background: var(--color-danger);
```

- [ ] **Step 2: Replace emoji attach button with SVG icon**

In `Messages.jsx`, replace the attach label (lines 182-190):

```jsx
              <label className="attach-btn" title="Attach file">
                📎
                <input
                  type="file"
                  accept="image/*,.pdf,.doc,.docx"
                  style={{ display: 'none' }}
                  onChange={e => setAttachment(e.target.files[0] || null)}
                />
              </label>
```

with:

```jsx
              <label className="attach-btn" title="Attach file">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                </svg>
                <input
                  type="file"
                  accept="image/*,.pdf,.doc,.docx"
                  style={{ display: 'none' }}
                  onChange={e => setAttachment(e.target.files[0] || null)}
                />
              </label>
```

- [ ] **Step 3: Replace emoji file link icon with SVG**

In `Messages.jsx`, replace the file attachment link rendering (lines 147-155):

```jsx
                    {msg.attachment_path && !isImage(msg.attachment_type) && (
                      <a
                        href={attachUrl(msg.attachment_path)}
                        target="_blank"
                        rel="noreferrer"
                        className="msg-file-link"
                      >
                        📎 {msg.attachment_name}
                      </a>
                    )}
```

with:

```jsx
                    {msg.attachment_path && !isImage(msg.attachment_type) && (
                      <a
                        href={attachUrl(msg.attachment_path)}
                        target="_blank"
                        rel="noreferrer"
                        className="msg-file-link"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                        </svg>
                        {msg.attachment_name}
                      </a>
                    )}
```

- [ ] **Step 4: Replace emoji in attachment preview**

In `Messages.jsx`, replace the attachment preview (lines 170-174):

```jsx
              {attachment && (
                <div className="attachment-preview">
                  📎 {attachment.name}
                  <button type="button" onClick={() => setAttachment(null)}>✕</button>
                </div>
              )}
```

with:

```jsx
              {attachment && (
                <div className="attachment-preview">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  {attachment.name}
                  <button type="button" onClick={() => setAttachment(null)} aria-label="Remove attachment">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              )}
```

- [ ] **Step 5: Fix "Send" button loading text**

In `Messages.jsx`, replace the send button (lines 191-197):

```jsx
              <button
                type="submit"
                className="btn-primary"
                disabled={sending || (!messageText.trim() && !attachment)}
              >
                {sending ? '...' : 'Send'}
              </button>
```

with:

```jsx
              <button
                type="submit"
                className="btn-primary send-btn"
                disabled={sending || (!messageText.trim() && !attachment)}
              >
                {sending ? 'Sending' : 'Send'}
              </button>
```

- [ ] **Step 6: Add error banner and attachment icon CSS**

Add to `Messages.css` before the `@media` query:

```css
/* Error banner */
.messages-page .error-banner {
  padding: 10px 16px;
  background: var(--color-danger-light);
  color: var(--color-danger);
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}

/* Attach button polish */
.attach-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-muted);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.15s;
}
.attach-btn:hover {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

/* Send button sizing */
.send-btn {
  border-radius: 20px;
  padding: 10px 20px;
}
```

And remove the old `.attach-btn` rule (lines 201-206):
```css
.attach-btn {
  font-size: 18px;
  cursor: pointer;
  padding: 6px;
  line-height: 1;
}
```

- [ ] **Step 7: Verify build**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx webpack --mode development 2>&1 | tail -3`

Expected: compiled successfully

- [ ] **Step 8: Run frontend tests**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx jest --verbose 2>&1 | tail -10`

Expected: 15/15 pass.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/pages/Messages.jsx frontend/src/pages/Messages.css
git commit -m "fix(messages): replace emojis with SVGs, use design system variables

Replaces emoji 📎 and ✕ with SVG icons for attach button, file links,
and attachment preview. Fixes hardcoded #ef4444 to --color-danger.
Adds error banner styling and polishes attach/send button design."
```

---

## Quick Reference

| Task | What | Files | Severity |
|------|------|-------|----------|
| 1 | Backend: accept JWT from query param for file serving | `app.py`, `tests/test_messaging_files.py` | Critical |
| 2 | Frontend: append token to all attachment URLs | `Messages.jsx` | Critical |
| 3 | Add thread header with partner name/avatar | `Messages.jsx`, `Messages.css` | Medium |
| 4 | Design system consistency: SVG icons, CSS vars, polish | `Messages.jsx`, `Messages.css` | Low |
