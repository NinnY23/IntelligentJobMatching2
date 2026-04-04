"""
Tests for prolog_engine.py.
These tests require SWI-Prolog to be installed and on PATH.
Run: pytest tests/test_prolog_engine.py -v
"""
import pytest
from prolog_engine import rank_candidates, rank_jobs


# ---------------------------------------------------------------------------
# rank_candidates
# ---------------------------------------------------------------------------

def test_rank_candidates_returns_sorted_by_score():
    candidates = [
        {'user_id': 1, 'name': 'Alice', 'skills': ['python', 'flask']},
        {'user_id': 2, 'name': 'Bob',   'skills': ['python', 'flask', 'docker']},
    ]
    results = rank_candidates(
        job_required_skills=['python', 'flask', 'docker'],
        job_preferred_skills=['aws'],
        candidates=candidates
    )
    # Both candidates should appear (Bob fully matches required)
    assert len(results) == 2
    # Bob (user_id 2) has the higher score
    assert results[0]['user_id'] == 2
    assert results[0]['score'] > results[1]['score']


def test_rank_candidates_excludes_below_50():
    candidates = [
        {'user_id': 1, 'name': 'Weak', 'skills': ['java']},
    ]
    results = rank_candidates(
        job_required_skills=['python', 'flask', 'docker', 'aws'],
        job_preferred_skills=[],
        candidates=candidates
    )
    # java matches 0/4 required → score = 0 → below 50 → excluded
    assert len(results) == 0


def test_rank_candidates_result_shape():
    candidates = [
        {'user_id': 5, 'name': 'Carol', 'skills': ['python', 'docker']},
    ]
    results = rank_candidates(
        job_required_skills=['python', 'docker'],
        job_preferred_skills=[],
        candidates=candidates
    )
    assert len(results) == 1
    r = results[0]
    assert r['user_id'] == 5
    assert r['name'] == 'Carol'
    assert isinstance(r['score'], float)
    assert isinstance(r['matched_skills'], list)
    assert isinstance(r['missing_skills'], list)
    assert 'python' in r['matched_skills']
    assert 'docker' in r['matched_skills']
    assert r['missing_skills'] == []


def test_rank_candidates_missing_skills_populated():
    candidates = [
        {'user_id': 6, 'name': 'Dan', 'skills': ['python']},
    ]
    results = rank_candidates(
        job_required_skills=['python', 'docker'],
        job_preferred_skills=[],
        candidates=candidates
    )
    assert len(results) == 1
    assert 'docker' in results[0]['missing_skills']


# ---------------------------------------------------------------------------
# rank_jobs
# ---------------------------------------------------------------------------

def test_rank_jobs_returns_sorted():
    jobs = [
        {
            'job_id': 1,
            'position': 'Junior Dev',
            'company': 'A',
            'required_skills': ['python'],
            'preferred_skills': []
        },
        {
            'job_id': 2,
            'position': 'Senior Dev',
            'company': 'B',
            'required_skills': ['python', 'flask'],
            'preferred_skills': ['docker']
        },
    ]
    results = rank_jobs(candidate_skills=['python', 'flask', 'docker'], jobs=jobs)
    assert len(results) == 2
    # Scores must be in descending order
    assert results[0]['score'] >= results[1]['score']


def test_rank_jobs_matched_and_missing():
    jobs = [{
        'job_id': 1,
        'position': 'Dev',
        'company': 'Co',
        'required_skills': ['python', 'docker'],
        'preferred_skills': []
    }]
    results = rank_jobs(candidate_skills=['python'], jobs=jobs)
    assert len(results) == 1
    assert 'python' in results[0]['matched_skills']
    assert 'docker' in results[0]['missing_skills']


def test_rank_jobs_excludes_below_50():
    jobs = [{
        'job_id': 1,
        'position': 'Dev',
        'company': 'Co',
        'required_skills': ['java', 'spring', 'hibernate', 'oracle'],
        'preferred_skills': []
    }]
    results = rank_jobs(candidate_skills=['python'], jobs=jobs)
    assert len(results) == 0


def test_rank_jobs_result_shape():
    jobs = [{
        'job_id': 99,
        'position': 'Tester',
        'company': 'QA Co',
        'required_skills': ['python'],
        'preferred_skills': ['selenium']
    }]
    results = rank_jobs(candidate_skills=['python', 'selenium'], jobs=jobs)
    assert len(results) == 1
    r = results[0]
    assert r['job_id'] == 99
    assert r['position'] == 'Tester'
    assert r['company'] == 'QA Co'
    assert isinstance(r['score'], float)
    assert isinstance(r['matched_skills'], list)
    assert isinstance(r['missing_skills'], list)
