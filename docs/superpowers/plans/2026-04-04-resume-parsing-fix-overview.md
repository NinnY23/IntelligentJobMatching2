# Resume Parsing Fix Plan — Overview

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 7 bugs in the resume text parsing pipeline so that pasting resume content into the Profile page correctly extracts phone numbers, skills (without false positives), education, experience, and name — with proper casing and deduplication.

**Architecture:** All parsing logic lives in helper functions at the top of `app.py` (lines 24–117). The endpoint `/api/parse-resume-text` (lines 469–523) calls these helpers and writes results to the User model. The frontend `Profile.jsx` sends the text and updates the form from the response. Fixes are surgical — we fix each helper function, add experience extraction, improve the skill dictionary, and fix the deduplication logic. No new endpoints or model changes needed.

**Tech Stack:** Flask/SQLAlchemy backend, spaCy NLP, regex, React 19 frontend

---

## Root Cause Analysis

### Bug 1: `extract_phone()` Returns Capture Group, Not Full Match (Critical)

**Location:** `app.py:69-77`

**Root cause:** The first phone regex pattern `r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'` contains a capture group `(\+?\d{1,3}[-.\s]?)`. When `re.findall()` encounters a pattern with groups, it returns the **group content**, not the full match. So for `"+1-555-123-4567"`, `phones[0]` returns `"+1-"` (just the country code) instead of the full number. Pattern 2 has the same bug: `r'(\+\d{1,3})\s?\d{1,14}'` returns only `"+1"`.

**Fix:** Convert capture groups to non-capturing `(?:...)` or use `re.search().group(0)` instead of `re.findall()`.

### Bug 2: Skill Matching Uses Substring, Causes False Positives (High)

**Location:** `app.py:114`

**Root cause:** `if skill in text_lower` does substring matching. This means:
- `"go"` matches `"google"`, `"going"`, `"good"`
- `"sql"` matches `"postgresql"`, `"mysql"` (user gets "Sql" even if they only know PostgreSQL)
- `"css"` matches `"accessing"`, `"process"`
- `"git"` matches `"digital"`, `"legitimate"`
- `"r"` would match everything (not in list, but shows the fragility)
- `"express"` matches `"expression"`, `"expressed"`
- `"redis"` matches `"credits"`

**Fix:** Use word-boundary regex `r'\b' + re.escape(skill) + r'\b'` for matching, with special handling for skills containing special chars (`c++`, `c#`, `node.js`).

### Bug 3: `.title()` Gives Wrong Casing for Acronyms (High)

**Location:** `app.py:115`

**Root cause:** `skill.title()` capitalizes the first letter of each word and lowercases the rest. This produces wrong output for:

| Input | `.title()` | Correct |
|-------|-----------|---------|
| `"aws"` | `"Aws"` | `"AWS"` |
| `"html"` | `"Html"` | `"HTML"` |
| `"css"` | `"Css"` | `"CSS"` |
| `"sql"` | `"Sql"` | `"SQL"` |
| `"mysql"` | `"Mysql"` | `"MySQL"` |
| `"postgresql"` | `"Postgresql"` | `"PostgreSQL"` |
| `"mongodb"` | `"Mongodb"` | `"MongoDB"` |
| `"node.js"` | `"Node.Js"` | `"Node.js"` |
| `"gcp"` | `"Gcp"` | `"GCP"` |

**Fix:** Replace `COMMON_SKILLS` list with a `SKILL_DISPLAY_NAMES` dict that maps lowercase → correct display name.

### Bug 4: Case-Sensitive Skill Deduplication (Medium)

**Location:** `app.py:491`

**Root cause:** `list(set(existing_skills + extracted_skills))` uses Python's default set which is case-sensitive. If user manually typed `"python"` and the extractor returns `"Python"`, both appear in the set. The user sees `"python, Python"` in their skills.

**Fix:** Deduplicate using case-insensitive comparison (lowercase set for seen-tracking, keep the best-cased version).

### Bug 5: No Experience Extraction (Medium)

**Location:** `app.py:469-523`

**Root cause:** The endpoint extracts name, email, phone, education, and skills — but never extracts work experience. The `experience` field exists on the User model but is never auto-populated. Users who paste a resume expect their work history to be picked up.

**Fix:** Add `extract_experience()` function that looks for experience-related keywords (company names, job titles, date ranges, "intern", "developer", "engineer", etc.) and populate `user.experience` if empty.

### Bug 6: Education Extraction Is Fragile (Medium)

**Location:** `app.py:80-93`

**Root cause:** `extract_education()` does line-by-line keyword matching. If a line contains any education keyword (like "school" or "graduated"), the entire raw line is included — even if it's `"I graduated from high school and went to work"`. It also misses multi-line education entries where the degree and university are on separate lines. The output is joined with `'; '` which looks unnatural.

**Fix:** Improve keyword matching to prefer lines that contain both a degree keyword AND an institution keyword, and use newlines instead of semicolons for multi-entry education.

### Bug 7: COMMON_SKILLS List Is Too Small (Low)

**Location:** `app.py:25-31`

**Root cause:** Only 37 skills. Missing major ones like: `typescript`, `swift`, `kotlin`, `scala`, `r`, `matlab`, `spring`, `spring boot`, `next.js`, `graphql`, `rest`, `api`, `figma`, `jira`, `jenkins`, `ci/cd`, `terraform`, `ansible`, `elasticsearch`, `kafka`, `rabbitmq`, `spark`, `hadoop`, `tableau`, `power bi`, `excel`, `photoshop`, `illustrator`, `unity`, `unreal`, etc.

**Fix:** Expand to ~80-100 common skills using the display-name dict from Bug 3 fix.

---

## Summary of All Bugs

| # | Bug | File | Lines | Severity |
|---|-----|------|-------|----------|
| 1 | Phone extraction returns capture group, not full match | `app.py` | 69-77 | Critical |
| 2 | Skill matching uses substring — false positives | `app.py` | 114 | High |
| 3 | `.title()` gives wrong casing for acronyms | `app.py` | 115 | High |
| 4 | Case-sensitive skill deduplication | `app.py` | 491 | Medium |
| 5 | No experience extraction | `app.py` | 469-523 | Medium |
| 6 | Education extraction is fragile | `app.py` | 80-93 | Medium |
| 7 | COMMON_SKILLS too small (37 entries) | `app.py` | 25-31 | Low |

## Plan Files

1. **This file** — Overview and root cause analysis
2. **`2026-04-04-resume-parsing-fix-tasks.md`** — All implementation tasks
