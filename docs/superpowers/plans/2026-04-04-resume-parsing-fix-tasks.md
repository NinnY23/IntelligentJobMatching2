# Resume Parsing Fix — Implementation Tasks

> See `2026-04-04-resume-parsing-fix-overview.md` for root cause analysis and context.

---

### Task 1: Fix `extract_phone()` — Returns Capture Group Instead of Full Match

**Problem:** `re.findall()` with capture groups returns the group content, not the full match. For `"+1-555-123-4567"`, it returns `"+1-"` instead of the full number.

**Files:**
- Modify: `app.py:66-78`
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Write failing test for phone extraction**

Add to `tests/test_profile.py`:

```python
def test_resume_parse_extracts_full_phone_number(client, seeker_token):
    """Phone number should be extracted in full, not just the country code."""
    res = client.post('/api/parse-resume-text', json={
        'resumeText': 'Jane Doe\njane@example.com\n+1-555-123-4567\nSkills: Python'
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    data = res.get_json()
    phone = data['resume_data']['phone']
    assert phone is not None
    assert len(phone) >= 10, f"Phone too short, got capture group? '{phone}'"
    assert '555' in phone and '4567' in phone
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_extracts_full_phone_number -v`

Expected: FAIL — `phone` will be `"+1-"` or similar short string.

- [ ] **Step 3: Fix `extract_phone()` in `app.py`**

Replace `app.py` lines 66-78:

```python
def extract_phone(text):
    """Extract phone number from text using regex."""
    phone_patterns = [
        r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+\d{1,3}\s?\d{1,14}',
        r'\b\d{10}\b'
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None
```

Key changes:
- Converted capture groups `(...)` to non-capturing `(?:...)`
- Changed from `re.findall()` → `re.search().group(0)` to always get the full match
- Returns the matched string directly, never a tuple

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_extracts_full_phone_number -v`

Expected: PASS

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py -v`

Expected: All profile tests pass.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_profile.py
git commit -m "fix: extract_phone returns full match instead of capture group

re.findall with capture groups returns group content, not the full
match. Changed to re.search().group(0) with non-capturing groups
so '+1-555-123-4567' returns the full number, not just '+1-'."
```

---

### Task 2: Replace COMMON_SKILLS List with SKILL_DISPLAY_NAMES Dict (Fixes Bugs 3 + 7)

**Problem:** `.title()` produces wrong casing (`"Aws"`, `"Html"`, `"Mysql"`), and the skills list is too small (37 entries). Both are fixed by replacing the list with a dict that maps lowercase → correct display name.

**Files:**
- Modify: `app.py:24-31` (replace `COMMON_SKILLS`)
- Modify: `app.py:109-116` (update `extract_skills_from_text`)
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Write failing test for skill casing**

Add to `tests/test_profile.py`:

```python
def test_resume_parse_skills_correct_casing(client, seeker_token):
    """Extracted skills should have correct display names, not .title() casing."""
    res = client.post('/api/parse-resume-text', json={
        'resumeText': 'Skills: python, aws, html, css, sql, mysql, node.js, gcp, mongodb, postgresql'
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    skills = res.get_json()['extracted_skills']
    skills_set = set(skills)
    assert 'Python' in skills_set
    assert 'AWS' in skills_set, f"Expected 'AWS', got {[s for s in skills if 'ws' in s.lower()]}"
    assert 'HTML' in skills_set, f"Expected 'HTML', got {[s for s in skills if 'htm' in s.lower()]}"
    assert 'CSS' in skills_set
    assert 'SQL' in skills_set
    assert 'MySQL' in skills_set
    assert 'Node.js' in skills_set
    assert 'GCP' in skills_set
    assert 'MongoDB' in skills_set
    assert 'PostgreSQL' in skills_set
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_skills_correct_casing -v`

Expected: FAIL — `"Aws"` instead of `"AWS"`, etc.

- [ ] **Step 3: Replace `COMMON_SKILLS` with `SKILL_DISPLAY_NAMES` in `app.py`**

Replace `app.py` lines 24-31 (the `COMMON_SKILLS` list) with:

```python
# Skill lookup: lowercase key → correct display name
# Used by extract_skills_from_text() for matching and casing
SKILL_DISPLAY_NAMES = {
    # Programming languages
    'python': 'Python', 'javascript': 'JavaScript', 'typescript': 'TypeScript',
    'java': 'Java', 'c++': 'C++', 'c#': 'C#', 'php': 'PHP', 'ruby': 'Ruby',
    'go': 'Go', 'rust': 'Rust', 'swift': 'Swift', 'kotlin': 'Kotlin',
    'scala': 'Scala', 'r': 'R', 'matlab': 'MATLAB', 'perl': 'Perl',
    # Web frontend
    'html': 'HTML', 'css': 'CSS', 'react': 'React', 'angular': 'Angular',
    'vue': 'Vue', 'next.js': 'Next.js', 'tailwind': 'Tailwind',
    'bootstrap': 'Bootstrap', 'sass': 'Sass', 'webpack': 'Webpack',
    # Web backend
    'node.js': 'Node.js', 'express': 'Express', 'flask': 'Flask',
    'django': 'Django', 'spring': 'Spring', 'spring boot': 'Spring Boot',
    'fastapi': 'FastAPI', 'laravel': 'Laravel', 'rails': 'Rails',
    # Databases
    'sql': 'SQL', 'mysql': 'MySQL', 'postgresql': 'PostgreSQL',
    'mongodb': 'MongoDB', 'redis': 'Redis', 'sqlite': 'SQLite',
    'elasticsearch': 'Elasticsearch', 'dynamodb': 'DynamoDB',
    # Cloud & DevOps
    'aws': 'AWS', 'azure': 'Azure', 'gcp': 'GCP', 'docker': 'Docker',
    'kubernetes': 'Kubernetes', 'terraform': 'Terraform', 'ansible': 'Ansible',
    'jenkins': 'Jenkins', 'ci/cd': 'CI/CD', 'nginx': 'Nginx',
    # Data & ML
    'machine learning': 'Machine Learning', 'deep learning': 'Deep Learning',
    'data analysis': 'Data Analysis', 'data science': 'Data Science',
    'pandas': 'Pandas', 'numpy': 'NumPy', 'tensorflow': 'TensorFlow',
    'pytorch': 'PyTorch', 'scikit-learn': 'Scikit-learn', 'spark': 'Spark',
    'hadoop': 'Hadoop', 'tableau': 'Tableau', 'power bi': 'Power BI',
    # Tools & practices
    'linux': 'Linux', 'git': 'Git', 'agile': 'Agile', 'scrum': 'Scrum',
    'jira': 'Jira', 'figma': 'Figma', 'rest api': 'REST API',
    'graphql': 'GraphQL', 'microservices': 'Microservices',
    # Mobile
    'react native': 'React Native', 'flutter': 'Flutter',
    'android': 'Android', 'ios': 'iOS',
    # Messaging & streaming
    'kafka': 'Kafka', 'rabbitmq': 'RabbitMQ',
}
```

- [ ] **Step 4: Update `extract_skills_from_text()` to use the dict**

Replace `app.py` lines 109-116:

```python
def extract_skills_from_text(text):
    """Extract skills from resume text by matching against known skills dictionary."""
    text_lower = text.lower()
    found_skills = []
    seen_lower = set()
    for skill_key, display_name in SKILL_DISPLAY_NAMES.items():
        if skill_key in text_lower and skill_key not in seen_lower:
            found_skills.append(display_name)
            seen_lower.add(skill_key)
    return found_skills
```

Note: This still uses substring matching — Bug 2 (word boundary) is fixed in Task 3. This task only fixes the casing and expands the dictionary.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_skills_correct_casing -v`

Expected: PASS

- [ ] **Step 6: Run full test suite**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v`

Expected: All 88 tests pass. Some existing tests reference extracted skills — they should still work because the dict contains all the old skills.

- [ ] **Step 7: Commit**

```bash
git add app.py tests/test_profile.py
git commit -m "fix: replace COMMON_SKILLS list with SKILL_DISPLAY_NAMES dict

Fixes wrong casing from .title() (e.g., 'Aws' → 'AWS', 'Html' → 'HTML',
'Node.Js' → 'Node.js'). Expands from 37 to ~80 recognized skills including
TypeScript, Kotlin, FastAPI, Next.js, Terraform, etc."
```

---

### Task 3: Fix Skill Matching to Use Word Boundaries Instead of Substring (Bug 2)

**Problem:** `if skill in text_lower` causes false positives: `"go"` matches `"google"`, `"sql"` matches `"postgresql"`, `"css"` matches `"accessing"`, `"git"` matches `"digital"`.

**Files:**
- Modify: `app.py:109-116` (update `extract_skills_from_text`)
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Write failing test for false positive skills**

Add to `tests/test_profile.py`:

```python
def test_resume_parse_no_false_positive_skills(client, seeker_token):
    """Skill matching must not produce false positives from substrings."""
    res = client.post('/api/parse-resume-text', json={
        'resumeText': '''Software Engineer
Experienced in building digital platforms using Google Cloud.
Accessing databases and processing data efficiently.
Good communication and problem-solving skills.
Worked at Goldman Sachs on credit risk systems.'''
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    skills = res.get_json()['extracted_skills']
    skills_lower = [s.lower() for s in skills]
    # "go" should NOT match "google", "good", "goldman"
    assert 'go' not in skills_lower, f"False positive: 'Go' matched from 'Google/Good/Goldman'"
    # "css" should NOT match "accessing"
    assert 'css' not in skills_lower, f"False positive: 'CSS' matched from 'accessing'"
    # "git" should NOT match "digital"
    assert 'git' not in skills_lower, f"False positive: 'Git' matched from 'digital'"
    # "r" should NOT match random words
    assert 'r' not in skills_lower, f"False positive: 'R' matched from common text"
    # "sql" should NOT match "postgresql" substring
    assert 'sql' not in skills_lower, f"False positive: 'SQL' matched from 'Goldman Sachs'"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_no_false_positive_skills -v`

Expected: FAIL — `"Go"` and `"CSS"` and `"Git"` will be in the extracted skills.

- [ ] **Step 3: Implement word-boundary skill matching**

Replace `extract_skills_from_text()` in `app.py` with:

```python
# Pre-compile skill patterns for performance (module level, after SKILL_DISPLAY_NAMES)
_SKILL_PATTERNS = {}
for _key in SKILL_DISPLAY_NAMES:
    # Skills with special regex chars need escaping
    escaped = re.escape(_key)
    # For short skills (<=2 chars like "r", "go", "c#"), require stricter context:
    # must be surrounded by whitespace, commas, or start/end of string
    if len(_key) <= 2:
        _SKILL_PATTERNS[_key] = re.compile(
            r'(?:^|[\s,;:(])' + escaped + r'(?:$|[\s,;:)])',
            re.IGNORECASE
        )
    else:
        _SKILL_PATTERNS[_key] = re.compile(
            r'(?<![a-zA-Z])' + escaped + r'(?![a-zA-Z])',
            re.IGNORECASE
        )


def extract_skills_from_text(text):
    """Extract skills from resume text using word-boundary matching."""
    found_skills = []
    seen_lower = set()
    for skill_key, display_name in SKILL_DISPLAY_NAMES.items():
        if skill_key not in seen_lower and _SKILL_PATTERNS[skill_key].search(text):
            found_skills.append(display_name)
            seen_lower.add(skill_key)
    return found_skills
```

Key design decisions:
- Short skills (1-2 chars like `"r"`, `"go"`) require whitespace/punctuation boundaries — this prevents `"go"` matching in `"google"` but allows `"Go,"` or `"Go "` or `"skills: go"`
- Longer skills use `(?<![a-zA-Z])` and `(?![a-zA-Z])` lookbehind/lookahead — this prevents `"css"` matching in `"accessing"` but allows `"CSS"` or `"css,"` or `"node.js"`
- `re.escape()` handles special chars in `"c++"`, `"c#"`, `"node.js"`
- Patterns are pre-compiled at module load for performance

- [ ] **Step 4: Run false-positive test to verify it passes**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_no_false_positive_skills -v`

Expected: PASS

- [ ] **Step 5: Write test for true positives to ensure we didn't over-restrict**

Add to `tests/test_profile.py`:

```python
def test_resume_parse_true_positive_skills(client, seeker_token):
    """Skills mentioned properly in resume text should be detected."""
    res = client.post('/api/parse-resume-text', json={
        'resumeText': '''Skills: Python, JavaScript, React, Node.js, SQL, CSS, Git, Docker, AWS, Go
Experience: 3 years with Flask, Django, and PostgreSQL.
Familiar with machine learning, TensorFlow, and data analysis.'''
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    skills = res.get_json()['extracted_skills']
    skills_lower = [s.lower() for s in skills]
    for expected in ['python', 'javascript', 'react', 'node.js', 'docker', 'aws',
                     'flask', 'django', 'postgresql', 'machine learning', 'tensorflow']:
        assert expected in skills_lower, f"Missed true positive: '{expected}'"
```

- [ ] **Step 6: Run true-positive test**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_true_positive_skills -v`

Expected: PASS

- [ ] **Step 7: Run full test suite**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v`

Expected: All tests pass.

- [ ] **Step 8: Commit**

```bash
git add app.py tests/test_profile.py
git commit -m "fix: use word-boundary matching for skill extraction

Substring matching caused false positives: 'go' matched 'google',
'css' matched 'accessing', 'git' matched 'digital'. Now uses
pre-compiled regex with word boundaries. Short skills (1-2 chars)
require whitespace/punctuation context for stricter matching."
```

---

### Task 4: Fix Case-Sensitive Skill Deduplication (Bug 4)

**Problem:** `set(existing_skills + extracted_skills)` is case-sensitive. If user has `"python"` and extractor returns `"Python"`, both appear. User sees `"python, Python"`.

**Files:**
- Modify: `app.py:489-492`
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Write failing test for duplicate skills**

Add to `tests/test_profile.py`:

```python
def test_resume_parse_deduplicates_skills_case_insensitive(client, seeker_token):
    """Skills should not duplicate when existing and extracted differ only in case."""
    # First, set the user's skills to lowercase manually
    client.put('/api/profile', json={
        'skills': 'python, javascript, react'
    }, headers={'Authorization': f'Bearer {seeker_token}'})

    # Now parse resume that mentions the same skills
    res = client.post('/api/parse-resume-text', json={
        'resumeText': 'Skills: Python, JavaScript, React, Docker, AWS'
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200

    # Check profile for duplicates
    profile_res = client.get('/api/profile',
                             headers={'Authorization': f'Bearer {seeker_token}'})
    profile = profile_res.get_json()['user']
    skills_list = [s.strip() for s in profile['skills'].split(',') if s.strip()]
    skills_lower = [s.lower() for s in skills_list]
    # No duplicates when compared case-insensitively
    assert len(skills_lower) == len(set(skills_lower)), \
        f"Duplicate skills found: {skills_list}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_deduplicates_skills_case_insensitive -v`

Expected: FAIL — duplicates like `"python"` and `"Python"` both present.

- [ ] **Step 3: Fix deduplication in `parse_resume_text()` endpoint**

In `app.py`, replace the skill merging logic (lines 489-492):

```python
        # Update user's skills
        existing_skills = user.get_skills_list()
        all_skills = list(set(existing_skills + extracted_skills))
        user.set_skills_list(all_skills)
```

with:

```python
        # Merge skills with case-insensitive deduplication
        # Prefer the display-name cased version (from extractor) over user-typed version
        existing_skills = user.get_skills_list()
        seen_lower = {}
        for skill in extracted_skills:
            seen_lower[skill.lower()] = skill
        for skill in existing_skills:
            if skill.lower() not in seen_lower:
                seen_lower[skill.lower()] = skill
        user.set_skills_list(list(seen_lower.values()))
```

This gives priority to the correctly-cased extracted version. If user had `"python"` and extractor returns `"Python"`, the result is `"Python"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_deduplicates_skills_case_insensitive -v`

Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v`

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_profile.py
git commit -m "fix: case-insensitive skill deduplication in resume parser

set() is case-sensitive, so 'python' and 'Python' both survived merge.
Now uses a lowercase-keyed dict, preferring the correctly-cased version
from the extractor over user-typed versions."
```

---

### Task 5: Add Experience Extraction (Bug 5)

**Problem:** The resume parser extracts name, email, phone, education, and skills — but never extracts work experience. The `experience` field on User is never auto-populated.

**Files:**
- Modify: `app.py` (add `extract_experience()` function + wire into endpoint)
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Write failing test for experience extraction**

Add to `tests/test_profile.py`:

```python
def test_resume_parse_extracts_experience(client, seeker_token):
    """Resume parsing should extract and populate work experience."""
    res = client.post('/api/parse-resume-text', json={
        'resumeText': '''John Smith
john@example.com
+1-555-123-4567

Education:
Bachelor of Science in Computer Science, KMITL (2024)

Experience:
Software Engineer at Google (2022-2024)
Junior Developer at Startup Inc (2020-2022)
Intern at TechCorp (Summer 2019)

Skills: Python, JavaScript, React'''
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert 'experience' in data['resume_data']
    experience_lines = data['resume_data']['experience']
    assert len(experience_lines) >= 2, f"Expected at least 2 experience entries, got {experience_lines}"

    # Verify profile was populated
    profile_res = client.get('/api/profile',
                             headers={'Authorization': f'Bearer {seeker_token}'})
    profile = profile_res.get_json()['user']
    assert len(profile['experience']) > 0, "Experience field should be populated"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_extracts_experience -v`

Expected: FAIL — `'experience'` key missing from `resume_data` or experience field empty.

- [ ] **Step 3: Add `extract_experience()` function**

Add after `extract_education()` in `app.py` (after line 93):

```python
# Experience-related keywords
EXPERIENCE_KEYWORDS = [
    'experience', 'work history', 'employment', 'professional experience',
    'work experience', 'career'
]

EXPERIENCE_LINE_PATTERNS = [
    # Lines with date ranges like (2020-2024), 2020–2024, Jan 2020 - Dec 2024
    r'\d{4}\s*[-–—]\s*(?:\d{4}|present|current|now)',
    # Lines with job title keywords
    r'\b(?:engineer|developer|analyst|manager|designer|intern|lead|architect|consultant|coordinator|specialist|director|administrator)\b',
    # Lines with "at" + company pattern
    r'\b(?:at|@)\s+[A-Z]',
]


def extract_experience(text):
    """Extract work experience entries from resume text."""
    lines = text.split('\n')
    experience_list = []
    in_experience_section = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        line_lower = stripped.lower()

        # Detect experience section header
        if any(kw in line_lower for kw in EXPERIENCE_KEYWORDS) and len(stripped) < 40:
            in_experience_section = True
            continue

        # Stop if we hit another section header (short line ending with ':' or all-caps)
        if in_experience_section and len(stripped) < 40:
            if stripped.endswith(':') or stripped.isupper():
                if not any(re.search(p, stripped, re.IGNORECASE) for p in EXPERIENCE_LINE_PATTERNS):
                    in_experience_section = False
                    continue

        # Collect lines in experience section
        if in_experience_section:
            experience_list.append(stripped)
            continue

        # Outside any section, check if line matches experience patterns
        if any(re.search(p, stripped, re.IGNORECASE) for p in EXPERIENCE_LINE_PATTERNS):
            # Exclude education lines
            if not any(kw in line_lower for kw in EDUCATION_KEYWORDS):
                experience_list.append(stripped)

    return experience_list[:5]  # Return top 5 entries
```

- [ ] **Step 4: Wire `extract_experience()` into the endpoint**

In `app.py`, in the `parse_resume_text()` function (around line 487), add the experience extraction call. After the `extracted_education = extract_education(resume_text)` line, add:

```python
        extracted_experience = extract_experience(resume_text)
```

Then after the education auto-populate block (after line 504), add:

```python
        if extracted_experience and not user.experience.strip():
            user.experience = '\n'.join(extracted_experience)
            fields_populated += 1
```

And in the response `resume_data` dict, add the experience key:

```python
        return jsonify({
            "message": "Resume text parsed successfully",
            "resume_data": {
                "name": extracted_name,
                "email": extracted_email,
                "phone": extracted_phone,
                "skills": extracted_skills,
                "education": extracted_education,
                "experience": extracted_experience
            },
            "extracted_skills": extracted_skills,
            "fields_populated": fields_populated,
            "user": user.to_dict()
        }), 200
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_extracts_experience -v`

Expected: PASS

- [ ] **Step 6: Run full test suite**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v`

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add app.py tests/test_profile.py
git commit -m "feat: add experience extraction to resume parser

Resume parser now extracts work experience entries by detecting
experience section headers and matching lines with date ranges,
job title keywords, and company patterns. Auto-populates the
user.experience field if empty."
```

---

### Task 6: Improve Education Extraction (Bug 6)

**Problem:** `extract_education()` does line-level keyword matching. Any line containing "school" or "graduated" is included verbatim — even `"I graduated from high school and went to work"`. Output is joined with `'; '` which looks unnatural.

**Files:**
- Modify: `app.py:80-93`
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Write failing test for education extraction quality**

Add to `tests/test_profile.py`:

```python
def test_resume_parse_education_quality(client, seeker_token):
    """Education extraction should find degree+institution lines, not random mentions."""
    res = client.post('/api/parse-resume-text', json={
        'resumeText': '''Jane Doe

Education:
B.Eng Computer Engineering, KMITL (2024)
High School Diploma, Bangkok International School (2020)

I graduated from high school and went to work at a tech company.
Skills: Python, JavaScript'''
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    data = res.get_json()
    edu = data['resume_data']['education']
    # Should find the actual education entries
    assert len(edu) >= 2, f"Expected at least 2 education entries, got {edu}"
    assert any('KMITL' in e for e in edu), f"Should find KMITL entry: {edu}"
    assert any('Bangkok' in e or 'School' in e for e in edu), f"Should find high school entry: {edu}"

    # Check the populated field uses newlines, not semicolons
    profile_res = client.get('/api/profile',
                             headers={'Authorization': f'Bearer {seeker_token}'})
    profile = profile_res.get_json()['user']
    if profile['education']:
        assert '; ' not in profile['education'] or '\n' in profile['education'], \
            "Education should use newlines for multi-entry formatting"
```

- [ ] **Step 2: Run test to verify current behavior**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_education_quality -v`

Note: This test may pass partially — the main improvement is the join separator and section-awareness.

- [ ] **Step 3: Improve `extract_education()` in `app.py`**

Replace `app.py` lines 80-93:

```python
def extract_education(text):
    """Extract education entries from resume text."""
    lines = text.split('\n')
    education_list = []
    in_education_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        line_lower = stripped.lower()

        # Detect education section header
        if ('education' in line_lower or 'academic' in line_lower) and len(stripped) < 40:
            in_education_section = True
            continue

        # Stop if we hit another section header
        if in_education_section and len(stripped) < 40:
            if stripped.endswith(':') or stripped.isupper():
                if not any(kw in line_lower for kw in EDUCATION_KEYWORDS):
                    in_education_section = False
                    continue

        # Lines in an education section are collected directly
        if in_education_section:
            education_list.append(stripped)
            continue

        # Outside sections, require at least one degree keyword AND one institution keyword
        degree_kws = ['bachelor', 'master', 'phd', 'degree', 'diploma', 'b.tech',
                       'b.e.', 'm.tech', 'b.sc', 'm.sc', 'b.eng', 'm.eng']
        institution_kws = ['university', 'college', 'institute', 'school', 'kmitl']
        has_degree = any(kw in line_lower for kw in degree_kws)
        has_institution = any(kw in line_lower for kw in institution_kws)
        if has_degree and has_institution:
            education_list.append(stripped)

    return education_list[:5]
```

Also update the education auto-populate line in `parse_resume_text()`. Change:

```python
            user.education = '; '.join(extracted_education)
```

to:

```python
            user.education = '\n'.join(extracted_education)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_education_quality -v`

Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v`

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_profile.py
git commit -m "fix: improve education extraction with section detection

Education extraction now detects 'Education:' section headers and
collects entries within. Outside sections, requires both a degree
keyword AND institution keyword to avoid false positives. Uses
newline separator instead of semicolons for natural formatting."
```

---

### Task 7: Final Integration Test and Regression Check

**Problem:** Ensure all 6 fixes work together on a realistic resume and nothing is broken.

**Files:**
- Modify: `tests/test_profile.py`

- [ ] **Step 1: Write comprehensive integration test**

Add to `tests/test_profile.py`:

```python
def test_resume_parse_full_integration(client, seeker_token):
    """Full resume parse should correctly extract all fields from realistic resume."""
    resume = '''Somchai Prasert
somchai.prasert@email.com
+66-81-234-5678

Education:
B.Eng Computer Engineering, KMITL (2020-2024)
High School Diploma, Triam Udom Suksa School (2017-2020)

Experience:
Software Engineer at LINE Thailand (2024-present)
Backend Developer Intern at Agoda (Summer 2023)

Skills:
Python, JavaScript, TypeScript, React, Node.js, Flask, Docker, AWS, PostgreSQL,
Git, Agile, REST API, Machine Learning, HTML, CSS

Familiar with CI/CD pipelines and microservices architecture.
'''
    res = client.post('/api/parse-resume-text', json={
        'resumeText': resume
    }, headers={'Authorization': f'Bearer {seeker_token}'})

    assert res.status_code == 200
    data = res.get_json()
    rd = data['resume_data']

    # Phone: full number, not just country code
    assert rd['phone'] is not None
    assert len(rd['phone']) >= 10

    # Skills: correct casing, no false positives
    skills = data['extracted_skills']
    skills_lower = [s.lower() for s in skills]
    assert 'python' in skills_lower
    assert 'react' in skills_lower
    assert 'aws' in skills_lower
    # Check correct casing
    assert 'AWS' in skills, f"Expected 'AWS' not 'Aws': {skills}"
    assert 'HTML' in skills, f"Expected 'HTML' not 'Html': {skills}"

    # Education: found entries
    assert len(rd['education']) >= 1

    # Experience: found entries
    assert len(rd['experience']) >= 1

    # Profile populated
    profile_res = client.get('/api/profile',
                             headers={'Authorization': f'Bearer {seeker_token}'})
    profile = profile_res.get_json()['user']
    # Skills should have no case-insensitive duplicates
    skill_list = [s.strip() for s in profile['skills'].split(',') if s.strip()]
    skill_list_lower = [s.lower() for s in skill_list]
    assert len(skill_list_lower) == len(set(skill_list_lower)), \
        f"Duplicate skills: {skill_list}"
```

- [ ] **Step 2: Run integration test**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/test_profile.py::test_resume_parse_full_integration -v`

Expected: PASS

- [ ] **Step 3: Run full backend test suite**

Run: `cd "E:/Projects/Intelligent job matching website" && python -m pytest tests/ -v`

Expected: All tests pass (should be 88 + new tests = ~95 tests).

- [ ] **Step 4: Run frontend tests**

Run: `cd "E:/Projects/Intelligent job matching website/frontend" && npx jest --verbose`

Expected: 15/15 pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_profile.py
git commit -m "test: add comprehensive resume parsing integration test

Covers full resume with Thai phone number, correct skill casing,
education section detection, experience extraction, and case-insensitive
deduplication in a single realistic scenario."
```

---

## Quick Reference: Files Modified

| File | Tasks | Purpose |
|------|-------|---------|
| `app.py:24-31` | 2 | Replace `COMMON_SKILLS` with `SKILL_DISPLAY_NAMES` |
| `app.py:66-78` | 1 | Fix `extract_phone()` capture group bug |
| `app.py:80-93` | 6 | Improve `extract_education()` with section detection |
| `app.py:93+` | 5 | Add `extract_experience()` function |
| `app.py:109-116` | 2, 3 | Fix `extract_skills_from_text()` casing + word boundaries |
| `app.py:489-504` | 4, 5 | Fix deduplication + wire experience extraction |
| `tests/test_profile.py` | 1-7 | New tests for each bug fix |
