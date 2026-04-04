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

    applications = db.relationship(
        'Application',
        backref='applicant',
        lazy='dynamic',
        cascade='all, delete-orphan',
        foreign_keys='Application.user_id'
    )
    
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
    required_skills = db.Column(db.Text, default='')   # was: skills
    preferred_skills = db.Column(db.Text, default='')  # new column
    salary_min = db.Column(db.String(50), default='')
    salary_max = db.Column(db.String(50), default='')
    job_type = db.Column(db.String(50), default='Full-time')
    openings = db.Column(db.Integer, default=1)
    deadline = db.Column(db.String(50), default='')
    applicants = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'employer_id': self.employer_id,
            'position': self.position,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'job_type': self.job_type,
            'openings': self.openings,
            'deadline': self.deadline,
            'applicants': self.applicants,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_skills_list(self):
        """Return required_skills as a Python list."""
        if not self.required_skills:
            return []
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]

    def set_skills_list(self, skills_list):
        """Accept a list or comma string and store in required_skills."""
        if isinstance(skills_list, list):
            self.required_skills = ', '.join(list(set(skills_list)))
        else:
            self.required_skills = skills_list

    def get_preferred_skills_list(self):
        """Return preferred_skills as a Python list."""
        if not self.preferred_skills:
            return []
        return [s.strip() for s in self.preferred_skills.split(',') if s.strip()]

    applications = db.relationship(
        'Application',
        backref='job_rel',
        lazy='dynamic',
        cascade='all, delete-orphan',
        foreign_keys='Application.job_id'
    )


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'shortlisted', 'withdrawn'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Unique constraint: one application per user per job
    __table_args__ = (db.UniqueConstraint('job_id', 'user_id', name='uq_application'),)

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True)
    body = db.Column(db.Text, default='', nullable=True)
    attachment_path = db.Column(db.String(500), default='')
    attachment_name = db.Column(db.String(255), default='')
    attachment_type = db.Column(db.String(100), default='')
    read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'job_id': self.job_id,
            'body': self.body or '',
            'attachment_path': self.attachment_path or '',
            'attachment_name': self.attachment_name or '',
            'attachment_type': self.attachment_type or '',
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
