"""
prolog_engine.py
~~~~~~~~~~~~~~~~
Python bridge to SWI-Prolog via pyswip.

Public API:
    rank_candidates(job_required_skills, job_preferred_skills, candidates)
        -> sorted list, score > 0, uses Prolog compute_score/4

    rank_jobs(candidate_skills, jobs)
        -> sorted list, score > 0 only, uses Prolog compute_score/4
"""
from dotenv import load_dotenv
load_dotenv()  # ensure SWI_HOME_DIR is set before pyswip initialises

import os
from pyswip import Prolog

_prolog = None  # lazily initialised singleton


def get_prolog() -> Prolog:
    """Return (and lazily initialise) the Prolog singleton.

    Thread safety: the singleton is initialised on first call. Flask's
    development server is single-threaded, so this is safe. Multi-threaded
    WSGI deployments would need a lock around the None check.
    """
    global _prolog
    if _prolog is None:
        _prolog = Prolog()
        pl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matching.pl')
        _prolog.consult(pl_path)
    return _prolog


def _to_prolog_list(items: list) -> str:
    """Convert a Python list of strings to a Prolog list literal, lower-cased.

    Example: ['Python', 'Flask'] -> "['python','flask']"
    """
    escaped = [f"'{item.lower().strip()}'" for item in items if item.strip()]
    return '[' + ','.join(escaped) + ']'


def rank_candidates(
    job_required_skills: list,
    job_preferred_skills: list,
    candidates: list
) -> list:
    """Rank employee candidates for a job using the Prolog engine.

    Uses compute_score/4 (no 50-point threshold) so ALL candidates with
    any skill overlap appear in the results — useful for employer review.

    Args:
        job_required_skills: list of skill strings (required for the job)
        job_preferred_skills: list of skill strings (nice-to-have)
        candidates: list of dicts with keys: user_id, name, skills (list)

    Returns:
        List of dicts sorted by score descending, score > 0 only.
        Each dict: user_id, name, score (float), matched_skills, missing_skills.
    """
    prolog = get_prolog()
    req = _to_prolog_list(job_required_skills)
    pref = _to_prolog_list(job_preferred_skills)
    req_set = {s.lower().strip() for s in job_required_skills if s.strip()}

    results = []
    for candidate in candidates:
        cskills = _to_prolog_list(candidate['skills'])
        query = f"compute_score({cskills}, {req}, {pref}, Score)"
        solutions = list(prolog.query(query))
        if solutions:
            score = float(solutions[0]['Score'])
            if score <= 0:
                continue
            cand_set = {s.lower().strip() for s in candidate['skills'] if s.strip()}
            matched = sorted(req_set & cand_set)
            missing = sorted(req_set - cand_set)
            results.append({
                'user_id': candidate['user_id'],
                'name': candidate['name'],
                'score': round(score, 1),
                'matched_skills': matched,
                'missing_skills': missing,
            })

    return sorted(results, key=lambda x: x['score'], reverse=True)


def rank_jobs(candidate_skills: list, jobs: list) -> list:
    """Rank job postings for a candidate using the Prolog engine.

    Uses compute_score/4 (no 50-point threshold) so partial matches are
    visible to candidates browsing job listings.

    Args:
        candidate_skills: list of skill strings the candidate has
        jobs: list of dicts with keys: job_id, position, company,
              required_skills (list), preferred_skills (list, optional)

    Returns:
        List of dicts sorted by score descending, score > 0 only.
        Each dict: job_id, position, company, score (float),
                   matched_skills, missing_skills.
    """
    prolog = get_prolog()
    cskills = _to_prolog_list(candidate_skills)
    cand_set = {s.lower().strip() for s in candidate_skills if s.strip()}

    results = []
    for job in jobs:
        req = _to_prolog_list(job['required_skills'])
        pref = _to_prolog_list(job.get('preferred_skills', []))
        query = f"compute_score({cskills}, {req}, {pref}, Score)"
        solutions = list(prolog.query(query))
        if solutions:
            score = float(solutions[0]['Score'])
            if score <= 0:
                continue
            req_set = {s.lower().strip() for s in job['required_skills'] if s.strip()}
            matched = sorted(req_set & cand_set)
            missing = sorted(req_set - cand_set)
            results.append({
                'job_id': job['job_id'],
                'position': job['position'],
                'company': job['company'],
                'score': round(score, 1),
                'matched_skills': matched,
                'missing_skills': missing,
            })

    return sorted(results, key=lambda x: x['score'], reverse=True)
