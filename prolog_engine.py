"""
prolog_engine.py
~~~~~~~~~~~~~~~~
Thin Python wrapper around matching.pl via pyswip.

Public API:
    rank_candidates(job_required_skills, job_preferred_skills, candidates)
    rank_jobs(candidate_skills, jobs)

Both functions return a list of dicts sorted by score descending.

Both rank_candidates and rank_jobs use Python-side scoring (same formula
as matching.pl suitable/4) and include results with score > 0, making
partial matches visible even when below the 50-point threshold.
The Prolog engine is still used for consulting matching.pl and is
available via get_prolog() for direct queries.
"""
from dotenv import load_dotenv
load_dotenv()  # ensure SWI_HOME_DIR is set before pyswip initialises

import os
from pyswip import Prolog

_prolog = None  # module-level singleton


def get_prolog() -> Prolog:
    """Return (and lazily initialise) the Prolog singleton."""
    global _prolog
    if _prolog is None:
        _prolog = Prolog()
        pl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'matching.pl')
        _prolog.consult(pl_path)
    return _prolog


def _to_prolog_list(items: list) -> str:
    """Convert a Python list of strings to a Prolog list literal, lower-cased.

    Example: ['Python', 'Flask'] → "['python','flask']"
    """
    escaped = [f"'{item.lower().strip()}'" for item in items if item.strip()]
    return '[' + ','.join(escaped) + ']'


def _compute_score(cand_skills: set, req_skills: set, pref_skills: set) -> float:
    """Compute the match score in Python using the same formula as matching.pl.

    Score = (|cand ∩ req| / |req|) * 70  +  (|cand ∩ pref| / |pref|) * 30

    Special cases (mirroring the Prolog rules):
      - If req is empty  → required component is 70 (full score)
      - If pref is empty → preferred component is 0
    """
    matched_req = cand_skills & req_skills
    matched_pref = cand_skills & pref_skills

    if req_skills:
        req_score = (len(matched_req) / len(req_skills)) * 70
    else:
        req_score = 70.0

    if pref_skills:
        pref_score = (len(matched_pref) / len(pref_skills)) * 30
    else:
        pref_score = 0.0

    return req_score + pref_score


def rank_candidates(
    job_required_skills: list,
    job_preferred_skills: list,
    candidates: list
) -> list:
    """Rank employee candidates for a job.

    Uses Python-side scoring (same formula as matching.pl) so that partial
    matches with score > 0 but < 50 are still visible to employers.

    Args:
        job_required_skills: list of skill strings (required for the job)
        job_preferred_skills: list of skill strings (nice-to-have)
        candidates: list of dicts, each with keys:
                    - user_id (int)
                    - name    (str)
                    - skills  (list of str)

    Returns:
        List of dicts sorted by score descending. Each dict contains:
            user_id, name, score (float), matched_skills (list),
            missing_skills (list).
        Only candidates with score > 0 are included.
    """
    req_set = {s.lower().strip() for s in job_required_skills if s.strip()}
    pref_set = {s.lower().strip() for s in job_preferred_skills if s.strip()}

    results = []
    for candidate in candidates:
        cand_set = {s.lower().strip() for s in candidate['skills'] if s.strip()}
        score = _compute_score(cand_set, req_set, pref_set)

        if score > 0:
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
    """Rank job postings for a candidate.

    Uses Python-side scoring (same formula as matching.pl) so that partial
    matches with score > 0 but < 50 are still visible to candidates.

    Args:
        candidate_skills: list of skill strings the candidate has
        jobs: list of dicts, each with keys:
              - job_id          (int)
              - position        (str)
              - company         (str)
              - required_skills (list of str)
              - preferred_skills (list of str, optional)

    Returns:
        List of dicts sorted by score descending. Each dict contains:
            job_id, position, company, score (float),
            matched_skills (list), missing_skills (list).
        Only jobs with score > 0 are included.
    """
    cand_set = {s.lower().strip() for s in candidate_skills if s.strip()}

    results = []
    for job in jobs:
        req_set = {s.lower().strip() for s in job['required_skills'] if s.strip()}
        pref_set = {s.lower().strip() for s in job.get('preferred_skills', []) if s.strip()}
        score = _compute_score(cand_set, req_set, pref_set)

        if score > 0:
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
