# Part 4: Frontend Polish — Responsive CSS, Visual Highlighting, Error Boundaries

[Back to plan index](2026-04-04-fixes-and-features-plan-index.md)

---

## Task 6: Responsive CSS

**Files:**
- Modify: `frontend/src/components/Navbar.jsx` and `frontend/src/components/Navbar.css`
- Modify: `frontend/src/pages/Jobs.css`
- Modify: `frontend/src/Profile.css`
- Modify: `frontend/src/CreateJobPost.css`
- Modify: `frontend/src/pages/Dashboard.css`
- Modify: `frontend/src/pages/MyJobs.css`
- Modify: `frontend/src/pages/Messages.css`
- Modify: `frontend/src/pages/Applications.css`
- Modify: `frontend/src/pages/Applicants.css`
- Modify: `frontend/src/components/AuthCard.css`

### Step 1: Add responsive hamburger menu to Navbar

- [ ] **Modify Navbar.jsx — add hamburger toggle state**

In `frontend/src/components/Navbar.jsx`, add state for mobile menu:

```javascript
const [menuOpen, setMenuOpen] = useState(false);
```

Add a hamburger button in the JSX (visible only on mobile):
```jsx
<button className="nav-hamburger" onClick={() => setMenuOpen(!menuOpen)}
  aria-label="Toggle menu">
  {menuOpen ? '✕' : '☰'}
</button>
```

Add `className={`nav-links ${menuOpen ? 'nav-links-open' : ''}`}` to the nav links container.

- [ ] **Add responsive styles to Navbar.css**

Append to `frontend/src/components/Navbar.css`:

```css
.nav-hamburger {
  display: none;
  background: none;
  border: none;
  font-size: 24px;
  color: white;
  cursor: pointer;
  padding: 4px 8px;
}

@media (max-width: 768px) {
  .nav-hamburger {
    display: block;
  }

  .nav-links {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: inherit;
    flex-direction: column;
    padding: 12px 16px;
    gap: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 100;
  }

  .nav-links-open {
    display: flex;
  }

  .navbar {
    position: relative;
  }
}
```

### Step 2: Add responsive styles to all page CSS files

- [ ] **Append responsive rules to Jobs.css**

```css
@media (max-width: 768px) {
  .jobs-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .jobs-filters {
    flex-direction: column;
    gap: 8px;
  }

  .jobs-card {
    padding: 16px;
  }

  .jobs-modal-content {
    width: 95%;
    margin: 20px auto;
    max-height: 90vh;
  }
}
```

- [ ] **Append responsive rules to Profile.css**

```css
@media (max-width: 768px) {
  .profile-form {
    padding: 16px;
  }

  .profile-form .form-row {
    flex-direction: column;
    gap: 0;
  }

  .profile-form input,
  .profile-form textarea,
  .profile-form select {
    width: 100%;
  }

  .profile-page {
    padding: 12px;
  }
}
```

- [ ] **Append responsive rules to CreateJobPost.css**

```css
@media (max-width: 768px) {
  .create-job-form {
    padding: 16px;
    margin: 12px;
  }

  .create-job-form .form-row {
    flex-direction: column;
    gap: 0;
  }

  .create-job-form input,
  .create-job-form textarea,
  .create-job-form select {
    width: 100%;
  }
}
```

- [ ] **Append responsive rules to Dashboard.css**

```css
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .dashboard-page {
    padding: 12px;
  }

  .stat-card {
    padding: 16px;
  }

  .quick-actions {
    flex-direction: column;
    gap: 8px;
  }
}
```

- [ ] **Append responsive rules to MyJobs.css**

```css
@media (max-width: 768px) {
  .my-jobs-grid {
    grid-template-columns: 1fr;
  }

  .my-jobs-page {
    padding: 12px;
  }

  .job-card-actions {
    flex-direction: column;
    gap: 6px;
  }
}
```

- [ ] **Append responsive rules to Messages.css**

```css
@media (max-width: 768px) {
  .messages-layout {
    flex-direction: column;
  }

  .messages-sidebar {
    width: 100%;
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }

  .messages-thread {
    width: 100%;
  }

  .messages-page {
    padding: 0;
  }
}
```

- [ ] **Append responsive rules to Applications.css**

```css
@media (max-width: 768px) {
  .applications-list {
    gap: 12px;
  }

  .application-card {
    padding: 12px;
  }

  .applications-page {
    padding: 12px;
  }
}
```

- [ ] **Append responsive rules to Applicants.css**

```css
@media (max-width: 768px) {
  .applicants-table {
    display: block;
    overflow-x: auto;
  }

  .applicants-page {
    padding: 12px;
  }

  .applicant-card {
    padding: 12px;
  }
}
```

- [ ] **Append responsive rules to AuthCard.css**

```css
@media (max-width: 768px) {
  .auth-card {
    margin: 16px;
    padding: 24px 16px;
    max-width: 100%;
  }

  .auth-page {
    padding: 12px;
  }
}
```

Note: The exact class names above may not all exist — when implementing, check the actual CSS file for the correct selectors and adjust the media queries to target the actual layout containers. The key principle is: flex containers with `flex-direction: row` should become `column` on mobile, grids should become `1fr`, and padding should be reduced.

### Step 3: Commit

- [ ] **Commit responsive CSS**

```bash
cd "E:/Projects/Intelligent job matching website"
git add frontend/src/components/Navbar.jsx frontend/src/components/Navbar.css \
  frontend/src/pages/Jobs.css frontend/src/Profile.css frontend/src/CreateJobPost.css \
  frontend/src/pages/Dashboard.css frontend/src/pages/MyJobs.css \
  frontend/src/pages/Messages.css frontend/src/pages/Applications.css \
  frontend/src/pages/Applicants.css frontend/src/components/AuthCard.css
git commit -m "feat: add responsive CSS for mobile and tablet

Adds media queries at 768px breakpoint for all pages. Navbar gets
hamburger menu on mobile. Grids stack vertically. Forms go full-width.
Implements PDF req 2.1.2 #2."
```

---

## Task 7: Visual Highlighting of Skills

**Files:**
- Modify: `frontend/src/pages/Jobs.jsx`
- Modify: `frontend/src/pages/Jobs.css`
- Modify: `frontend/src/pages/Applicants.jsx`
- Modify: `frontend/src/pages/Applicants.css`

### Step 1: Add skill highlighting to Jobs.jsx

- [ ] **Add match bar component to Jobs.jsx**

In `frontend/src/pages/Jobs.jsx`, add this component before the main `Jobs` export (after the existing `MatchBadge` component around line 50):

```jsx
function MatchBar({ score }) {
  if (score == null) return null;
  const pct = Math.round(score);
  let color = '#4F46E5';
  if (pct >= 80) color = '#16a34a';
  else if (pct >= 50) color = '#f59e0b';
  else color = '#9CA3AF';
  return (
    <div className="jobs-match-bar-container">
      <div className="jobs-match-bar">
        <div className="jobs-match-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="jobs-match-bar-label">{pct}%</span>
    </div>
  );
}

function SkillChip({ skill, matched }) {
  return (
    <span className={`jobs-skill-chip ${matched ? 'jobs-skill-matched' : 'jobs-skill-missing'}`}>
      {skill}
    </span>
  );
}
```

- [ ] **Use SkillChip and MatchBar in the job detail modal**

In the job detail modal/card section where skills are displayed, replace the plain skill text with:

```jsx
{/* Replace existing skill display with this */}
<div className="jobs-skills-section">
  <h4>Required Skills</h4>
  <div className="jobs-skill-chips">
    {(job.required_skills || '').split(',').filter(Boolean).map(skill => {
      const trimmed = skill.trim();
      const isMatched = (job.matched_skills || []).map(s => s.toLowerCase()).includes(trimmed.toLowerCase());
      return <SkillChip key={trimmed} skill={trimmed} matched={isMatched} />;
    })}
  </div>
</div>

{job.missing_skills && job.missing_skills.length > 0 && (
  <div className="jobs-skills-section">
    <h4>Skills to Develop</h4>
    <div className="jobs-skill-chips">
      {job.missing_skills.map(skill => (
        <SkillChip key={skill} skill={skill} matched={false} />
      ))}
    </div>
  </div>
)}

{job.match_score != null && <MatchBar score={job.match_score} />}
```

- [ ] **Add styles to Jobs.css**

Append to `frontend/src/pages/Jobs.css`:

```css
/* Match bar */
.jobs-match-bar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.jobs-match-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.jobs-match-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.jobs-match-bar-label {
  font-size: 13px;
  font-weight: 600;
  min-width: 36px;
}

/* Skill chips */
.jobs-skill-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.jobs-skill-chip {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.jobs-skill-matched {
  background: #DCFCE7;
  color: #166534;
}

.jobs-skill-missing {
  background: #FEF3C7;
  color: #92400E;
}

.jobs-skills-section {
  margin-top: 12px;
}

.jobs-skills-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 4px;
}
```

### Step 2: Add skill highlighting to Applicants.jsx

- [ ] **Add SkillChip and MatchBar to Applicants.jsx**

In `frontend/src/pages/Applicants.jsx`, add the same `SkillChip` and `MatchBar` components (or extract to shared file if preferred — for speed, duplicate is fine):

```jsx
function MatchBar({ score }) {
  const pct = Math.round(score);
  let color = '#4F46E5';
  if (pct >= 80) color = '#16a34a';
  else if (pct >= 50) color = '#f59e0b';
  else color = '#9CA3AF';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
      <div style={{ flex: 1, height: '8px', background: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: '4px' }} />
      </div>
      <span style={{ fontSize: '13px', fontWeight: 600 }}>{pct}%</span>
    </div>
  );
}
```

In the applicant card where skills are shown, use color-coded chips:

```jsx
<div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
  {(applicant.matched_skills || []).map(s => (
    <span key={s} style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '12px',
      background: '#DCFCE7', color: '#166534' }}>{s}</span>
  ))}
  {(applicant.missing_skills || []).map(s => (
    <span key={s} style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '12px',
      background: '#FEF3C7', color: '#92400E' }}>{s}</span>
  ))}
</div>
{applicant.match_score != null && <MatchBar score={applicant.match_score} />}
```

### Step 3: Commit

- [ ] **Commit visual highlighting**

```bash
cd "E:/Projects/Intelligent job matching website"
git add frontend/src/pages/Jobs.jsx frontend/src/pages/Jobs.css \
  frontend/src/pages/Applicants.jsx frontend/src/pages/Applicants.css
git commit -m "feat: add visual skill highlighting and match bars

Matched skills shown in green, missing skills in amber. Match score
displayed as progress bar. Implements PDF req 2.1.2 #6."
```

---

## Task 8: Error Boundary & Global 401 Handling

**Files:**
- Create: `frontend/src/components/ErrorBoundary.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/api.js`

### Step 1: Create ErrorBoundary component

- [ ] **Create frontend/src/components/ErrorBoundary.jsx**

```jsx
import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: '60vh', padding: '24px',
          textAlign: 'center',
        }}>
          <h2 style={{ fontSize: '24px', marginBottom: '12px', color: '#1f2937' }}>
            Something went wrong
          </h2>
          <p style={{ color: '#6b7280', marginBottom: '24px', maxWidth: '400px' }}>
            An unexpected error occurred. Please try refreshing the page.
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            style={{
              padding: '10px 24px', borderRadius: '8px', border: 'none',
              background: '#4F46E5', color: 'white', cursor: 'pointer',
              fontSize: '14px', fontWeight: 600,
            }}
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Step 2: Wrap App with ErrorBoundary

- [ ] **Modify App.jsx**

Add import at top of `frontend/src/App.jsx`:
```javascript
import ErrorBoundary from './components/ErrorBoundary';
```

Wrap the Router in the default export:
```jsx
export default function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AppContent />
      </Router>
    </ErrorBoundary>
  );
}
```

### Step 3: Add global 401 handling to api.js

- [ ] **Add auth error interceptor to api.js**

At the top of `frontend/src/api.js`, add a helper function:

```javascript
function handleAuthError(res) {
  if (res.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Session expired. Please log in again.');
  }
  return res;
}
```

Then in each exported function that makes authenticated requests, add `handleAuthError` after the fetch. For example, update `getProfile`:

```javascript
export async function getProfile() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/profile', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  handleAuthError(res);
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}
```

Apply the same pattern to all functions that use `Bearer ${token}`:
- `fetchJobPosts`
- `fetchJobMatches`
- `getProfile`
- `updateProfile`
- `applyForJob`
- `fetchMyApplications`
- `withdrawApplication`
- `updateJobPost`
- `deleteJobPost`
- `fetchJobApplicants`
- `updateApplicationStatus`
- `fetchEmployerDashboard`
- `fetchConversations`
- `fetchThread`
- `sendMessage`
- `markThreadRead`
- `fetchUnreadCount`

For `fetchUnreadCount`, keep the existing catch that returns 0, but add the auth check before it.

### Step 4: Commit

- [ ] **Commit error boundary and 401 handling**

```bash
cd "E:/Projects/Intelligent job matching website"
git add frontend/src/components/ErrorBoundary.jsx frontend/src/App.jsx frontend/src/api.js
git commit -m "feat: add error boundary and global JWT expiry handling

ErrorBoundary catches render crashes. All API calls redirect to login
on 401 (expired JWT). Improves reliability and user experience."
```
