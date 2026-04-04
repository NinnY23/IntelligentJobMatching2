# app.py

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import io
import fitz  # PyMuPDF
import re
import spacy
import bcrypt
import jwt as pyjwt
from datetime import timedelta
from models import db, User, Job, Application, Message
from sqlalchemy import or_, and_
import os
import uuid
from werkzeug.utils import secure_filename
from prolog_engine import rank_candidates, rank_jobs as prolog_rank_jobs

# Common skills to look for in resumes
COMMON_SKILLS = [
    'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
    'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes',
    'aws', 'azure', 'gcp', 'linux', 'git', 'agile', 'scrum', 'machine learning',
    'data analysis', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'flask', 'django'
]

# Education keywords
EDUCATION_KEYWORDS = [
    'bachelor', 'master', 'phd', 'degree', 'diploma', 'university', 'college',
    'institute', 'school', 'b.tech', 'b.e.', 'm.tech', 'kmitl', 'graduated',
    'graduation', 'postgraduate', 'undergraduate', 'b.sc', 'm.sc'
]

# In-memory store for password reset tokens {token: {email, expires_at}}
password_resets = {}

# Load spaCy model (optional, with error handling)
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("Warning: spaCy model 'en_core_web_sm' not found.")
    print("   Name extraction will use fallback method (first line of resume)")
    nlp = None

def extract_text_from_pdf_fitz(pdf_file):
    """Extract text from PDF file using PyMuPDF (fitz)."""
    pdf_document = fitz.open(stream=pdf_file.read(), filetype='pdf')
    text = ""
    for page in pdf_document:
        text += page.get_text()
    pdf_document.close()
    return text

def extract_email(text):
    """Extract email address from text using regex."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else None

def extract_phone(text):
    """Extract phone number from text using regex."""
    # Pattern for various phone formats
    phone_patterns = [
        r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'(\+\d{1,3})\s?\d{1,14}',
        r'\b\d{10}\b'
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            return phones[0]
    return None

def extract_education(text):
    """Extract education information from text."""
    education_list = []
    lines = text.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        # Check if line contains education keywords
        for keyword in EDUCATION_KEYWORDS:
            if keyword in line_lower:
                education_list.append(line.strip())
                break
    
    return education_list[:3] if education_list else []  # Return top 3

def extract_name(text):
    """Extract name using spaCy NER or from first line."""
    if nlp:
        doc = nlp(text[:500])  # Use first 500 chars for name extraction
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                return ent.text
    
    # Fallback: return first non-empty line as potential name
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if lines:
        return lines[0]
    return None

def extract_skills_from_text(text):
    """Extract skills from resume text by matching against common skills list."""
    text_lower = text.lower()
    found_skills = []
    for skill in COMMON_SKILLS:
        if skill in text_lower:
            found_skills.append(skill.title())  # Capitalize first letter
    return found_skills

app = Flask(__name__)
CORS(app)

# SQLAlchemy Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DB_URI',
    'sqlite:///dev.db'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)


# Global variable for job counter (for ID generation as fallback)
job_counter = 1

# ===== RBAC Decorator for Role-Based Access Control =====
from functools import wraps

def require_role(required_role):
    """Decorator to restrict endpoint access by user role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"message": "Unauthorized"}), 401

            token = auth_header.split(' ')[1]
            try:
                payload = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            except pyjwt.ExpiredSignatureError:
                return jsonify({"message": "Token expired"}), 401
            except pyjwt.InvalidTokenError:
                return jsonify({"message": "Invalid token"}), 401

            user = User.query.get(payload.get('user_id'))
            if not user:
                return jsonify({"message": "User not found"}), 404

            if user.role != required_role:
                return jsonify({"message": f"Access denied. This endpoint requires '{required_role}' role"}), 403

            return f(user, *args, **kwargs)
        return decorated_function
    return decorator

# ===== Helper Function for Job Matching Algorithm (70/30 weighted) =====
def calculate_match_score(user_skills, job_skills, job_description=""):
    """
    Calculate match score between user skills and job requirements.
    Uses 70% weight for required skills and 30% for preferred skills.
    """
    user_skills_set = set(skill.lower().strip() for skill in user_skills)
    job_skills_list = [skill.lower().strip() for skill in job_skills]
    
    # For simplicity, treat all job skills as part of the match
    # In production, you could parse job_description to extract required vs preferred
    matched_skills = user_skills_set & set(job_skills_list)
    
    if not job_skills_list:
        return 0
    
    match_percentage = (len(matched_skills) / len(job_skills_list)) * 100
    return round(match_percentage, 2)

@app.route("/")
def home():
    return "Backend is running!"

@app.route("/api/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        role = data.get('role', 'employee')  # Default to 'employee', can be 'employer'
        
        if role not in ['employee', 'employer']:
            return jsonify({"message": "Invalid role. Must be 'employee' or 'employer'"}), 400
        
        if not email or not password or not name:
            return jsonify({"message": "Email, password, and name are required"}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"message": "Email already exists"}), 400
        
        # Hash the password before storing
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # Create new user with role
        new_user = User(
            email=email,
            password=hashed_password,
            name=name,
            phone='',
            location='',
            bio='',
            skills='',
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT token (24-hour expiry)
        token = pyjwt.encode(
            {
                'user_id': new_user.id,
                'email': new_user.email,
                'role': new_user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

        return jsonify({
            "token": token,
            "user": new_user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400
        
        # Query user from database
        user = User.query.filter_by(email=email).first()
        
        if not user or not bcrypt.checkpw(
            password.encode('utf-8'),
            user.password.encode('utf-8')
        ):
            return jsonify({"message": "Invalid email or password"}), 401
        
        # Generate JWT token (24-hour expiry)
        token = pyjwt.encode(
            {
                'user_id': user.id,
                'email': user.email,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

        return jsonify({
            "token": token,
            "user": user.to_dict(),
            "role": user.role  # Include role for frontend routing
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.json
        email = data.get('email')

        if not email:
            return jsonify({"message": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"message": "If the email exists, a reset link has been sent"}), 200

        import secrets
        reset_token = secrets.token_urlsafe(32)
        password_resets[reset_token] = {
            'email': email,
            'expires_at': datetime.utcnow() + timedelta(hours=1)
        }

        print(f"\n{'='*50}")
        print(f"PASSWORD RESET TOKEN for {email}")
        print(f"Token: {reset_token}")
        print(f"Reset URL: http://localhost:3000/reset-password?token={reset_token}")
        print(f"Expires: {password_resets[reset_token]['expires_at'].isoformat()}")
        print(f"{'='*50}\n")

        return jsonify({
            "message": "If the email exists, a reset link has been sent",
            "reset_token": reset_token
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/reset-password", methods=["POST"])
def reset_password():
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('new_password')

        if not token or not new_password:
            return jsonify({"message": "Token and new password are required"}), 400

        if len(new_password) < 4:
            return jsonify({"message": "Password must be at least 4 characters"}), 400

        reset_data = password_resets.get(token)
        if not reset_data:
            return jsonify({"message": "Invalid or expired reset token"}), 400

        if datetime.utcnow() > reset_data['expires_at']:
            del password_resets[token]
            return jsonify({"message": "Reset token has expired"}), 400

        user = User.query.filter_by(email=reset_data['email']).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        user.password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        db.session.commit()
        del password_resets[token]

        return jsonify({"message": "Password reset successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/api/profile", methods=["GET"])
def get_profile():
    try:
        user, err = get_current_user_or_401()
        if err:
            return err

        return jsonify({
            "user": user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/profile", methods=["PUT"])
def update_profile():
    try:
        user, err = get_current_user_or_401()
        if err:
            return err

        data = request.json

        # Update user fields
        user.name = data.get('name', user.name)
        user.phone = data.get('phone', user.phone)
        user.location = data.get('location', user.location)
        user.bio = data.get('bio', user.bio)
        user.education = data.get('education', user.education)
        user.experience = data.get('experience', user.experience)
        user.skills = data.get('skills', user.skills)
        
        db.session.commit()
        
        return jsonify({
            "user": user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/api/upload-resume", methods=["POST"])
def upload_resume():
    try:
        user, err = get_current_user_or_401()
        if err:
            return err

        if 'resume' not in request.files:
            return jsonify({"message": "No file provided"}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({"message": "No file selected"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"message": "Only PDF files are allowed"}), 400
        
        # Extract text from PDF using PyMuPDF
        pdf_text = extract_text_from_pdf_fitz(io.BytesIO(file.read()))
        
        # Extract structured information
        extracted_name = extract_name(pdf_text)
        extracted_email = extract_email(pdf_text)
        extracted_phone = extract_phone(pdf_text)
        extracted_skills = extract_skills_from_text(pdf_text)
        extracted_education = extract_education(pdf_text)
        
        # Update user's skills
        existing_skills = user.get_skills_list()
        all_skills = list(set(existing_skills + extracted_skills))
        user.set_skills_list(all_skills)

        # Auto-populate empty profile fields from resume
        fields_populated = 0
        if extracted_name and not user.name.strip():
            user.name = extracted_name
            fields_populated += 1
        if extracted_phone and not user.phone.strip():
            user.phone = str(extracted_phone)
            fields_populated += 1
        if extracted_education and not user.education.strip():
            user.education = '; '.join(extracted_education)
            fields_populated += 1

        db.session.commit()

        return jsonify({
            "message": "Resume parsed successfully",
            "resume_data": {
                "name": extracted_name,
                "email": extracted_email,
                "phone": extracted_phone,
                "skills": extracted_skills,
                "education": extracted_education
            },
            "extracted_skills": extracted_skills,
            "fields_populated": fields_populated,
            "user": user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/api/parse-resume-text", methods=["POST"])
def parse_resume_text():
    try:
        user, err = get_current_user_or_401()
        if err:
            return err

        data = request.json
        resume_text = data.get('resumeText', '')
        
        if not resume_text or resume_text.strip() == '':
            return jsonify({"message": "Resume text is required"}), 400
        
        # Extract structured information
        extracted_name = extract_name(resume_text)
        extracted_email = extract_email(resume_text)
        extracted_phone = extract_phone(resume_text)
        extracted_skills = extract_skills_from_text(resume_text)
        extracted_education = extract_education(resume_text)
        
        # Update user's skills
        existing_skills = user.get_skills_list()
        all_skills = list(set(existing_skills + extracted_skills))
        user.set_skills_list(all_skills)

        # Auto-populate empty profile fields from resume
        fields_populated = 0
        if extracted_name and not user.name.strip():
            user.name = extracted_name
            fields_populated += 1
        if extracted_phone and not user.phone.strip():
            user.phone = str(extracted_phone)
            fields_populated += 1
        if extracted_education and not user.education.strip():
            user.education = '; '.join(extracted_education)
            fields_populated += 1

        db.session.commit()

        return jsonify({
            "message": "Resume text parsed successfully",
            "resume_data": {
                "name": extracted_name,
                "email": extracted_email,
                "phone": extracted_phone,
                "skills": extracted_skills,
                "education": extracted_education
            },
            "extracted_skills": extracted_skills,
            "fields_populated": fields_populated,
            "user": user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/match-jobs", methods=["GET"])
def match_jobs():
    return jsonify({"status": "ok"})

@app.route("/api/job-posts", methods=["POST"])
def create_job_post():
    try:
        employer, err = get_current_user_or_401()
        if err:
            return err

        data = request.json
        
        # Validate required fields
        if not data.get('position') or not data.get('company') or not data.get('location') or not data.get('description'):
            return jsonify({"message": "Missing required fields"}), 400
        
        required_skills = data.get('required_skills', data.get('skills', ''))
        preferred_skills = data.get('preferred_skills', '')

        # Create new job post
        job_post = Job(
            employer_id=employer.id,
            position=data.get('position'),
            company=data.get('company'),
            location=data.get('location'),
            description=data.get('description'),
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            salary_min=data.get('salaryMin', ''),
            salary_max=data.get('salaryMax', ''),
            job_type=data.get('type', 'Full-time'),
            openings=int(data.get('openings', 1)),
            deadline=data.get('deadline', ''),
            applicants=0
        )
        
        db.session.add(job_post)
        db.session.commit()
        
        return jsonify({
            "message": "Job post created successfully",
            "job": job_post.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/api/job-posts", methods=["GET"])
def get_job_posts():
    try:
        # Query all job posts from database
        jobs = Job.query.all()
        jobs_list = [job.to_dict() for job in jobs]
        
        return jsonify(jobs_list), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs_alias():
    """Alias for /api/job-posts — kept for frontend compatibility."""
    return get_job_posts()


@app.route('/api/jobs/matches', methods=['GET'])
def get_job_matches():
    """Return jobs ranked by Prolog match score for the authenticated employee."""
    user, err = get_current_user_or_401()
    if err:
        return err

    if user.role != 'employee':
        return jsonify({"message": "Only job seekers can view job matches"}), 403

    candidate_skills = user.get_skills_list()
    if not candidate_skills:
        return jsonify([]), 200

    all_jobs = Job.query.all()
    jobs_input = [
        {
            'job_id': j.id,
            'position': j.position,
            'company': j.company,
            'required_skills': j.get_skills_list(),
            'preferred_skills': j.get_preferred_skills_list(),
        }
        for j in all_jobs
    ]

    ranked = prolog_rank_jobs(candidate_skills, jobs_input)

    job_map = {j.id: j for j in all_jobs}
    results = []
    for r in ranked:
        job_obj = job_map[r['job_id']]
        d = job_obj.to_dict()
        d['match_score'] = r['score']
        d['matched_skills'] = r['matched_skills']
        d['missing_skills'] = r['missing_skills']
        results.append(d)

    return jsonify(results), 200


@app.route('/api/job-posts/<int:job_id>', methods=['PUT'])
@require_role('employer')
def update_job_post(employer, job_id):
    """Employer edits their own job posting."""
    job = Job.query.filter_by(id=job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    data = request.get_json()
    updatable_fields = [
        'position', 'company', 'location', 'description',
        'required_skills', 'preferred_skills',
        'salary_min', 'salary_max', 'job_type', 'openings', 'deadline'
    ]
    for field in updatable_fields:
        if field in data:
            setattr(job, field, data[field])

    db.session.commit()
    return jsonify({"message": "Job updated", "job": job.to_dict()}), 200


@app.route('/api/job-posts/<int:job_id>', methods=['DELETE'])
@require_role('employer')
def delete_job_post(employer, job_id):
    """Employer deletes their own job posting (cascades to applications)."""
    job = Job.query.filter_by(id=job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job deleted"}), 200


@app.route('/api/job-posts/<int:job_id>/candidates', methods=['GET'])
@require_role('employer')
def get_job_candidates(employer, job_id):
    """Return employees ranked by Prolog match score for the given job."""
    job = Job.query.filter_by(id=job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    employees = User.query.filter_by(role='employee').all()
    candidates_input = [
        {
            'user_id': u.id,
            'name': u.name,
            'skills': u.get_skills_list(),
        }
        for u in employees
    ]

    ranked = rank_candidates(
        job_required_skills=job.get_skills_list(),
        job_preferred_skills=job.get_preferred_skills_list(),
        candidates=candidates_input
    )
    return jsonify(ranked), 200


# ===== EMPLOYER ENDPOINTS (Role-Based Access) =====
@app.route("/api/employer/candidates", methods=["GET"])
@require_role('employer')
def get_employer_candidates(user):
    """
    Get top 10 matched candidates for a specific job posting.
    Uses 70/30 weighted matching algorithm.
    Query params: job_id (required)
    """
    try:
        job_id = request.args.get('job_id')
        
        if not job_id:
            return jsonify({"message": "job_id parameter is required"}), 400
        
        # Get the job posting
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({"message": "Job not found"}), 404
        
        # Verify that the job belongs to this employer
        if job.employer_id != user.id:
            return jsonify({"message": "You don't have access to this job's candidates"}), 403
        
        # Get all employees (students)
        employees = User.query.filter_by(role='employee').all()
        
        # Calculate match scores for each employee
        candidates = []
        job_skills = job.get_skills_list()
        
        for employee in employees:
            user_skills = employee.get_skills_list()
            
            # Calculate match score
            match_score = calculate_match_score(user_skills, job_skills, job.description)
            
            # Count matching skills
            matched_count = len(set(s.lower() for s in user_skills) & set(s.lower() for s in job_skills))
            missing_count = len(job_skills) - matched_count
            
            candidates.append({
                'id': employee.id,
                'name': employee.name,
                'email': employee.email,
                'phone': employee.phone,
                'location': employee.location,
                'skills': employee.get_skills_list(),
                'match_score': match_score,
                'matched_skills_count': matched_count,
                'missing_skills_count': missing_count,
                'bio': employee.bio
            })
        
        # Sort by match score (descending) and get top 10
        candidates_sorted = sorted(candidates, key=lambda x: x['match_score'], reverse=True)[:10]
        
        return jsonify({
            'job_id': job_id,
            'job_position': job.position,
            'job_company': job.company,
            'required_skills': job_skills,
            'total_candidates_matched': len([c for c in candidates if c['match_score'] > 0]),
            'top_candidates': candidates_sorted
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/employer/jobs", methods=["GET"])
@require_role('employer')
def get_employer_jobs(user):
    """Get all job postings created by the logged-in employer."""
    try:
        jobs = Job.query.filter_by(employer_id=user.id).all()
        jobs_list = [job.to_dict() for job in jobs]
        
        return jsonify({
            'total_jobs': len(jobs_list),
            'jobs': jobs_list
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# ── Job Application Endpoints ──────────────────────────────────────────────

@app.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
def apply_for_job(job_id):
    """Job seeker submits an application for a job."""
    user, err = get_current_user_or_401()
    if err:
        return err
    if user.role != 'employee':
        return jsonify({"message": "Only job seekers can apply"}), 403

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"message": "Job not found"}), 404

    existing = Application.query.filter_by(job_id=job_id, user_id=user.id).first()
    if existing:
        return jsonify({"message": "Already applied to this job"}), 409

    app_obj = Application(job_id=job_id, user_id=user.id, status='pending')
    db.session.add(app_obj)
    job.applicants = (job.applicants or 0) + 1
    db.session.commit()
    return jsonify({"message": "Application submitted", "application": app_obj.to_dict()}), 201


@app.route('/api/applications', methods=['GET'])
def get_my_applications():
    """Return all applications belonging to the logged-in job seeker, with job details."""
    user, err = get_current_user_or_401()
    if err:
        return err

    apps = Application.query.filter_by(user_id=user.id).all()
    result = []
    for a in apps:
        d = a.to_dict()
        job = Job.query.get(a.job_id)
        if job:
            d['job'] = job.to_dict()
        result.append(d)
    return jsonify(result), 200


@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
def withdraw_application(app_id):
    """Job seeker withdraws an application (not allowed when shortlisted)."""
    user, err = get_current_user_or_401()
    if err:
        return err

    application = Application.query.filter_by(id=app_id, user_id=user.id).first()
    if not application:
        return jsonify({"message": "Application not found"}), 404
    if application.status == 'shortlisted':
        return jsonify({"message": "Cannot withdraw a shortlisted application"}), 400

    job = Job.query.get(application.job_id)
    if job and (job.applicants or 0) > 0:
        job.applicants -= 1
    db.session.delete(application)
    db.session.commit()
    return jsonify({"message": "Application withdrawn"}), 200


@app.route('/api/job-posts/<int:job_id>/applicants', methods=['GET'])
@require_role('employer')
def get_job_applicants(employer, job_id):
    """Return all applicants for a job, ranked by match score."""
    job = Job.query.filter_by(id=job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Job not found"}), 404

    apps = Application.query.filter_by(job_id=job_id).all()
    result = []
    required = [s.strip().lower() for s in (job.required_skills or '').split(',') if s.strip()]
    preferred = [s.strip().lower() for s in (job.preferred_skills or '').split(',') if s.strip()]

    for a in apps:
        applicant = User.query.get(a.user_id)
        if not applicant:
            continue
        candidate_skills = [
            s.strip().lower()
            for s in (applicant.skills or '').split(',') if s.strip()
        ]
        matched = [s for s in required if s in candidate_skills]
        missing = [s for s in required if s not in candidate_skills]
        score = round((len(matched) / len(required) * 70) if required else 0)
        result.append({
            'application_id': a.id,
            'status': a.status,
            'applied_at': a.created_at.isoformat(),
            'user_id': applicant.id,
            'name': applicant.name,
            'email': applicant.email,
            'skills': applicant.skills,
            'bio': applicant.bio or '',
            'education': applicant.education or '',
            'experience': applicant.experience or '',
            'match_score': score,
            'matched_skills': matched,
            'missing_skills': missing,
        })

    result.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(result), 200


@app.route('/api/applications/<int:app_id>/status', methods=['PATCH'])
@require_role('employer')
def update_application_status(employer, app_id):
    """Employer updates application status (shortlist/reject)."""
    data = request.get_json()
    status = data.get('status') if data else None
    if status not in ('pending', 'shortlisted', 'withdrawn'):
        return jsonify({"message": "Invalid status"}), 400

    application = Application.query.get(app_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    # Verify the application belongs to one of the employer's jobs
    job = Job.query.filter_by(id=application.job_id, employer_id=employer.id).first()
    if not job:
        return jsonify({"message": "Forbidden"}), 403

    application.status = status
    db.session.commit()
    return jsonify({"message": "Status updated", "application": application.to_dict()}), 200


@app.route('/api/employer/dashboard', methods=['GET'])
@require_role('employer')
def employer_dashboard(employer):
    """Aggregate stats for the employer's dashboard."""
    jobs = Job.query.filter_by(employer_id=employer.id).all()
    total_jobs = len(jobs)
    job_ids = [j.id for j in jobs]

    # Count total applicants from Application records (reliable counter)
    total_applicants = (
        Application.query.filter(Application.job_id.in_(job_ids)).count()
        if job_ids else 0
    )

    total_shortlisted = (
        Application.query.filter(
            Application.job_id.in_(job_ids),
            Application.status == 'shortlisted'
        ).count()
        if job_ids else 0
    )

    # Build lookup dicts to avoid N+1 queries
    jobs_by_id = {j.id: j for j in jobs}

    recent_apps = (
        Application.query
        .filter(Application.job_id.in_(job_ids))
        .order_by(Application.created_at.desc())
        .limit(5)
        .all()
        if job_ids else []
    )

    # Batch-load applicant users
    applicant_ids = [a.user_id for a in recent_apps]
    users_by_id = {u.id: u for u in User.query.filter(User.id.in_(applicant_ids)).all()} if applicant_ids else {}

    recent = []
    for a in recent_apps:
        applicant = users_by_id.get(a.user_id)
        job = jobs_by_id.get(a.job_id)
        if not applicant or not job:
            app.logger.warning(
                f"Dashboard: missing record for application {a.id} "
                f"(user_id={a.user_id}, job_id={a.job_id})"
            )
            continue
        recent.append({
            'applicant_name': applicant.name,
            'job_position': job.position,
            'applied_at': a.created_at.isoformat(),
            'status': a.status,
        })

    return jsonify({
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'total_shortlisted': total_shortlisted,
        'recent_applications': recent,
    }), 200


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_current_user(request):
    """Extract user from JWT Bearer token. Returns User or None."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ')[1]
    try:
        payload = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return User.query.get(payload['user_id'])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


def get_current_user_or_401():
    """Extract user from JWT. Returns (user, None) or (None, error_response)."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None, (jsonify({"message": "Unauthorized"}), 401)
    token = auth.split(' ')[1]
    try:
        payload = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except pyjwt.ExpiredSignatureError:
        return None, (jsonify({"message": "Token expired"}), 401)
    except pyjwt.InvalidTokenError:
        return None, (jsonify({"message": "Invalid token"}), 401)
    user = User.query.get(payload.get('user_id'))
    if not user:
        return None, (jsonify({"message": "User not found"}), 404)
    return user, None


@app.route('/api/messages', methods=['GET'])
def get_conversations():
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    msgs = Message.query.filter(
        or_(Message.sender_id == user.id, Message.receiver_id == user.id)
    ).order_by(Message.created_at.desc()).all()

    partners = {}
    for m in msgs:
        partner_id = m.receiver_id if m.sender_id == user.id else m.sender_id
        if partner_id not in partners:
            partner = User.query.get(partner_id)
            unread = Message.query.filter_by(
                sender_id=partner_id, receiver_id=user.id, read=False
            ).count()
            partners[partner_id] = {
                'partner_id': partner_id,
                'partner_name': partner.name if partner else 'Unknown',
                'last_message': m.body or f'[{m.attachment_name}]',
                'last_message_at': m.created_at.isoformat(),
                'unread_count': unread
            }
    return jsonify(list(partners.values())), 200


@app.route('/api/messages/<int:other_user_id>', methods=['GET'])
def get_thread(other_user_id):
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    after = request.args.get('after')

    query = Message.query.filter(
        or_(
            and_(Message.sender_id == user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == user.id)
        )
    )
    if after:
        from datetime import datetime as dt
        try:
            after_dt = dt.fromisoformat(after)
            query = query.filter(Message.created_at > after_dt)
        except ValueError:
            pass

    messages = query.order_by(Message.created_at.asc()).paginate(
        page=1, per_page=50, error_out=False
    ).items
    return jsonify([m.to_dict() for m in messages]), 200


@app.route('/api/messages/<int:other_user_id>', methods=['POST'])
def send_message(other_user_id):
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401

    receiver = User.query.get(other_user_id)
    if not receiver:
        return jsonify({"message": "Recipient not found"}), 404

    has_connection = Application.query.join(Job).filter(
        or_(
            and_(Application.user_id == user.id, Job.employer_id == other_user_id),
            and_(Application.user_id == other_user_id, Job.employer_id == user.id)
        )
    ).first()
    if not has_connection:
        return jsonify({"message": "You can only message users connected through a job application"}), 403

    body = request.form.get('body', '')
    attachment_path = ''
    attachment_name = ''
    attachment_type = ''

    if 'attachment' in request.files:
        file = request.files['attachment']
        if file and file.filename and allowed_file(file.filename):
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            if size > MAX_FILE_SIZE:
                return jsonify({"message": "File too large. Max 10MB."}), 400
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'messages', str(user.id))
            os.makedirs(upload_dir, exist_ok=True)
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            attachment_path = f"messages/{user.id}/{filename}"
            attachment_name = secure_filename(file.filename)
            attachment_type = file.content_type or f"application/{ext}"

    if not body and not attachment_path:
        return jsonify({"message": "Message must have text or attachment"}), 400

    msg = Message(
        sender_id=user.id,
        receiver_id=other_user_id,
        body=body,
        attachment_path=attachment_path,
        attachment_name=attachment_name,
        attachment_type=attachment_type
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"message": "Sent", "data": msg.to_dict()}), 201


@app.route('/api/messages/<int:other_user_id>/read', methods=['PATCH'])
def mark_read(other_user_id):
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401
    Message.query.filter_by(
        sender_id=other_user_id, receiver_id=user.id, read=False
    ).update({'read': True})
    db.session.commit()
    return jsonify({"message": "Marked as read"}), 200


@app.route('/api/uploads/messages/<path:filepath>', methods=['GET'])
def serve_message_file(filepath):
    user = get_current_user(request)
    if not user:
        return jsonify({"message": "Unauthorized"}), 401
    parts_path = filepath.split('/')
    if len(parts_path) >= 1:
        try:
            int(parts_path[0])  # validate it's numeric
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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
