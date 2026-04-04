from models import Job, User, db


def test_job_has_required_skills_field(app):
    with app.app_context():
        assert hasattr(Job, 'required_skills'), \
            "Job model must have a 'required_skills' column"


def test_job_has_preferred_skills_field(app):
    with app.app_context():
        assert hasattr(Job, 'preferred_skills'), \
            "Job model must have a 'preferred_skills' column"


def test_job_preferred_skills_defaults_to_empty(app):
    with app.app_context():
        employer = User(
            email='emp@test.com',
            password='x',
            name='Emp',
            role='employer'
        )
        db.session.add(employer)
        db.session.flush()
        job = Job(
            employer_id=employer.id,
            position='Dev',
            company='Co',
            location='BKK',
            description='desc'
        )
        db.session.add(job)
        db.session.commit()
        assert job.preferred_skills == ''


def test_job_get_preferred_skills_list(app):
    with app.app_context():
        employer = User(
            email='emp2@test.com',
            password='x',
            name='Emp2',
            role='employer'
        )
        db.session.add(employer)
        db.session.flush()
        job = Job(
            employer_id=employer.id,
            position='Dev',
            company='Co',
            location='BKK',
            description='desc',
            preferred_skills='python, flask'
        )
        db.session.add(job)
        db.session.commit()
        result = job.get_preferred_skills_list()
        assert 'python' in result
        assert 'flask' in result


def test_job_to_dict_includes_both_skill_fields(app):
    with app.app_context():
        employer = User(
            email='emp3@test.com',
            password='x',
            name='Emp3',
            role='employer'
        )
        db.session.add(employer)
        db.session.flush()
        job = Job(
            employer_id=employer.id,
            position='Dev',
            company='Co',
            location='BKK',
            description='desc',
            required_skills='python',
            preferred_skills='docker'
        )
        db.session.add(job)
        db.session.commit()
        d = job.to_dict()
        assert 'required_skills' in d
        assert 'preferred_skills' in d
