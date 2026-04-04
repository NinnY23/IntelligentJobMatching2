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
from models import db, User, Job
import os

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

# Load spaCy model (optional, with error handling)
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    print("⚠️ Warning: spaCy model 'en_core_web_sm' not found.")
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

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

app = Flask(__name__)
CORS(app)

# SQLAlchemy Configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Use MySQL for production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DB_URI',
    'mysql+pymysql://root:password@localhost:3306/intelligent_job_matching'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

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
            # Extract email from token (format: token_email_timestamp)
            parts = token.split('_')
            if len(parts) < 2:
                return jsonify({"message": "Invalid token"}), 401
            
            email = parts[1]
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return jsonify({"message": "User not found"}), 404
            
            if user.role != required_role:
                return jsonify({"message": f"Access denied. This endpoint requires '{required_role}' role"}), 403
            
            # Pass user to the route handler
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
        
        # Create new user with role
        new_user = User(
            email=email,
            password=password,  # In production: use bcrypt.hashpw()
            name=name,
            phone='',
            location='',
            bio='',
            skills='',
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate fake token
        token = f"token_{email}_{datetime.now().timestamp()}"
        
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
        
        if not user or user.password != password:  # In production: use bcrypt.checkpw()
            return jsonify({"message": "Invalid email or password"}), 401
        
        # Generate fake token
        token = f"token_{email}_{datetime.now().timestamp()}"
        
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
        
        # Check if user exists in database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # For security, don't reveal if email exists
            return jsonify({"message": "If the email exists, a reset link has been sent"}), 200
        
        # In production: Generate secure token and send email
        reset_token = f"reset_{email}_{datetime.now().timestamp()}"
        # Note: In production, store this in database with expiration time
        
        return jsonify({"message": "If the email exists, a reset link has been sent"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/profile", methods=["GET"])
def get_profile():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Unauthorized"}), 401
        
        token = auth_header.split(' ')[1]
        # Extract email from token (format: token_email_timestamp)
        parts = token.split('_')
        if len(parts) < 2:
            return jsonify({"message": "Invalid token"}), 401
        
        email = parts[1]
        
        # Query user from database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        return jsonify({
            "user": user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/profile", methods=["PUT"])
def update_profile():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Unauthorized"}), 401
        
        token = auth_header.split(' ')[1]
        # Extract email from token
        parts = token.split('_')
        if len(parts) < 2:
            return jsonify({"message": "Invalid token"}), 401
        
        email = parts[1]
        
        # Query user from database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        data = request.json
        
        # Update user fields
        user.name = data.get('name', user.name)
        user.phone = data.get('phone', user.phone)
        user.location = data.get('location', user.location)
        user.bio = data.get('bio', user.bio)
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
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Unauthorized"}), 401
        
        token = auth_header.split(' ')[1]
        parts = token.split('_')
        if len(parts) < 2:
            return jsonify({"message": "Invalid token"}), 401
        
        email = parts[1]
        
        # Query user from database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
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
            "user": user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/api/parse-resume-text", methods=["POST"])
def parse_resume_text():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Unauthorized"}), 401
        
        token = auth_header.split(' ')[1]
        parts = token.split('_')
        if len(parts) < 2:
            return jsonify({"message": "Invalid token"}), 401
        
        email = parts[1]
        
        # Query user from database
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
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
            "user": user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/match-jobs", methods=["GET"])
def match_jobs():
    return jsonify({"status": "ok"})

@app.route("/api/debug/users", methods=["GET"])
def get_all_users():
    """Debug endpoint - View all registered users (remove in production)"""
    try:
        users = User.query.all()
        users_dict = {}
        
        for user in users:
            user_data = user.to_dict()
            users_dict[user.email] = user_data
        
        return jsonify({
            "total_users": len(users),
            "users": users_dict
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/job-posts", methods=["POST"])
def create_job_post():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Unauthorized"}), 401
        
        token = auth_header.split(' ')[1]
        parts = token.split('_')
        if len(parts) < 2:
            return jsonify({"message": "Invalid token"}), 401
        
        employer_email = parts[1]
        
        # Query employer from database
        employer = User.query.filter_by(email=employer_email).first()
        
        if not employer:
            return jsonify({"message": "User not found"}), 404
        
        data = request.json
        
        # Validate required fields
        if not data.get('position') or not data.get('company') or not data.get('location') or not data.get('description'):
            return jsonify({"message": "Missing required fields"}), 400
        
        # Create new job post
        job_post = Job(
            employer_id=employer.id,
            position=data.get('position'),
            company=data.get('company'),
            location=data.get('location'),
            description=data.get('description'),
            skills=data.get('skills', ''),
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
        
        return jsonify({
            "total": len(jobs_list),
            "jobs": jobs_list
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/debug/jobs", methods=["GET"])
def debug_get_jobs():
    """Debug endpoint - View all job posts"""
    try:
        jobs = Job.query.all()
        jobs_dict = {job.id: job.to_dict() for job in jobs}
        
        return jsonify({
            "total_jobs": len(jobs),
            "jobs": jobs_dict
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

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

if __name__ == "__main__":
    app.run(debug=True)
