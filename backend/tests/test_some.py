import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from matcher import match_jobs


def test_match_jobs_scores():
    user = {"skills": ["Python", "SQL"]}
    results = match_jobs(user)
    # the first two jobs should both have full required matches
    assert results[0]["score"] == results[1]["score"]
    assert results[0]["job"] in ["Backend Developer", "Data Analyst"]


def test_missing_skills():
    user = {"skills": ["JavaScript"]}
    results = match_jobs(user)
    # frontend developer requires JavaScript, HTML, CSS; missing two
    front = next(r for r in results if r["job"] == "Frontend Developer")
    assert set(front["missing_skills"]) == {"HTML", "CSS"}