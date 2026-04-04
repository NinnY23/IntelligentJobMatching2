# UI/UX Consistency Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all broken styling, eliminate inline styles, standardize on the CSS design system, and make every page look polished and consistent.

**Architecture:** The app already has a solid design system in `index.css` (CSS variables, global button/chip/modal classes). The problems are: (1) JSX class names that don't match CSS definitions, (2) inline styles bypassing the design system, (3) hardcoded colors instead of CSS variables, (4) mobile navbar hiding the logout button. Every fix reuses existing CSS patterns rather than inventing new ones.

**Tech Stack:** React 19, CSS (no preprocessor), CSS custom properties (variables)

---

## Issue Summary

| # | Page / Component | Problem | Severity |
|---|-----------------|---------|----------|
| 1 | Applications.jsx | CSS class names in JSX don't match CSS file — entire page unstyled | Critical |
| 2 | MyJobs.jsx | Filter tabs are 100% inline-styled with wrong color (#2563eb) | High |
| 3 | Dashboard.jsx | Status chips use inline styles bypassing global `.status-chip` | Medium |
| 4 | Applicants.jsx | MatchBar + status chips are inline-styled; duplicate MatchBar component | Medium |
| 5 | CreateJobPost.jsx | "Save as Draft" button is inline-styled with no hover | Medium |
| 6 | Jobs.jsx | Missing `max-width` and `.jobs-layout` grid wrapper not applied | Medium |
| 7 | Navbar | Logout button hidden on mobile (`.navbar-user { display: none }`) | High |
| 8 | Cross-cutting | Hardcoded hex colors (#2563eb, #374151, #7C3AED, etc.) instead of CSS vars | Low |

## Plan Files

The implementation is split across 4 plan files (this overview + 3 task files):

1. **`2026-04-04-ui-ux-consistency-fix-overview.md`** — This file (overview + summary)
2. **`2026-04-04-ui-ux-fix-tasks-1-3.md`** — Tasks 1–3 (Applications, MyJobs, Dashboard)
3. **`2026-04-04-ui-ux-fix-tasks-4-6.md`** — Tasks 4–6 (Applicants, CreateJobPost, Jobs)
4. **`2026-04-04-ui-ux-fix-tasks-7-8.md`** — Tasks 7–8 (Navbar mobile, hardcoded colors)

## Execution Order

Tasks 1–6 are independent and can be executed in any order.
Task 7 (Navbar) is independent.
Task 8 (hardcoded colors) should run last as it touches files modified by earlier tasks.

## Design System Reference

All fixes must use these CSS variables from `frontend/src/index.css`:

```css
--color-primary: #4F46E5;
--color-primary-dark: #4338ca;
--color-primary-light: #e0e7ff;
--color-success: #16a34a;
--color-danger: #dc2626;
--color-danger-light: #fee2e2;
--color-text: #1e1b4b;
--color-muted: #6b7280;
--color-border: #e5e7eb;
--color-bg: #f8faff;
--font: 'Plus Jakarta Sans', sans-serif;
--radius: 10px;
--shadow: 0 1px 4px rgba(79,70,229,0.08);
--shadow-md: 0 4px 12px rgba(79,70,229,0.12);
```

Global classes available in `index.css`: `.btn-primary`, `.btn-outline`, `.btn-danger`, `.btn-sm`, `.btn-danger-sm`, `.skill-tag`, `.score-badge`, `.status-chip`, `.modal-overlay`, `.modal`, `.modal-close`, `.loading`, `.empty-state`, `.error-banner`, `.info-banner`, `.muted`, `.skill-tags`.
