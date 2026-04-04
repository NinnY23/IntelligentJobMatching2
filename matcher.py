from jobs import JOBS

def match_jobs(user):
    user_skills = set(user.get("skills", []))
    results = []

    for job in JOBS:
        required = set(job["required"])
        preferred = set(job["preferred"])

        required_match = len(user_skills & required) / len(required)
        preferred_match = (
            len(user_skills & preferred) / len(preferred)
            if preferred else 0
        )

        score = round((required_match * 0.7 + preferred_match * 0.3) * 100, 2)

        results.append({
            "job": job["title"],
            "score": score,
            "missing_skills": list(required - user_skills)
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)
