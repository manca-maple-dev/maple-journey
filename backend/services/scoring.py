"""Simplified CRS-style PR readiness scoring."""

EDU_POINTS = {"high_school": 30, "diploma": 90, "bachelor": 120, "two_degrees": 128, "masters": 135, "phd": 150}
LANG_POINTS = {"basic": 0, "intermediate": 60, "advanced": 100, "fluent": 136}


def compute_pr_score(a: dict) -> int:
    """Simplified CRS-style score (excl. provincial nomination bonus)."""
    score = 0
    age = a.get("age") or 0
    if 20 <= age <= 29:
        score += 110
    elif 30 <= age <= 35:
        score += 90
    elif 36 <= age <= 40:
        score += 60
    elif 18 <= age <= 19 or 41 <= age <= 45:
        score += 40
    else:
        score += 10
    score += EDU_POINTS.get(a.get("education"), 0)
    score += LANG_POINTS.get(a.get("language"), 0)
    score += min(int(a.get("experience_years") or 0), 5) * 15
    if a.get("canadian_experience"):
        score += 80
    if a.get("job_offer"):
        score += 50
    if a.get("provincial_nomination"):
        score += 600  # PNP effectively guarantees an ITA
    return min(score, 1200)
