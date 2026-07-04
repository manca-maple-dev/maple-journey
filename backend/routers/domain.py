"""User-facing domain APIs: questionnaire, timeline, documents, jobs, benefits,
resources, legal aid, announcements."""
import re
import uuid
from datetime import datetime, timezone, date, timedelta

from fastapi import APIRouter, Depends, Body, BackgroundTasks

from core.db import db, clean
from core.security import get_current_user
from models import QuestionnaireIn
from services.profile import legal_personalization_context
from services.scoring import compute_pr_score
from services.email_service import send_email_safe
from services.source_registry import source_registry_snapshot, refresh_legal_sources_and_resources
from services.community_sources import fetch_live_community_resources, cache_community_resources, get_cached_community_resources
from services.update_pipeline import run_update_cycle

router = APIRouter(tags=["domain"])


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def legal_resource_relevance(resource: dict, user: dict) -> tuple[int, list[str]]:
    """Return a deterministic relevance score and transparent reasons."""
    ctx = legal_personalization_context(user)
    reasons = []
    score = 0

    resource_province = _normalize_text(resource.get("province"))
    user_province = _normalize_text(ctx.get("province"))
    resource_type = _normalize_text(resource.get("type"))
    newcomer_type = _normalize_text(ctx.get("newcomer_type"))
    description = _normalize_text(resource.get("description"))
    name = _normalize_text(resource.get("name"))

    if user_province and resource_province:
        if resource_province == user_province:
            score += 5
            reasons.append("In your province")
        elif resource_province == "national":
            score += 2
            reasons.append("Available across Canada")

    if newcomer_type:
        refugee_markers = {"refugee", "refugee_claimant", "protected_person"}
        if newcomer_type in refugee_markers and resource_type == "refugee":
            score += 5
            reasons.append("Matches refugee legal support")
        elif newcomer_type in {"worker", "temp_foreign_worker", "visitor_work_permit"} and resource_type == "immigration":
            score += 4
            reasons.append("Matches work or permit issues")
        elif newcomer_type == "student" and "study" in description:
            score += 4
            reasons.append("Relevant to study permit issues")

    for topic in ctx.get("legal_topics") or []:
        if topic and (topic in description or topic in name or topic in resource_type):
            score += 3
            reasons.append(f"Matches your topic: {topic}")

    if resource.get("cost") == "Free":
        score += 1
        reasons.append("Free support")

    return score, reasons[:3]


def job_relevance(job: dict, profile: dict) -> list[str]:
    """Transparent, per-profile relevance tags (no black-box score — blueprint v2)."""
    reasons = []
    title = (job.get("title") or "").lower()
    tags = [t.lower() for t in (job.get("tags") or [])]
    loc = (job.get("location") or "").upper()
    loc_prov = loc.split(",")[-1].strip() if "," in loc else ""

    occ = (profile.get("current_occupation") or "").lower()
    if occ:
        words = [w for w in re.split(r"\W+", occ) if len(w) > 2]
        if any(w in title for w in words) or any(any(w in t for w in words) for t in tags):
            reasons.append("Matches your field")

    prov = (profile.get("province_of_residence") or profile.get("intended_province") or "").upper()
    if prov and prov == loc_prov:
        reasons.append("In your province")

    if "lmia-exempt" in tags:
        reasons.append("LMIA-exempt")
    return reasons


# ----- Onboarding profile (rich, blueprint questionnaire) -----
@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return {"profile": user.get("profile") or {}, "completed": bool(user.get("profile_completed"))}


@router.put("/profile")
async def save_profile(background_tasks: BackgroundTasks, body: dict = Body(...), user: dict = Depends(get_current_user)):
    was_completed = bool(user.get("profile_completed"))
    profile = {k: v for k, v in (body or {}).items() if v not in (None, "", [])}
    updates = {"profile": profile, "profile_completed": True}
    # Mirror a few fields that existing logic (timeline, nudges, briefing) reads.
    cat = profile.get("immigration_category")
    if cat:
        updates["visa_type"] = cat
    if profile.get("work_permit_expiry"):
        updates["work_permit_expiry"] = profile["work_permit_expiry"]
    if profile.get("country_of_citizenship") or profile.get("country_of_birth"):
        updates["country_of_origin"] = profile.get("country_of_citizenship") or profile.get("country_of_birth")
    ntype_map = {
        "refugee_claimant": "refugee", "protected_person": "refugee",
        "refugee": "refugee",
        "student": "student",
        "temp_foreign_worker": "worker", "visitor_work_permit": "worker", "tn_visa": "worker",
        "worker": "worker",
        "visitor": "visitor",
        "permanent_resident": "permanent_resident",
        "spousal_family": "family",
    }
    if cat in ntype_map:
        updates["newcomer_type"] = ntype_map[cat]
    await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
    # Bust the cached briefing so Maple's greeting reflects the new profile immediately.
    await db.wings_cache.delete_one({"user_id": str(user["_id"])})
    # Congratulate on first-time completion only (not on later profile edits).
    if not was_completed and user.get("email"):
        background_tasks.add_task(send_email_safe, user["email"], "onboarding_complete",
                                  name=user.get("name", ""), city=profile.get("current_city", ""))
    return {"profile": profile, "completed": True}


# ----- Questionnaire / PR readiness -----
@router.get("/questionnaire")
async def get_questionnaire(user: dict = Depends(get_current_user)):
    doc = await db.questionnaires.find_one({"user_id": str(user["_id"])})
    if not doc:
        return {"answers": None, "score": user.get("pr_score", 0)}
    return {"answers": doc.get("answers"), "score": doc.get("score", 0)}


@router.post("/questionnaire")
async def save_questionnaire(body: QuestionnaireIn, user: dict = Depends(get_current_user)):
    answers = body.model_dump()
    score = compute_pr_score(answers)
    await db.questionnaires.update_one(
        {"user_id": str(user["_id"])},
        {"$set": {"user_id": str(user["_id"]), "answers": answers, "score": score, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"pr_score": min(score, 600)}})
    return {"answers": answers, "score": score}


# ----- Jobs (shared catalog) & saved jobs -----
@router.get("/jobs")
async def list_jobs(user: dict = Depends(get_current_user)):
    jobs = await db.jobs.find({}).to_list(200)
    saved = await db.saved_jobs.find({"user_id": str(user["_id"])}).to_list(200)
    saved_ids = {s["job_id"] for s in saved}
    profile = user.get("profile") or {}
    out = []
    for j in jobs:
        c = clean(j)
        c["saved"] = c["id"] in saved_ids
        c["relevance"] = job_relevance(j, profile)
        c.pop("match", None)
        out.append(c)
    # Relevant-first, then freshness where available (no black-box score, per blueprint v2).
    out.sort(key=lambda x: (len(x["relevance"]), x.get("posted_at", "")), reverse=True)
    audience_note = {
        "refugee_claimant": "If your work permit is still pending, you may be eligible for an open work permit — check canada.ca before applying.",
        "protected_person": "If your work permit is still pending, you may be eligible for an open work permit — check canada.ca before applying.",
        "student": "As a student, confirm your on- and off-campus work limits before applying.",
        "temp_foreign_worker": "Your permit may be employer-specific — verify a job allows your employer before applying.",
        "visitor_work_permit": "Confirm your permit lets you work for this employer before applying.",
    }.get(profile.get("immigration_category"))
    has_profile = bool(profile.get("current_occupation") or profile.get("current_city"))
    return {"jobs": out, "audience_note": audience_note, "has_profile": has_profile}


@router.post("/jobs/{job_id}/save")
async def toggle_save_job(job_id: str, user: dict = Depends(get_current_user)):
    existing = await db.saved_jobs.find_one({"user_id": str(user["_id"]), "job_id": job_id})
    if existing:
        await db.saved_jobs.delete_one({"_id": existing["_id"]})
        return {"saved": False}
    await db.saved_jobs.insert_one({"user_id": str(user["_id"]), "job_id": job_id})
    return {"saved": True}


# ----- Status & Deadlines self-check (informational only; NO score/strategy) -----
HEALTH_WAIT = {
    "ON": "OHIP may have up to a 3-month waiting period.",
    "BC": "BC MSP may have up to a 3-month waiting period.",
    "QC": "Québec RAMQ may have up to a 3-month waiting period.",
    "NB": "New Brunswick may have up to a 3-month waiting period.",
    "AB": "Alberta (AHCIP) has no waiting period — coverage can start on arrival.",
    "SK": "Saskatchewan has no waiting period.",
    "MB": "Manitoba has no waiting period.",
    "NS": "Nova Scotia may have a waiting period into the following year.",
    "NL": "Newfoundland & Labrador coverage generally starts on arrival.",
}
IRCC = "https://www.canada.ca/en/immigration-refugees-citizenship"


def _pdate(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


@router.get("/status-check")
async def status_check(user: dict = Depends(get_current_user)):
    p = user.get("profile") or {}
    today = date.today()
    cat = p.get("immigration_category")
    cards = []

    prd = _pdate(p.get("pr_received_date"))
    if prd:
        elig = prd + timedelta(days=1095)
        cards.append({"id": "citizenship", "title": "Citizenship eligibility", "kind": "milestone",
                      "detail": "General estimate using the 3-of-5-year (1,095 days) physical-presence rule. Time in Canada before PR can count partially — confirm your exact date with the official residence calculator.",
                      "date": elig.isoformat(), "days": (elig - today).days,
                      "source": "https://www.canada.ca/en/immigration-refugees-citizenship/services/canadian-citizenship/become-canadian-citizen/eligibility.html",
                      "action": "Official eligibility"})

    wpe = _pdate(p.get("work_permit_expiry"))
    if wpe:
        d = (wpe - today).days
        cards.append({"id": "work_permit", "title": "Work permit expiry", "kind": "deadline",
                      "detail": "Apply to extend before it expires — if you apply before the expiry date you may keep working under maintained status while you wait.",
                      "date": wpe.isoformat(), "days": d,
                      "source": f"{IRCC}/services/work-canada/permit/temporary/extend-change-conditions.html",
                      "action": "Review renewal steps"})

    spe = _pdate(p.get("study_permit_expiry"))
    if spe:
        d = (spe - today).days
        cards.append({"id": "study_permit", "title": "Study permit expiry", "kind": "deadline",
                      "detail": "Apply to extend at least 30 days before it expires to keep your student status.",
                      "date": spe.isoformat(), "days": d,
                      "source": f"{IRCC}/services/study-canada/extend-study-permit.html",
                      "action": "Extend your study permit"})

    if p.get("has_sin") is False or (p.get("has_sin") is None and cat):
        cards.append({"id": "sin", "title": "Apply for your SIN", "kind": "todo",
                      "detail": "You need a Social Insurance Number to work and file taxes. It's free and often issued the same day at a Service Canada Centre.",
                      "source": "https://www.canada.ca/en/employment-social-development/services/sin.html",
                      "action": "How to apply"})

    prov = p.get("province_of_residence") or p.get("intended_province")
    if prov:
        note = HEALTH_WAIT.get(prov, "Coverage rules and any waiting period vary by province.")
        cards.append({"id": "health", "title": "Provincial health coverage", "kind": "todo",
                      "detail": f"{note} Apply as soon as you arrive, and consider private insurance for any waiting period.",
                      "source": "https://www.canada.ca/en/health-canada/services/health-care-system/canada-health-care-system-medicare/newcomers.html",
                      "action": "Coverage by province"})

    if cat == "student":
        cards.append({"id": "pgwp", "title": "Post-Graduation Work Permit", "kind": "info",
                      "detail": "Graduating from an eligible program may let you apply for a PGWP to work in Canada. Eligibility depends on your program and institution.",
                      "source": f"{IRCC}/services/study-canada/work/after-graduation.html",
                      "action": "PGWP eligibility"})
    if cat == "spousal_family":
        cards.append({"id": "owp", "title": "Open work permit for spouses", "kind": "info",
                      "detail": "Spouses or common-law partners of some workers or students may be eligible for an open work permit. Eligibility depends on your partner's status.",
                      "source": f"{IRCC}/services/work-canada/permit/temporary/eligibility.html",
                      "action": "Check eligibility"})

    order = {"deadline": 0, "todo": 1, "milestone": 2, "info": 3}
    cards.sort(key=lambda c: (order.get(c["kind"], 5), c.get("days", 9999)))
    return {"status": cat, "profile_completed": bool(user.get("profile_completed")), "cards": cards,
            "generated_at": datetime.now(timezone.utc).isoformat()}


# ----- Benefits (shared catalog) -----
@router.get("/benefits")
@router.get("/domain/benefits")
async def list_benefits(user: dict = Depends(get_current_user)):
    items = await db.benefits.find({}).to_list(200)
    return [clean(i) for i in items]


# ----- Resources (public) -----
@router.get("/resources")
async def list_resources():
    items = await db.resources.find({}).to_list(200)
    return [clean(i) for i in items]


# ----- Legal help (free / low-cost legal aid) -----
@router.get("/legal-resources")
async def list_legal_resources(user: dict = Depends(get_current_user)):
    items = await db.legal_resources.find({}).to_list(200)
    ranked = []
    for item in items:
        cleaned = clean(item)
        score, reasons = legal_resource_relevance(cleaned, user)
        cleaned["relevance_score"] = score
        cleaned["relevance_reasons"] = reasons
        cleaned["freshness_label"] = cleaned.get("freshness_label") or "Needs refresh"
        ranked.append(cleaned)
    ranked.sort(
        key=lambda resource: (
            resource.get("relevance_score", 0),
            resource.get("cost") == "Free",
            resource.get("province") == "National",
        ),
        reverse=True,
    )
    return ranked


@router.get("/source-registry")
async def get_source_registry(user: dict = Depends(get_current_user)):
    rows = await source_registry_snapshot(db)
    return [clean(row) for row in rows]


@router.post("/source-registry/refresh")
async def refresh_source_registry(user: dict = Depends(get_current_user)):
    result = await refresh_legal_sources_and_resources(db)
    return {"ok": True, **result}


# Community resources endpoints moved to routers/community.py
# GET /community/resources - for backward compatibility, calls community router
# (Removed duplicate endpoint to avoid conflicts)


@router.post("/updates/run")
async def run_updates_now(user: dict = Depends(get_current_user)):
    result = await run_update_cycle(db)
    return clean(result)


@router.get("/updates/runs")
async def list_update_runs(limit: int = 20, user: dict = Depends(get_current_user)):
    rows = await db.update_runs.find({}).sort("started_at", -1).to_list(max(1, min(limit, 100)))
    return [clean(row) for row in rows]


# ----- Announcements (authed read) -----
@router.get("/announcements")
async def list_announcements(user: dict = Depends(get_current_user)):
    items = await db.announcements.find({}).sort("created_at", -1).to_list(50)
    return [clean(i) for i in items]


# ----- Landing content (public) -----
@router.get("/content")
async def public_content():
    doc = await db.content.find_one({"_id": "landing"})
    return doc.get("data", {}) if doc else {}
