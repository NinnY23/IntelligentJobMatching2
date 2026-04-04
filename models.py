# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for storing user account and profile information."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), default='')
    location = db.Column(db.String(120), default='')
    bio = db.Column(db.Text, default='')
    skills = db.Column(db.Text, default='')  # Stored as comma-separated string
    role = db.Column(db.String(50), default='employee', nullable=False)  # 'employee' or 'employer'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationship with Job posts (One User can have Many Jobs)
    job_posts = db.relationship('Job', backref='employer', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='Job.employer_id')
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'location': self.location,
            'bio': self.bio,
            'skills': self.skills,
            'role': self.role
        }
    
    def get_skills_list(self):
        """Get skills as a list."""
        if not self.skills:
            return []
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
    
    def set_skills_list(self, skills_list):
        """Set skills from a list, removing duplicates."""
        if isinstance(skills_list, list):
            unique_skills = list(set(skills_list))
            self.skills = ', '.join(unique_skills)
        else:
            self.skills = skills_list


class Job(db.Model):
    """Job model for storing job postings."""
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    position = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.Text, default='')  # Stored as comma-separated string
    salary_min = db.Column(db.String(50), default='')
    salary_max = db.Column(db.String(50), default='')
    job_type = db.Column(db.String(50), default='Full-time')
    openings = db.Column(db.Integer, default=1)
    deadline = db.Column(db.String(50), default='')
    applicants = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """Convert job to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'position': self.position,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'skills': self.skills,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'job_type': self.job_type,
            'openings': self.openings,
            'deadline': self.deadline,
            'applicants': self.applicants,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'employer_email': self.employer.email if self.employer else '',
            'employer_id': self.employer_id
        }
    
    def get_skills_list(self):
        """Get skills as a list."""
        if not self.skills:
            return []
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
    
    def set_skills_list(self, skills_list):
        """Set skills from a list, removing duplicates."""
        if isinstance(skills_list, list):
            unique_skills = list(set(skills_list))
            self.skills = ', '.join(unique_skills)
        else:
            self.skills = skills_list
