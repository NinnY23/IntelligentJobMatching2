# Sprint 7: Polish & Missing Features — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up the "Message Employer" and "Message" buttons, add mobile responsiveness to the Messages page, show read receipts on sent messages, and remove the stale JobMatch.jsx file.

**Architecture:** All changes are frontend-only React/CSS edits. No backend changes required. The messaging deep-link pattern uses React Router's `useSearchParams` to pass a pre-selected partner ID in the URL (`/messages?partner=<id>`), so Jobs and Applicants pages can navigate directly into a conversation without any new API endpoints.

**Tech Stack:** React 19, React Router 6 (`useNavigate`, `useSearchParams`), CSS custom properties, Webpack 5

---

## File Map

| File | Change |
|---|---|
| `frontend/src/pages/Jobs.jsx` | Add `useNavigate`, pass `onMessageEmployer` to `JobModal`, add "Message Employer" button in modal |
| `frontend/src/pages/Messages.jsx` | Read `?partner=` URL param on mount to pre-select conversation; add "← Back" button for mobile |
| `frontend/src/pages/Messages.css` | Add `@media (max-width: 768px)` breakpoint — single-column layout with panel toggling |
| `frontend/src/pages/Applicants.jsx` | Add `useNavigate`, add "Message" button per applicant row |
| `frontend/src/JobMatch.jsx` | Delete (stale) |
| `frontend/src/JobMatch.css` | Delete (stale) |

---

## Task 7.1: "Message Employer" button in the Jobs modal

**Files:**
- Modify: `frontend/src/pages/Jobs.jsx`
- Modify: `frontend/src/pages/Messages.jsx`

### Context

`JobModal` (line 95 of Jobs.jsx) currently renders one button — "Apply Now" — inside `.jobs-modal-actions`.

`Jobs()` (line 289) reads user from localStorage and uses `isEmployee` to gate employee-only UI.

`Messages.jsx` (line 5) initialises `activePartnerId` to `null` and never reads the URL.

### Changes

**Jobs.jsx — three edits:**

1. Add `useNavigate` to the React Router import.
2. In `Jobs()`, instantiate `navigate` and pass a callback to `JobModal`.
3. In `JobModal`, accept `onMessageEmployer` prop and render the button.

**Messages.jsx — one edit:**

Add `useSearchParams` import and a one-time effect that reads the `partner` query param on mount.

---

- [ ] **Step 1: Edit the React Router import in Jobs.jsx**

Find line 3 of `frontend/src/pages/Jobs.jsx`:
```js
import React, { useState, useEffect } from 'react';
```
It has no React Router import. Add one after it (line 4 area does not import react-router-dom currently — verify first):

If there is no existing react-router-dom import, add after line 3:
```js
import { useNavigate } from 'react-router-dom';
```

- [ ] **Step 2: Add `navigate` to the `Jobs()` function**

In `Jobs()` (starts around line 289), after the existing state declarations (after `const [minMatch, setMinMatch] = useState(0);`), add:
```js
const navigate = useNavigate();
```

- [ ] **Step 3: Pass `onMessageEmployer` to `JobModal`**

Find where `<JobModal` is rendered in the `Jobs` return (it will be something like `{selectedJob && <JobModal job={selectedJob} ...`). Add one prop:
```jsx
onMessageEmployer={(employerId) => navigate(`/messages?partner=${employerId}`)}
```

The full `JobModal` invocation should look like:
```jsx
{selectedJob && (
  <JobModal
    job={selectedJob}
    onClose={() => setSelectedJob(null)}
    isEmployee={isEmployee}
    onMessageEmployer={(employerId) => navigate(`/messages?partner=${employerId}`)}
  />
)}
```

- [ ] **Step 4: Accept `onMessageEmployer` in `JobModal` and render the button**

`JobModal` signature is currently:
```js
function JobModal({ job, onClose, isEmployee }) {
```

Change to:
```js
function JobModal({ job, onClose, isEmployee, onMessageEmployer }) {
```

Then find the `.jobs-modal-actions` div (currently contains only the "Apply Now" button). Replace it with:
```jsx
{isEmployee && (
  <div className="jobs-modal-actions">
    <button
      className="jobs-apply-btn"
      onClick={handleApply}
      disabled={applying}
    >
      {applying ? 'Submitting…' : 'Apply Now'}
    </button>
    {job.employer_id && (
      <button
        className="jobs-message-btn"
        onClick={() => onMessageEmployer(job.employer_id)}
      >
        Message Employer
      </button>
    )}
  </div>
)}
```

- [ ] **Step 5: Add `.jobs-message-btn` style to Jobs.css**

Read `frontend/src/pages/Jobs.css` to find where `.jobs-apply-btn` is defined, then add after it:
```css
.jobs-message-btn {
  padding: 10px 24px;
  border: 1.5px solid var(--color-primary);
  border-radius: var(--radius);
  background: transparent;
  color: var(--color-primary);
  font-size: 15px;
  font-weight: 600;
  font-family: var(--font);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.jobs-message-btn:hover {
  background: var(--color-primary-light);
}
```

- [ ] **Step 6: Add `useSearchParams` to Messages.jsx**

In `frontend/src/pages/Messages.jsx`, the import on line 1 is:
```js
import React, { useState, useEffect, useRef } from 'react';
```

Add after it:
```js
import { useSearchParams } from 'react-router-dom';
```

- [ ] **Step 7: Read `?partner=` param in Messages.jsx**

Inside `Messages({ user })`, after all the existing `useState`/`useRef` declarations and before the first `useEffect`, add:
```js
const [searchParams] = useSearchParams();

useEffect(() => {
  const partnerId = searchParams.get('partner');
  if (partnerId) {
    setActivePartnerId(Number(partnerId));
  }
}, []);
```

- [ ] **Step 8: Verify the build compiles**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -20
```

Expected: `successfully compiled` (or webpack output with no errors). If there are errors, fix them before proceeding.

- [ ] **Step 9: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add frontend/src/pages/Jobs.jsx frontend/src/pages/Jobs.css frontend/src/pages/Messages.jsx && git commit -m "feat: wire Message Employer button and deep-link to conversation"
```

---

## Task 7.2: "Message" button on Applicants rows

**Files:**
- Modify: `frontend/src/pages/Applicants.jsx`

### Context

`Applicants.jsx` shows a table of candidates. Each row has an `Actions` column with Shortlist/Unshortlist buttons. The applicant data already includes `user_id` (returned by `GET /api/job-posts/<id>/applicants`).

---

- [ ] **Step 1: Add `useNavigate` import to Applicants.jsx**

Line 2 of `frontend/src/pages/Applicants.jsx` is:
```js
import React, { useState, useEffect } from 'react';
```

Add after it:
```js
import { useNavigate } from 'react-router-dom';
```

- [ ] **Step 2: Instantiate `navigate` in the component**

Inside `Applicants({ jobId })`, after `const [message, setMessage] = useState('');` add:
```js
const navigate = useNavigate();
```

- [ ] **Step 3: Add the Message button to each row's Actions cell**

Find the Actions `<td>` block (around line 163). It currently contains the Shortlist/Unshortlist buttons. Add a Message button after the existing buttons:

```jsx
<td>
  {a.status !== 'shortlisted' && (
    <button
      className="btn-sm"
      onClick={() => handleStatusChange(a.application_id, 'shortlisted')}
    >
      Shortlist
    </button>
  )}
  {a.status === 'shortlisted' && (
    <button
      className="btn-sm"
      onClick={() => handleStatusChange(a.application_id, 'pending')}
    >
      Unshortlist
    </button>
  )}
  {' '}
  <button
    className="btn-sm"
    onClick={() => navigate(`/messages?partner=${a.user_id}`)}
  >
    Message
  </button>
</td>
```

- [ ] **Step 4: Verify build compiles**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -20
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add frontend/src/pages/Applicants.jsx && git commit -m "feat: add Message button to applicants table row"
```

---

## Task 7.3: Responsive layout for Messages page

**Files:**
- Modify: `frontend/src/pages/Messages.jsx`
- Modify: `frontend/src/pages/Messages.css`

### Context

On mobile (≤768px), the two-column grid (280px sidebar + thread) won't fit. The fix:
- Single column layout on mobile
- Show conversations panel when `activePartnerId` is null
- Show thread panel when `activePartnerId` is set
- Add a "← Back" button in the thread panel that resets `activePartnerId` to `null`

The root `.messages-page` div gets a conditional class `has-active` when a conversation is open. CSS uses this to toggle visibility.

---

- [ ] **Step 1: Add `has-active` class to the root div in Messages.jsx**

In `Messages.jsx`, find the return statement's root element:
```jsx
<div className="messages-page">
```

Change it to:
```jsx
<div className={`messages-page${activePartnerId ? ' has-active' : ''}`}>
```

- [ ] **Step 2: Add a "← Back" button in the thread panel**

In the thread panel's JSX, find the `{!activePartnerId ? ... : <> ... </>}` block. Inside the `<>` (when a conversation IS active), add a back button as the first element:

```jsx
<>
  <button
    className="thread-back-btn"
    onClick={() => setActivePartnerId(null)}
    aria-label="Back to conversations"
  >
    ← Back
  </button>
  <div className="thread-messages">
    {/* existing thread messages */}
  </div>
  {/* existing error banner and form */}
</>
```

The `thread-back-btn` is hidden on desktop (display:none) and visible only on mobile — handled in CSS.

- [ ] **Step 3: Add responsive CSS to Messages.css**

Append to the end of `frontend/src/pages/Messages.css`:

```css
.thread-back-btn {
  display: none;
}

@media (max-width: 768px) {
  .messages-page {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr;
  }

  /* When no conversation is selected: show conversations, hide thread */
  .messages-page:not(.has-active) .conversations-panel {
    display: block;
  }
  .messages-page:not(.has-active) .thread-panel {
    display: none;
  }

  /* When a conversation is selected: hide conversations, show thread */
  .messages-page.has-active .conversations-panel {
    display: none;
  }
  .messages-page.has-active .thread-panel {
    display: flex;
  }

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
}
```

- [ ] **Step 4: Verify build compiles**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -20
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add frontend/src/pages/Messages.jsx frontend/src/pages/Messages.css && git commit -m "feat: responsive Messages page with mobile panel toggling"
```

---

## Task 7.4: Read receipt indicator on sent messages

**Files:**
- Modify: `frontend/src/pages/Messages.jsx`
- Modify: `frontend/src/pages/Messages.css`

### Context

The `Message.to_dict()` returns `"read": true/false`. When a message is in the thread, `msg.read` is available. For messages the current user sent (`isMine === true`), show a small `✓` when `msg.read === true` to indicate the recipient has read it.

---

- [ ] **Step 1: Add the read indicator to message bubbles in Messages.jsx**

Find the `<span className="msg-time">` element inside the message bubble render (around line 143). Change it from:
```jsx
<span className="msg-time">
  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
</span>
```

To:
```jsx
<span className="msg-time">
  {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
  {isMine && msg.read && <span className="msg-read-tick" aria-label="Read"> ✓</span>}
</span>
```

- [ ] **Step 2: Add `.msg-read-tick` style to Messages.css**

Append to `frontend/src/pages/Messages.css`:
```css
.msg-read-tick {
  opacity: 0.85;
  font-size: 11px;
  margin-left: 3px;
}
```

- [ ] **Step 3: Verify build compiles**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -20
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add frontend/src/pages/Messages.jsx frontend/src/pages/Messages.css && git commit -m "feat: show read receipt tick on sent messages"
```

---

## Task 7.5: Remove stale JobMatch files

**Files:**
- Delete: `frontend/src/JobMatch.jsx`
- Delete: `frontend/src/JobMatch.css`

### Context

`frontend/src/JobMatch.jsx` and `frontend/src/JobMatch.css` are the old job listing page from before Sprint 3. The active page is `frontend/src/pages/Jobs.jsx`. `JobMatch.jsx` is not imported anywhere in `App.jsx`.

---

- [ ] **Step 1: Confirm JobMatch.jsx is not imported anywhere**

Run:
```bash
cd "E:\Projects\Intelligent job matching website" && grep -r "JobMatch" frontend/src/App.jsx frontend/src/index.jsx 2>&1
```

Expected: no output (not imported). If it IS imported somewhere, fix the import to point to `./pages/Jobs` before deleting.

- [ ] **Step 2: Delete the stale files**

```bash
cd "E:\Projects\Intelligent job matching website" && rm frontend/src/JobMatch.jsx frontend/src/JobMatch.css
```

- [ ] **Step 3: Verify build still compiles**

```bash
cd "E:\Projects\Intelligent job matching website\frontend" && npm run build 2>&1 | tail -20
```

Expected: no errors. If errors appear referencing JobMatch, a file still imports it — fix that import first.

- [ ] **Step 4: Run backend tests to confirm no regressions**

```bash
cd "E:\Projects\Intelligent job matching website" && python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: `69 passed`.

- [ ] **Step 5: Commit**

```bash
cd "E:\Projects\Intelligent job matching website" && git add -A && git commit -m "chore: remove stale JobMatch.jsx and JobMatch.css"
```

---

## Self-Review

**Spec coverage:**
- ✅ "Message Employer" button in job detail modal (Task 7.1)
- ✅ "Message" button per applicant row (Task 7.2)
- ✅ Messages page responsive / mobile layout (Task 7.3)
- ✅ Read receipts on sent messages (Task 7.4)
- ✅ Stale files removed (Task 7.5)

**Placeholder scan:** All steps contain exact code. No TBDs.

**Type consistency:**
- `job.employer_id` — present in `Job.to_dict()` ✓
- `a.user_id` — present in `GET /api/job-posts/<id>/applicants` response ✓
- `msg.read` — present in `Message.to_dict()` ✓
- `activePartnerId` — already `Number | null` in Messages.jsx ✓
- `Number(partnerId)` converts string from URL param to match existing `=== user.id` comparison (which is a number) ✓
