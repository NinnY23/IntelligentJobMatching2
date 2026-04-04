# tests/test_profile.py
import pytest


def test_user_has_education_experience_fields(app):
    """User model must have education and experience columns."""
    from models import User
    with app.app_context():
        cols = [c.name for c in User.__table__.columns]
        assert 'education' in cols
        assert 'experience' in cols


def test_profile_update_saves_education_experience(client, seeker_token):
    """PUT /api/profile persists education and experience."""
    res = client.put('/api/profile', json={
        'education': 'B.Eng Computer Engineering, KMITL 2024',
        'experience': '1 year intern at TechCorp',
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['user']['education'] == 'B.Eng Computer Engineering, KMITL 2024'
    assert data['user']['experience'] == '1 year intern at TechCorp'


def test_profile_get_returns_education_experience(client, seeker_token):
    """GET /api/profile returns education and experience after save."""
    client.put('/api/profile', json={
        'education': 'Masters in AI',
        'experience': '3 years at StartupX',
    }, headers={'Authorization': f'Bearer {seeker_token}'})
    res = client.get('/api/profile', headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    user = res.get_json()['user']
    assert user['education'] == 'Masters in AI'
    assert user['experience'] == '3 years at StartupX'


def test_resume_text_populates_profile_fields(client, seeker_token):
    """Resume parsing should populate empty profile fields, not just skills."""
    res = client.post('/api/parse-resume-text', json={
        'resumeText': '''John Smith
john@example.com
+1-555-123-4567
Bachelor of Science in Computer Science from KMITL
3 years experience in Python, Flask, React development
Skills: Python, JavaScript, React, Flask, SQL'''
    }, headers={'Authorization': f'Bearer {seeker_token}'})

    assert res.status_code == 200
    data = res.get_json()
    assert 'fields_populated' in data

    # Verify profile was updated
    profile_res = client.get('/api/profile',
                             headers={'Authorization': f'Bearer {seeker_token}'})
    profile = profile_res.get_json()['user']
    # Skills should be populated
    assert len(profile['skills']) > 0


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
    # Should NOT include the narrative sentence about graduating
    assert not any('went to work' in e for e in edu), \
        f"Should not include narrative sentence: {edu}"


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


def test_upload_resume_extracts_experience(client, seeker_token):
    """PDF upload endpoint should also extract experience like the text endpoint."""
    import io
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    text = """John Smith
john@example.com
+1-555-123-4567

Education:
Bachelor of Science, KMITL (2024)

Experience:
Software Engineer at Google (2022-2024)
Intern at TechCorp (Summer 2019)

Skills: Python, JavaScript, React"""
    page.insert_text((72, 72), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    data = {'resume': (io.BytesIO(pdf_bytes), 'resume.pdf')}
    res = client.post('/api/upload-resume',
                      data=data,
                      content_type='multipart/form-data',
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    result = res.get_json()
    assert 'experience' in result['resume_data'], "resume_data should include experience key"
    assert len(result['resume_data']['experience']) >= 1, \
        f"Should extract experience, got: {result['resume_data'].get('experience')}"


def test_upload_resume_rejects_no_file(client, seeker_token):
    """Upload endpoint should return 400 when no file is provided."""
    res = client.post('/api/upload-resume',
                      data={},
                      content_type='multipart/form-data',
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 400
    assert 'No file' in res.get_json()['message']


def test_upload_resume_rejects_non_pdf(client, seeker_token):
    """Upload endpoint should reject non-PDF files."""
    import io
    data = {'resume': (io.BytesIO(b'not a pdf'), 'resume.txt')}
    res = client.post('/api/upload-resume',
                      data=data,
                      content_type='multipart/form-data',
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 400
    assert 'PDF' in res.get_json()['message']


def test_upload_resume_requires_auth(client):
    """Upload endpoint should require authentication."""
    import io
    data = {'resume': (io.BytesIO(b'fake'), 'resume.pdf')}
    res = client.post('/api/upload-resume',
                      data=data,
                      content_type='multipart/form-data')
    assert res.status_code == 401


def test_upload_resume_extracts_skills_from_pdf(client, seeker_token):
    """Upload endpoint should extract skills from PDF content."""
    import io
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Skills: Python, JavaScript, React, Docker, AWS", fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()

    data = {'resume': (io.BytesIO(pdf_bytes), 'resume.pdf')}
    res = client.post('/api/upload-resume',
                      data=data,
                      content_type='multipart/form-data',
                      headers={'Authorization': f'Bearer {seeker_token}'})
    assert res.status_code == 200
    result = res.get_json()
    skills = result['extracted_skills']
    skills_lower = [s.lower() for s in skills]
    assert 'python' in skills_lower
    assert 'react' in skills_lower
    assert 'aws' in skills_lower
    # Verify correct casing
    assert 'AWS' in skills, f"Expected 'AWS' not 'Aws': {skills}"