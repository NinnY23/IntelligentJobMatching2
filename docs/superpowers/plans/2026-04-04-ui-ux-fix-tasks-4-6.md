# UI/UX Fix — Tasks 4–6

> See `2026-04-04-ui-ux-consistency-fix-overview.md` for context and design system reference.

---

### Task 4: Fix Applicants.jsx Inline Styles

**Problem:** The Applicants page has (1) a MatchBar component with 100% inline styles (duplicate of the CSS-based version in Jobs.jsx), (2) status chips with inline styles instead of global CSS classes, and (3) SCORE_COLOR function used for inline badge coloring.

**Files:**
- Modify: `frontend/src/pages/Applicants.jsx`
- Modify: `frontend/src/pages/Applicants.css`

- [ ] **Step 1: Add MatchBar and score badge CSS to Applicants.css**

Add before the `@media` queries in `Applicants.css`:

```css
/* Match bar — same pattern as Jobs.css */
.applicants-match-bar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.applicants-match-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}
.applicants-match-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}
.applicants-match-bar-label {
  font-size: 13px;
  font-weight: 600;
  min-width: 36px;
}

/* Score badge colors */
.score-badge--high { background: var(--color-success); }
.score-badge--mid { background: var(--color-primary); }
.score-badge--low { background: var(--color-muted); }
```

- [ ] **Step 2: Replace inline MatchBar component with CSS-based version**

In `Applicants.jsx`, replace the MatchBar component (lines 13–27):

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

with:

```jsx
function MatchBar({ score }) {
  const pct = Math.round(score);
  let color = 'var(--color-primary)';
  if (pct >= 80) color = 'var(--color-success)';
  else if (pct >= 50) color = '#f59e0b';
  else color = 'var(--color-muted)';
  return (
    <div className="applicants-match-bar-container">
      <div className="applicants-match-bar">
        <div className="applicants-match-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="applicants-match-bar-label">{pct}%</span>
    </div>
  );
}
```

Note: The `width` and `background` remain as inline styles because they are dynamic values per-row. The structural layout moves to CSS.

- [ ] **Step 3: Replace SCORE_COLOR inline badge with CSS classes**

Replace the `SCORE_COLOR` function (lines 7–11):

```jsx
const SCORE_COLOR = score => {
  if (score >= 80) return '#16a34a';
  if (score >= 50) return '#4F46E5';
  return '#9ca3af';
};
```

with a helper that returns a CSS class modifier:

```jsx
const scoreClass = score => {
  if (score >= 80) return 'score-badge--high';
  if (score >= 50) return 'score-badge--mid';
  return 'score-badge--low';
};
```

Then in the table row (line 134–139), replace:

```jsx
<span
  className="score-badge"
  style={{ background: SCORE_COLOR(a.match_score) }}
>
  {a.match_score}%
</span>
```

with:

```jsx
<span className={`score-badge ${scoreClass(a.match_score)}`}>
  {a.match_score}%
</span>
```

Do the same in the profile modal (lines 261–264):

```jsx
<span
  className="score-badge"
  style={{ background: SCORE_COLOR(profileTarget.match_score) }}
>
  {profileTarget.match_score}% match
</span>
```

becomes:

```jsx
<span className={`score-badge ${scoreClass(profileTarget.match_score)}`}>
  {profileTarget.match_score}% match
</span>
```

- [ ] **Step 4: Replace inline status chips with CSS classes**

Remove the `STATUS_COLORS` constant (lines 29–33):
```jsx
const STATUS_COLORS = {
  pending: '#4F46E5',
  shortlisted: '#16a34a',
  withdrawn: '#9ca3af',
};
```

In the table (lines 161–172), replace:
```jsx
<span
  className="status-chip"
  style={{
    background: STATUS_COLORS[a.status] || '#6b7280',
    color: '#fff',
    padding: '2px 10px',
    borderRadius: '12px',
    fontSize: '0.85em',
  }}
>
  {a.status}
</span>
```

with:

```jsx
<span className={`status-chip status-${a.status}`}>
  {a.status}
</span>
```

In the profile modal (lines 245–249), replace:
```jsx
<span
  className="status-chip"
  style={{ background: STATUS_COLORS[profileTarget.status] || '#6b7280', color: '#fff' }}
>
  {profileTarget.status}
</span>
```

with:

```jsx
<span className={`status-chip status-${profileTarget.status}`}>
  {profileTarget.status}
</span>
```

- [ ] **Step 5: Verify the fix**

Run: `cd frontend && npx webpack --mode development 2>&1 | head -5`
Expected: Build succeeds.

Open as employer, go to any job's Applicants page. Verify:
- Match bars render correctly with green/amber/gray colors
- Score badges have colored backgrounds
- Status chips show correct colors without inline styles

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Applicants.jsx frontend/src/pages/Applicants.css
git commit -m "fix(applicants): replace inline styles with CSS classes

MatchBar, score badges, and status chips were all inline-styled.
Moved structural styles to CSS, replaced SCORE_COLOR/STATUS_COLORS
constants with CSS class modifiers using design system variables."
```

---

### Task 5: Fix CreateJobPost.jsx "Save as Draft" Button

**Problem:** The "Save as Draft" button uses inline styles with hardcoded colors and no hover effect.

**Files:**
- Modify: `frontend/src/CreateJobPost.jsx`
- Modify: `frontend/src/CreateJobPost.css`

- [ ] **Step 1: Add btn-secondary class to CreateJobPost.css**

Add to `CreateJobPost.css` after the `.form-actions` rule:

```css
.btn-secondary {
  background: var(--color-bg);
  color: var(--color-text);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius);
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font);
  transition: all 0.15s;
}
.btn-secondary:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-light);
}
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }
```

- [ ] **Step 2: Replace inline-styled button in CreateJobPost.jsx**

In `CreateJobPost.jsx` lines 255–258, replace:

```jsx
<button type="button" onClick={handleSaveDraft} disabled={loading}
  style={{ background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db',
           padding: '10px 20px', borderRadius: '8px', cursor: 'pointer' }}>
  {loading ? 'Saving...' : 'Save as Draft'}
</button>
```

with:

```jsx
<button type="button" onClick={handleSaveDraft} disabled={loading} className="btn-secondary">
  {loading ? 'Saving...' : 'Save as Draft'}
</button>
```

- [ ] **Step 3: Verify the fix**

Run: `cd frontend && npx webpack --mode development 2>&1 | head -5`
Expected: Build succeeds.

Open as employer, go to Post a Job. The "Save as Draft" button should have a light background and hover to indigo border/text.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/CreateJobPost.jsx frontend/src/CreateJobPost.css
git commit -m "fix(create-job): replace inline Save as Draft button with CSS class

Adds .btn-secondary with hover effect using design system variables.
Removes hardcoded #f3f4f6/#374151/#d1d5db inline styles."
```

---

### Task 6: Fix Jobs.jsx Missing max-width and Layout Grid

**Problem:** The Jobs page has no `max-width`, so content stretches to full viewport width on large screens. The `.jobs-layout` grid class is defined in CSS but never applied in JSX.

**Files:**
- Modify: `frontend/src/pages/Jobs.jsx`
- Modify: `frontend/src/pages/Jobs.css`

- [ ] **Step 1: Read Jobs.jsx to find the current page structure**

Read `frontend/src/pages/Jobs.jsx` fully to find where the sidebar and main content sections are rendered, and what wrapper divs exist. Look for the return statement of the main `Jobs` component.

- [ ] **Step 2: Add max-width to .jobs-page in Jobs.css**

In `Jobs.css` line 2–4, change:
```css
.jobs-page {
  padding: 24px 32px;
}
```
to:
```css
.jobs-page {
  padding: 24px 32px;
  max-width: 1200px;
  margin: 0 auto;
}
```

- [ ] **Step 3: Apply the jobs-layout grid wrapper in Jobs.jsx**

Find the JSX where the sidebar and main content are rendered side-by-side. Wrap them in a div with `className="jobs-layout"`. The exact location depends on the current JSX structure — look for the sidebar div (className="jobs-sidebar") and the main content div (className="jobs-main").

If the sidebar and main content currently sit as siblings inside `.jobs-page`:
```jsx
<div className="jobs-page">
  {/* tabs */}
  <div className="jobs-layout">
    <aside className="jobs-sidebar">...</aside>
    <div className="jobs-main">...</div>
  </div>
</div>
```

If there's already a wrapper but without the class, just add `className="jobs-layout"` to it.

- [ ] **Step 4: Verify the fix**

Run: `cd frontend && npx webpack --mode development 2>&1 | head -5`
Expected: Build succeeds.

Open Jobs page. Verify:
- Content is centered with max-width ~1200px
- Sidebar and job cards display in a 220px + 1fr grid layout
- On mobile (<768px), sidebar stacks above cards

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Jobs.jsx frontend/src/pages/Jobs.css
git commit -m "fix(jobs): add max-width and apply jobs-layout grid wrapper

Jobs page content now has max-width: 1200px for readability on wide
screens. Applied the existing .jobs-layout grid class to wrap sidebar
and main content in a proper 220px + 1fr layout."
```
