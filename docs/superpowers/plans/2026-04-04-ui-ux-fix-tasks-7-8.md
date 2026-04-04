# UI/UX Fix — Tasks 7–8

> See `2026-04-04-ui-ux-consistency-fix-overview.md` for context and design system reference.

---

### Task 7: Fix Navbar Mobile — Logout Button Hidden

**Problem:** On screens <=768px, `.navbar-user { display: none }` hides the entire user section including the Logout button. Users on mobile have no way to log out.

**Files:**
- Modify: `frontend/src/components/Navbar.jsx`
- Modify: `frontend/src/components/Navbar.css`

- [ ] **Step 1: Add a Logout link to the mobile hamburger menu in Navbar.jsx**

In `Navbar.jsx`, inside the `.navbar-links` div (the hamburger dropdown), add a Logout button that only shows on mobile. After the map of nav links (line 60, after the closing `</button>` of the last link and before the closing `</div>` of `.navbar-links`):

```jsx
{links.map(link => (
  <button
    key={link.path}
    className={`nav-link${isActive(link.path) ? ' active' : ''}`}
    onClick={() => { navigate(link.path); setMenuOpen(false); }}
    aria-current={isActive(link.path) ? 'page' : undefined}
  >
    {link.label}
    {link.badge > 0 && (
      <span className="nav-badge" aria-label={`${link.badge} unread`}>
        {link.badge}
      </span>
    )}
  </button>
))}
<button
  className="nav-link nav-logout-mobile"
  onClick={() => { setMenuOpen(false); onLogout(); }}
>
  Logout
</button>
```

Note: Also add `setMenuOpen(false)` to each nav link onClick so the menu closes after navigation.

- [ ] **Step 2: Add CSS for mobile-only logout button**

Add to `Navbar.css`:

```css
/* Mobile-only logout in hamburger menu */
.nav-logout-mobile {
  display: none;
}

@media (max-width: 768px) {
  .nav-logout-mobile {
    display: block;
    color: var(--color-danger);
    font-weight: 600;
    margin-top: 8px;
    padding-top: 12px;
    border-top: 1px solid var(--color-border);
  }
  .nav-logout-mobile:hover {
    background: var(--color-danger-light);
  }
}
```

This makes the logout button invisible on desktop (where `.navbar-user` is visible) and visible in the hamburger menu on mobile.

- [ ] **Step 3: Verify the fix**

Open the app and resize browser to <768px width. Click the hamburger menu. Verify:
- All nav links are listed
- A "Logout" option appears at the bottom with a separator line
- Clicking Logout logs the user out
- On desktop (>768px), the mobile logout is hidden and the existing `.navbar-user` Logout button is visible

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Navbar.jsx frontend/src/components/Navbar.css
git commit -m "fix(navbar): add logout button to mobile hamburger menu

On mobile (<768px) the .navbar-user section was hidden, leaving no
way to log out. Added a mobile-only Logout option at the bottom of
the hamburger dropdown menu."
```

---

### Task 8: Replace Hardcoded Colors with CSS Variables

**Problem:** Several files use hardcoded hex colors instead of CSS variables. This task is a sweep across all files modified by Tasks 1–7, plus any remaining instances.

**Files:**
- Modify: `frontend/src/pages/Jobs.jsx` (MatchBadge uses #7C3AED, #9CA3AF)
- Modify: `frontend/src/pages/Jobs.css` (description color #374151, skills-section h4 #6b7280)
- Modify: `frontend/src/components/Navbar.css` (nav-badge background #ef4444)

- [ ] **Step 1: Fix MatchBadge hardcoded colors in Jobs.jsx**

In `Jobs.jsx` lines 50–62, the MatchBadge component uses:
```jsx
let bg = '#4F46E5';
if (pct >= 80) bg = '#4F46E5';
else if (pct >= 50) bg = '#7C3AED';
else bg = '#9CA3AF';
```

Replace with CSS variable references:
```jsx
let bg = 'var(--color-primary)';
if (pct >= 80) bg = 'var(--color-primary)';
else if (pct >= 50) bg = '#7c3aed';
else bg = 'var(--color-muted)';
```

Note: `#7c3aed` (purple) is intentionally kept as a gradient accent — it's not in the design system variables but is used in the apply button gradient. This is acceptable as a deliberate accent color for "medium match" differentiation.

- [ ] **Step 2: Fix hardcoded colors in Jobs.css**

In `Jobs.css` line 557, change:
```css
.jobs-modal-description {
  font-size: 14px;
  color: #374151;
```
to:
```css
.jobs-modal-description {
  font-size: 14px;
  color: var(--color-text);
```

In `Jobs.css` lines 891–893, change:
```css
.jobs-skills-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
```
to:
```css
.jobs-skills-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
```

- [ ] **Step 3: Fix nav-badge hardcoded red in Navbar.css**

In `Navbar.css` line 52, change:
```css
.nav-badge {
  ...
  background: #ef4444;
```
to:
```css
.nav-badge {
  ...
  background: var(--color-danger);
```

Note: `--color-danger` is `#dc2626` which is slightly darker red. Both are valid reds — this brings it into the design system.

- [ ] **Step 4: Verify the fix**

Run: `cd frontend && npx webpack --mode development 2>&1 | head -5`
Expected: Build succeeds.

Visually check Jobs page — match badges should still show purple/indigo/gray. Modal description text should still be dark. Navbar unread badge should still be red.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Jobs.jsx frontend/src/pages/Jobs.css frontend/src/components/Navbar.css
git commit -m "fix: replace hardcoded hex colors with CSS variables

Replaces #374151 with --color-text, #6b7280 with --color-muted,
#ef4444 with --color-danger, and #9CA3AF with --color-muted across
Jobs.jsx, Jobs.css, and Navbar.css for design system consistency."
```
