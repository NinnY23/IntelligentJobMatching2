# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Mock database (in-memory storage for testing)
users_db = {}
reset_tokens = {}
job_posts_db = {}
job_counter = 1

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
        
        if not email or not password or not name:
            return jsonify({"message": "Email, password, and name are required"}), 400
        
        if email in users_db:
            return jsonify({"message": "Email already exists"}), 400
        
        # Store user (in production, use proper password hashing)
        users_db[email] = {
            'email': email,
            'password': password,  # In production: use bcrypt.hashpw()
            'name': name,
            'phone': '',
            'location': '',
            'bio': '',
            'skills': ''
        }
        
        # Generate fake token
        token = f"token_{email}_{datetime.now().timestamp()}"
        
        return jsonify({
            "token": token,
            "user": {
                "email": email,
                "name": name,
                "phone": '',
                "location": '',
                "bio": '',
                "skills": ''
            }
        }), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400
        
        if email not in users_db:
            return jsonify({"message": "Invalid email or password"}), 401
        
        user = users_db[email]
        if user['password'] != password:  # In production: use bcrypt.checkpw()
            return jsonify({"message": "Invalid email or password"}), 401
        
        # Generate fake token
        token = f"token_{email}_{datetime.now().timestamp()}"
        
        return jsonify({
            "token": token,
            "user": {
                "email": email,
                "name": user['name'],
                "phone": user['phone'],
                "location": user['location'],
                "bio": user['bio'],
                "skills": user['skills']
            }
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
        
        if email not in users_db:
            # For security, don't reveal if email exists
            return jsonify({"message": "If the email exists, a reset link has been sent"}), 200
        
        # In production: Generate secure token and send email
        reset_token = f"reset_{email}_{datetime.now().timestamp()}"
        reset_tokens[reset_token] = email
        
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
        # In production: Validate JWT token properly
        
        # For now, extract email from token (format: token_email_timestamp)
        parts = token.split('_')
        if len(parts) < 2:
            return jsonify({"message": "Invalid token"}), 401
        
        email = parts[1]
        
        if email not in users_db:
            return jsonify({"message": "User not found"}), 404
        
        user = users_db[email]
        
        return jsonify({
            "user": {
                "email": email,
                "name": user['name'],
                "phone": user['phone'],
                "location": user['location'],
                "bio": user['bio'],
                "skills": user['skills']
            }
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
        # In production: Validate JWT token properly
        
        # Extract email from token
        parts = token.split('_')
        if len(parts) < 2:
            return jsonify({"message": "Invalid token"}), 401
        
        email = parts[1]
        
        if email not in users_db:
            return jsonify({"message": "User not found"}), 404
        
        data = request.json
        user = users_db[email]
        
        # Update fields
        user['name'] = data.get('name', user['name'])
        user['phone'] = data.get('phone', user['phone'])
        user['location'] = data.get('location', user['location'])
        user['bio'] = data.get('bio', user['bio'])
        user['skills'] = data.get('skills', user['skills'])
        
        return jsonify({
            "user": {
                "email": email,
                "name": user['name'],
                "phone": user['phone'],
                "location": user['location'],
                "bio": user['bio'],
                "skills": user['skills']
            }
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/match-jobs", methods=["GET"])
def match_jobs():
    return jsonify({"status": "ok"})

@app.route("/api/debug/users", methods=["GET"])
def get_all_users():
    """Debug endpoint - View all registered users (remove in production)"""
    return jsonify({
        "total_users": len(users_db),
        "users": {email: {k: v for k, v in user.items() if k != 'password'} 
                  for email, user in users_db.items()}
    }), 200

@app.route("/api/job-posts", methods=["POST"])
def create_job_post():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Unauthorized"}), 401
        
        token = auth_header.split(' ')[1]
        # Extract email from token
        parts = token.split('_')
        if len(parts) < 2:
            return jsonify({"message": "Invalid token"}), 401
        
        employer_email = parts[1]
        
        if employer_email not in users_db:
            return jsonify({"message": "User not found"}), 404
        
        data = request.json
        global job_counter
        
        # Validate required fields
        if not data.get('position') or not data.get('company') or not data.get('location') or not data.get('description'):
            return jsonify({"message": "Missing required fields"}), 400
        
        job_post = {
            'id': job_counter,
            'employer_email': employer_email,
            'company': data.get('company'),
            'position': data.get('position'),
            'location': data.get('location'),
            'description': data.get('description'),
            'skills': data.get('skills', ''),
            'salary_min': data.get('salaryMin', ''),
            'salary_max': data.get('salaryMax', ''),
            'job_type': data.get('type', 'Full-time'),
            'openings': int(data.get('openings', 1)),
            'deadline': data.get('deadline', ''),
            'created_at': datetime.now().isoformat(),
            'applicants': 0
        }
        
        job_posts_db[job_counter] = job_post
        job_counter += 1
        
        return jsonify({
            "message": "Job post created successfully",
            "job": job_post
        }), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/job-posts", methods=["GET"])
def get_job_posts():
    try:
        # Return all job posts
        jobs_list = list(job_posts_db.values())
        return jsonify({
            "total": len(jobs_list),
            "jobs": jobs_list
        }), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route("/api/debug/jobs", methods=["GET"])
def debug_get_jobs():
    """Debug endpoint - View all job posts"""
    return jsonify({
        "total_jobs": len(job_posts_db),
        "jobs": job_posts_db
    }), 200

if __name__ == "__main__":
    app.run(debug=True)
