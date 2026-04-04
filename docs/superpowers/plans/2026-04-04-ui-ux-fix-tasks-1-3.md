# UI/UX Fix — Tasks 1–3

> See `2026-04-04-ui-ux-consistency-fix-overview.md` for context and design system reference.

---

### Task 1: Fix Applications.jsx CSS Class Mismatches

**Problem:** The JSX uses class names that don't match what the CSS file defines. The entire Applications page is unstyled — no table borders, no shadows, no tab highlighting, broken skeleton/empty/dialog states.

**Files:**
- Modify: `frontend/src/pages/Applications.jsx`
- Modify: `frontend/src/pages/Applications.css`

**Class name mapping (JSX → CSS):**

| JSX uses | CSS defines | Action |
|----------|------------|--------|
| `apps-page` | `.applications-page` | Fix JSX |
| `apps-title` | (missing) | Use existing `.apps-header h2` |
| `apps-subtitle` | (missing) | Use `.apps-count` |
| `apps-table-wrap` | (missing) | Add to CSS |
| `apps-table` | `.applications-table` | Fix JSX |
| `apps-tab--active` (BEM) | `.apps-tab.active` (compound) | Fix JSX |
| `apps-row` | (missing) | Not needed, remove |
| `apps-td-position`, `apps-td-company`, etc. | (missing) | Not needed, remove |
| `apps-dialog-backdrop` | `.apps-dialog-overlay` | Fix JSX |
| `apps-dialog-title` | (missing) | Use `.apps-dialog h3` |
| `apps-dialog-message` | (missing) | Use `.apps-dialog p` |
| `apps-dialog-cancel` | (missing) | Use `.btn-outline` |
| `apps-dialog-confirm` | (missing) | Use `.btn-danger` |
| `apps-dialog-icon` | (missing) | Add to CSS |
| `apps-error` | (missing) | Add to CSS |
| `apps-error-retry` | (missing) | Add to CSS |
| `apps-error-close` | (missing) | Add to CSS |
| `apps-empty`, `apps-empty-icon`, `apps-empty-title`, `apps-empty-sub`, `apps-empty-link` | (missing) | Add to CSS |
| `apps-type-chip` | (missing) | Add to CSS |
| `apps-withdraw-btn`, `apps-withdraw-btn--disabled` | (missing) | Add to CSS |
| `apps-location` | (missing) | Add to CSS |
| `apps-skel-row`, `apps-skel`, `apps-skel-title`, `apps-skel-sub`, `apps-skel-chip-sm`, `apps-skel-date`, `apps-skel-btn` | (missing) | Add to CSS |

- [ ] **Step 1: Fix the page container class in Applications.jsx**

In `Applications.jsx` line 156, change:
```jsx
<div className="apps-page">
```
to:
```jsx
<div className="applications-page">
```

- [ ] **Step 2: Fix the page header classes**

In `Applications.jsx` lines 159–166, the header uses `apps-title` and `apps-subtitle` which don't exist. Replace:
```jsx
<div className="apps-header">
  <div>
    <h1 className="apps-title">My Applications</h1>
    {!loading && (
      <p className="apps-subtitle">
```
with:
```jsx
<div className="apps-header">
  <div>
    <h2>My Applications</h2>
    {!loading && (
      <p className="apps-count">
```

- [ ] **Step 3: Fix the tab active class from BEM to compound**

In `Applications.jsx` line 202, change:
```jsx
className={`apps-tab${activeTab === tab ? ' apps-tab--active' : ''}`}
```
to:
```jsx
className={`apps-tab${activeTab === tab ? ' active' : ''}`}
```

- [ ] **Step 4: Fix the table class name**

In `Applications.jsx` lines 216 and 262, change both occurrences of:
```jsx
<table className="apps-table">
```
to:
```jsx
<table className="applications-table">
```

- [ ] **Step 5: Remove unnecessary per-cell class names from table rows**

In `Applications.jsx` lines 279–319, remove the non-existent cell classes. Replace:
```jsx
<tr key={app.id} className="apps-row">
  <td className="apps-td-position">
    <span className="apps-position-name">{job.position || '—'}</span>
  </td>
  <td className="apps-td-company">{job.company || '—'}</td>
  <td className="apps-td-location">
```
with:
```jsx
<tr key={app.id}>
  <td>
    <strong>{job.position || '—'}</strong>
  </td>
  <td>{job.company || '—'}</td>
  <td>
```

Do the same for all `apps-td-*` classes: remove `apps-td-type`, `apps-td-date`, `apps-td-status`, `apps-td-action`.

- [ ] **Step 6: Fix the confirm dialog classes**

In `Applications.jsx` lines 48–69 (ConfirmDialog component), replace:
```jsx
<div className="apps-dialog-backdrop" role="dialog" aria-modal="true" aria-labelledby="apps-dialog-title">
  <div className="apps-dialog">
    <div className="apps-dialog-icon">
```
with:
```jsx
<div className="apps-dialog-overlay" role="dialog" aria-modal="true" aria-labelledby="apps-dialog-title">
  <div className="apps-dialog">
    <div className="apps-dialog-icon">
```

Replace the dialog buttons (lines 60–65):
```jsx
<button className="apps-dialog-cancel" onClick={onCancel} disabled={loading}>
  Cancel
</button>
<button className="apps-dialog-confirm" onClick={onConfirm} disabled={loading}>
  {loading ? 'Withdrawing…' : 'Yes, Withdraw'}
</button>
```
with:
```jsx
<button className="btn-outline" onClick={onCancel} disabled={loading}>
  Cancel
</button>
<button className="btn-danger" onClick={onConfirm} disabled={loading}>
  {loading ? 'Withdrawing…' : 'Yes, Withdraw'}
</button>
```

- [ ] **Step 7: Add missing CSS classes to Applications.css**

Append the following to `Applications.css` (before the `@media` queries):

```css
/* Table wrapper */
.apps-table-wrap { overflow-x: auto; }

/* Dialog icon */
.apps-dialog-icon { margin-bottom: 16px; }

/* Error banners */
.apps-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: var(--radius);
  font-size: 14px;
  margin-bottom: 16px;
  background: var(--color-danger-light);
  color: var(--color-danger);
  border: 1px solid #fecaca;
}
.apps-error--warn {
  background: #fef3c7;
  color: #92400e;
  border-color: #fde68a;
}
.apps-error-retry {
  background: none;
  border: 1px solid currentColor;
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  color: inherit;
  font-family: var(--font);
  margin-left: auto;
  white-space: nowrap;
}
.apps-error-close {
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  font-size: 18px;
  line-height: 1;
  padding: 0;
  margin-left: auto;
  opacity: 0.7;
}
.apps-error-close:hover { opacity: 1; }

/* Empty state */
.apps-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}
.apps-empty-icon { margin-bottom: 16px; opacity: 0.5; }
.apps-empty-title { font-size: 18px; font-weight: 700; color: var(--color-text); margin: 0 0 8px 0; }
.apps-empty-sub { font-size: 14px; color: var(--color-muted); margin: 0; }
.apps-empty-link { color: var(--color-primary); text-decoration: none; font-weight: 600; }
.apps-empty-link:hover { text-decoration: underline; }

/* Job type chip */
.apps-type-chip {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 12px;
}

/* Location with icon */
.apps-location {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* Withdraw button */
.apps-withdraw-btn {
  background: none;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  padding: 5px 14px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-muted);
  cursor: pointer;
  font-family: var(--font);
  transition: all 0.15s;
}
.apps-withdraw-btn:hover:not(:disabled) {
  border-color: var(--color-danger);
  color: var(--color-danger);
  background: var(--color-danger-light);
}
.apps-withdraw-btn--disabled,
.apps-withdraw-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Skeleton rows */
.apps-skel-row td { padding: 14px 16px; }
.apps-skel {
  background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
  background-size: 200% 100%;
  animation: apps-shimmer 1.4s infinite;
  border-radius: 6px;
  height: 14px;
}
.apps-skel-title { width: 60%; }
.apps-skel-sub { width: 45%; }
.apps-skel-chip-sm { width: 50px; height: 20px; border-radius: 12px; }
.apps-skel-date { width: 70px; }
.apps-skel-btn { width: 60px; height: 24px; border-radius: 6px; }

@keyframes apps-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

- [ ] **Step 8: Verify the fix**

Run: `cd frontend && npx webpack --mode development 2>&1 | head -5`
Expected: Build succeeds with no errors.

Open the app, navigate to My Applications. Verify:
- Table has white background, rounded corners, border, shadow, hover effect on rows
- Status tabs highlight with indigo when active
- Withdraw button has a hover effect (red border + text)
- Empty state shows icon + centered text
- Skeleton loading shows animated shimmer rows

- [ ] **Step 9: Commit**

```bash
git add frontend/src/pages/Applications.jsx frontend/src/pages/Applications.css
git commit -m "fix(applications): align JSX class names with CSS definitions

The Applications page was completely unstyled because JSX used class
names (apps-page, apps-table, apps-tab--active, apps-dialog-backdrop)
that didn't match the CSS file definitions (applications-page,
applications-table, apps-tab.active, apps-dialog-overlay). Fixed all
mismatches and added missing CSS for error banners, empty states,
withdraw buttons, skeleton rows, and type chips."
```

---

### Task 2: Replace MyJobs.jsx Inline Styles with CSS Classes

**Problem:** The filter tabs in MyJobs.jsx are 100% inline-styled with wrong blue (#2563eb instead of --color-primary #4F46E5). Status badges also use inline styles.

**Files:**
- Modify: `frontend/src/pages/MyJobs.jsx`
- Modify: `frontend/src/pages/MyJobs.css`

- [ ] **Step 1: Add filter tab CSS classes to MyJobs.css**

Add to `MyJobs.css` after the `.page-header` block (before `.jobs-table`):

```css
/* Filter tabs — reuse same pattern as Applicants.css */
.myjobs-tabs { display: flex; gap: 6px; margin-bottom: 20px; }
.myjobs-tab {
  background: #fff;
  border: 1.5px solid var(--color-border);
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: var(--color-muted);
  font-family: var(--font);
  transition: all 0.15s;
  text-transform: capitalize;
}
.myjobs-tab.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.myjobs-tab:hover:not(.active) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* Status badges */
.myjobs-status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.myjobs-status--active { background: #dcfce7; color: #065f46; }
.myjobs-status--draft { background: #fef3c7; color: #92400e; }
.myjobs-status--archived { background: #f3f4f6; color: var(--color-muted); }
```

- [ ] **Step 2: Replace inline filter tabs in MyJobs.jsx**

In `MyJobs.jsx` lines 107–122, replace the entire inline-styled filter block:

```jsx
<div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
  {['all', 'active', 'draft', 'archived'].map(tab => (
    <button
      key={tab}
      onClick={() => setFilter(tab)}
      style={{
        padding: '6px 16px', borderRadius: '20px', border: '1px solid #d1d5db',
        background: filter === tab ? '#2563eb' : '#fff',
        color: filter === tab ? '#fff' : '#374151',
        cursor: 'pointer', fontWeight: 500, textTransform: 'capitalize'
      }}
    >
      {tab === 'all' ? 'All' : tab.charAt(0).toUpperCase() + tab.slice(1) + 's'}
    </button>
  ))}
</div>
```

with:

```jsx
<div className="myjobs-tabs">
  {['all', 'active', 'draft', 'archived'].map(tab => (
    <button
      key={tab}
      className={`myjobs-tab${filter === tab ? ' active' : ''}`}
      onClick={() => setFilter(tab)}
    >
      {tab === 'all' ? 'All' : tab.charAt(0).toUpperCase() + tab.slice(1) + 's'}
    </button>
  ))}
</div>
```

- [ ] **Step 3: Replace inline status badges in MyJobs.jsx**

Remove the `statusBadgeStyle` function (lines 82–88). Replace its usage on line 152:

```jsx
<td><span style={statusBadgeStyle(job.status)}>{job.status}</span></td>
```

with:

```jsx
<td><span className={`myjobs-status myjobs-status--${job.status}`}>{job.status}</span></td>
```

- [ ] **Step 4: Verify the fix**

Run: `cd frontend && npx webpack --mode development 2>&1 | head -5`
Expected: Build succeeds.

Open the app as an employer, navigate to My Jobs. Verify:
- Filter tabs are pill-shaped with indigo (#4F46E5) active state
- Status badges show green/amber/gray per status
- Hover effects work on tabs

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/MyJobs.jsx frontend/src/pages/MyJobs.css
git commit -m "fix(my-jobs): replace inline styles with CSS classes

Filter tabs were using inline styles with wrong blue (#2563eb). Status
badges were also inline-styled. Replaced both with CSS classes using
the design system's --color-primary and consistent pill/badge patterns."
```

---

### Task 3: Fix Dashboard.jsx Status Chips

**Problem:** Dashboard uses inline styles for status chips instead of the global `.status-chip` classes from index.css.

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`

- [ ] **Step 1: Remove STATUS_CHIP_COLORS constant and inline styles**

In `Dashboard.jsx`, delete lines 6–10:
```jsx
const STATUS_CHIP_COLORS = {
  pending: '#4F46E5',
  shortlisted: '#16a34a',
  withdrawn: '#9ca3af',
};
```

- [ ] **Step 2: Replace inline-styled status chip with CSS class**

In `Dashboard.jsx` lines 81–92, replace:
```jsx
<span
  className={`status-chip status-${a.status}`}
  style={{
    background: STATUS_CHIP_COLORS[a.status] || '#6b7280',
    color: '#fff',
    padding: '2px 10px',
    borderRadius: '12px',
    fontSize: '0.82em',
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

The global `.status-chip` class in `index.css` already provides `padding: 2px 10px`, `border-radius: 12px`, `font-size: 12px`, `font-weight: 600`, `color: #fff`. The modifier classes `.status-chip.status-pending`, `.status-chip.status-shortlisted`, `.status-chip.status-withdrawn` set the correct background colors.

- [ ] **Step 3: Verify the fix**

Run: `cd frontend && npx webpack --mode development 2>&1 | head -5`
Expected: Build succeeds.

Open dashboard. Status chips should show indigo (pending), green (shortlisted), gray (withdrawn) — same colors as before but now from CSS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Dashboard.jsx
git commit -m "fix(dashboard): use global status-chip CSS classes instead of inline styles

Removes STATUS_CHIP_COLORS constant and inline style object. The global
.status-chip classes in index.css already define the correct styles."
```
