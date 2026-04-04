#!/usr/bin/env python
# init_db.py

"""
Database initialization script for Intelligent Job Matching application.

This script creates all database tables and optionally seeds them with sample data.

Usage:
    python init_db.py              # Create tables only
    python init_db.py --seed       # Create tables and seed with sample data
"""

import sys
import os
from app import app, db
from models import User, Job
from datetime import datetime

def init_database():
    """Initialize the database by creating all tables."""
    with app.app_context():
        # Drop all tables (only for development/testing)
        # Uncomment the next line if you want to reset the database
        # db.drop_all()
        
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Display table information
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nCreated tables: {', '.join(tables)}")
        
        return True

def seed_database():
    """Seed the database with sample data."""
    with app.app_context():
        # Check if users already exist
        existing_users = User.query.first()
        if existing_users:
            print("⚠ Database already contains data. Skipping seed...")
            return False
        
        try:
            # Create sample users
            user1 = User(
                email='john@example.com',
                password='password123',
                name='John Doe',
                phone='+1-234-567-8900',
                location='San Francisco, CA',
                bio='Full-stack developer with 5 years of experience',
                skills='Python, JavaScript, React, AWS, Docker'
            )
            
            user2 = User(
                email='jane@example.com',
                password='password123',
                name='Jane Smith',
                phone='+1-345-678-9012',
                location='New York, NY',
                bio='Data scientist and ML engineer',
                skills='Python, Machine Learning, TensorFlow, SQL, Pandas'
            )
            
            user3 = User(
                email='employer@company.com',
                password='password123',
                name='Tech Company HR',
                phone='+1-456-789-0123',
                location='Austin, TX',
                bio='Hiring for tech positions',
                skills='Recruitment, HR, Tech'
            )
            
            db.session.add_all([user1, user2, user3])
            db.session.commit()
            
            print("✓ Sample users created:")
            print(f"  - {user1.email} (John Doe)")
            print(f"  - {user2.email} (Jane Smith)")
            print(f"  - {user3.email} (Tech Company)")
            
            # Create sample job posts
            job1 = Job(
                employer_id=user3.id,
                position='Senior Python Developer',
                company='Tech Company',
                location='Austin, TX',
                description='Looking for experienced Python developers to join our team.',
                required_skills='Python, Django, PostgreSQL, AWS',
                preferred_skills='',
                salary_min='100000',
                salary_max='150000',
                job_type='Full-time',
                openings=3,
                deadline='2026-05-31'
            )

            job2 = Job(
                employer_id=user3.id,
                position='React Frontend Engineer',
                company='Tech Company',
                location='Austin, TX',
                description='Build responsive web applications using React.',
                required_skills='JavaScript, React, HTML, CSS',
                preferred_skills='',
                salary_min='90000',
                salary_max='130000',
                job_type='Full-time',
                openings=2,
                deadline='2026-05-31'
            )

            job3 = Job(
                employer_id=user3.id,
                position='Data Scientist',
                company='Tech Company',
                location='Austin, TX',
                description='Work on ML models and data analysis projects.',
                required_skills='Python, Machine Learning, SQL, TensorFlow',
                preferred_skills='',
                salary_min='110000',
                salary_max='160000',
                job_type='Full-time',
                openings=1,
                deadline='2026-05-31'
            )
            
            db.session.add_all([job1, job2, job3])
            db.session.commit()
            
            print("\n✓ Sample job posts created:")
            print(f"  - {job1.position} at {job1.company}")
            print(f"  - {job2.position} at {job2.company}")
            print(f"  - {job3.position} at {job3.company}")
            
            print("\n✓ Database seeded successfully!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding database: {str(e)}")
            return False

def main():
    """Main function to initialize and optionally seed the database."""
    print("=" * 60)
    print("Intelligent Job Matching - Database Initialization")
    print("=" * 60)
    
    # Initialize database
    if not init_database():
        print("✗ Failed to initialize database")
        sys.exit(1)
    
    # Check if --seed flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == '--seed':
        print("\n" + "-" * 60)
        print("Seeding database with sample data...")
        print("-" * 60)
        
        if not seed_database():
            print("✗ Failed to seed database")
            sys.exit(1)
    else:
        print("\nTo seed the database with sample data, run:")
        print("  python init_db.py --seed")
    
    print("\n" + "=" * 60)
    print("✓ Database initialization complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
