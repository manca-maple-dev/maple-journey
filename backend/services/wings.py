"""Maple Wingman — Proactive Intelligence Engine with Weighted Match.

Implements:
- Weighted Match Engine (visa_status, city, job_sector) for proactive notifications
- Predictive hurdle analysis: surfaces deadlines, tax windows, grant eligibility
- AI briefing with sovereign tone
- Rule-based + profile-aware nudges that anticipate the user's next problem
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict

from core.config import DEFAULT_WINGS
from core.db import db
from services.profile import profile_summary, conversation_language, conversation_language_instruction

logger = logging.getLogger("maplejourney.wings")


def companion_welcome_message(user: dict, channel: str) -> str:
    """Deterministic first-message copy for Maple companion channels."""
    first_name = (user.get("name") or "there").split(" ")[0]
    language = conversation_language(user)
    if language == "French":
        return (
            f"Salut {first_name} ! Je suis Maple, ton compagnon pour {channel}. "
            "Je t’aide pas à pas avec les dates importantes, les avantages, le travail, le logement "
            "et les infos officielles vérifiées. Donne-moi ton prochain objectif, et je te répondrai simplement."
        )
    return (
        f"Hi {first_name}! I’m Maple, your newcomer companion on {channel}. "
        "I’m here to help you handle Canada one step at a time: deadlines, benefits, jobs, housing, "
        "and official guidance that stays grounded in verified sources. "
        "If you tell me your next goal, I’ll keep it practical and small by small."
    )


async def _openai_briefing(system_prompt: str, user_message: str) -> str:
    """Generate a Wingman briefing with OpenAI."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        return ""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=openai_key)
        model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1")
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=220,
            top_p=0.9,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        logger.exception("openai wingman briefing failed")
        return ""


def _offline_briefing(user: dict, suggestions: List[dict], days: Optional[int]) -> str:
    """Deterministic briefing used when AI is unavailable."""
    first_name = (user.get("name") or "there").split(" ")[0]
    top = suggestions[0]["title"] if suggestions else "complete your profile"
    language = conversation_language(user)
    if language == "French":
        days_text = f"Il te reste {days} jours sur ton permis." if days is not None else "La date d’expiration de ton permis n’est pas encore ajoutée."
        return (
            f"Voici ce qui compte aujourd’hui, {first_name}. {days_text} "
            f"Ton prochain meilleur pas: {top}."
        )
    days_text = f"You have {days} days left on your permit." if days is not None else "Your permit expiry date is not set yet."
    return (
        f"Here's what demands your attention today, {first_name}. {days_text} "
        f"Your next best move is to focus on: {top}."
    )


# ---------------------------------------------------------------------------
# Weighted Match Engine — Proactive notification scoring
# ---------------------------------------------------------------------------
# Each notification template has weighted relevance scores across dimensions.
# A user's profile is scored against all templates; highest-scoring surface first.

PROACTIVE_TEMPLATES = [
    {
        "id": "permit_expiry_critical",
        "weights": {"visa_status": {"work_permit": 10, "study_permit": 10, "visitor": 8}, "days_to_expiry": "<=90"},
        "icon": "alert-triangle",
        "severity": "critical",
        "title_template": "Your {permit_type} expires in {days} days — act now",
        "message_template": (
            "Under IRPR R.189, you maintain implied status only if you apply for extension BEFORE expiry. "
            "Filing now preserves your right to work/study while the application is processed. "
            "After expiry, restoration costs $229 extra and you lose work authorization."
        ),
        "action_label": "See extension steps",
        "action_path": "/app/assessment",
    },
    {
        "id": "permit_expiry_warning",
        "weights": {"visa_status": {"work_permit": 8, "study_permit": 8, "visitor": 6}, "days_to_expiry": "<=180"},
        "icon": "clock",
        "severity": "high",
        "title_template": "Work permit expires in {days} days",
        "message_template": (
            "Best practice: apply for extension at least 30 days before expiry. If you're considering "
            "PR, check if you qualify for a Bridging Open Work Permit (BOWP) under IRPR R.205 C43 — "
            "this keeps you working while your PR application is processed."
        ),
        "action_label": "Plan your extension",
        "action_path": "/app/assessment",
    },
    {
        "id": "tax_filing_deadline",
        "weights": {"visa_status": {"work_permit": 7, "study_permit": 6, "pr": 8}, "month_range": [1, 4]},
        "icon": "calendar",
        "severity": "high",
        "title_template": "Tax filing deadline approaching — unlock your benefits",
        "message_template": (
            "File your T1 return by April 30 to unlock GST/HST credit (~$500/year), Canada Child Benefit "
            "(if applicable), and provincial credits. Filing is required even with zero income. "
            "Free CVITP clinics are available for income under $35,000."
        ),
        "action_label": "Tax filing guide",
        "action_path": "/app/chat",
    },
    {
        "id": "crs_boost_opportunity",
        "weights": {"visa_status": {"work_permit": 9}, "pr_track": True, "score_below": 500},
        "icon": "trending-up",
        "severity": "medium",
        "title_template": "Your CRS is {score} — here's how to push past cut-offs",
        "message_template": (
            "Recent general draws: 480-530 range. A provincial nomination adds +600 (guaranteed ITA). "
            "Other boosts: French TEF/TCF (+25-50 points), 1-year Canadian experience (+53-72 points), "
            "or a valid LMIA job offer (+50/200 points)."
        ),
        "action_label": "Explore CRS boost paths",
        "action_path": "/app/assessment",
    },
    {
        "id": "pr_eligibility_window",
        "weights": {"visa_status": {"work_permit": 9}, "canadian_experience_months": ">=12"},
        "icon": "star",
        "severity": "high",
        "title_template": "You may now be eligible for Canadian Experience Class",
        "message_template": (
            "With 12+ months of skilled Canadian work experience (NOC TEER 0/1/2/3), you likely meet "
            "CEC eligibility under IRPR R.87.1. CEC draws often have lower cut-offs than general FSW draws. "
            "Let's assess your eligibility."
        ),
        "action_label": "Check CEC eligibility",
        "action_path": "/app/assessment",
    },
    {
        "id": "health_coverage_registration",
        "weights": {"visa_status": {"work_permit": 7, "study_permit": 6, "pr": 8}, "days_since_arrival": "<=30"},
        "icon": "heart",
        "severity": "high",
        "title_template": "Register for provincial health insurance now",
        "message_template": (
            "Apply for your provincial health card immediately — waiting periods are counted from your "
            "application date, not arrival date. Bring your permit, proof of address, and passport to "
            "your provincial health office. Until coverage starts, ensure you have private insurance."
        ),
        "action_label": "Health coverage guide",
        "action_path": "/app/chat",
    },
    {
        "id": "citizenship_eligible",
        "weights": {"visa_status": {"pr": 10}, "pr_days": ">=1095"},
        "icon": "flag",
        "severity": "info",
        "title_template": "You may be eligible for Canadian citizenship",
        "message_template": (
            "Under Citizenship Act s.5(1), you need 1,095 days physical presence in Canada within the "
            "last 5 years as a PR. If you've been here continuously since receiving PR, you may qualify. "
            "Application fee: $630. Processing: ~12-14 months."
        ),
        "action_label": "Citizenship requirements",
        "action_path": "/app/chat",
    },
    {
        "id": "refugee_legal_aid",
        "weights": {"visa_status": {"refugee": 10}},
        "icon": "shield",
        "severity": "critical",
        "title_template": "You qualify for FREE legal representation",
        "message_template": (
            "As a refugee claimant, you are entitled to legal aid in most provinces at no cost. "
            "Legal Aid Ontario, Aide juridique du Québec, and Legal Services Society BC all cover "
            "refugee claims. A representative will help prepare your Basis of Claim (BOC) form "
            "and represent you at your IRB hearing."
        ),
        "action_label": "Find free legal aid",
        "action_path": "/app/legal",
    },
    {
        "id": "job_sector_match",
        "weights": {"job_sector": {"healthcare": 8, "tech": 7, "trades": 8, "transport": 7}},
        "icon": "briefcase",
        "severity": "info",
        "title_template": "New {sector} roles matched to your profile",
        "message_template": (
            "I found positions in your sector that are LMIA-exempt, PNP-eligible, or from employers "
            "with positive LMIAs. Some may also qualify for category-based Express Entry draws "
            "targeting your occupation."
        ),
        "action_label": "View matched jobs",
        "action_path": "/app/jobs",
    },
    {
        "id": "onboard_prompt",
        "weights": {"profile_incomplete": True},
        "icon": "sparkles",
        "severity": "high",
        "title_template": "Complete your profile for personalized intelligence",
        "message_template": (
            "I can provide precise, proactive guidance — deadlines, eligibility windows, sector-matched "
            "jobs — but I need to know your situation first. A 2-minute profile unlocks everything."
        ),
        "action_label": "Get started",
        "action_path": "/app/onboarding",
    },
]


def days_until(iso: Optional[str]) -> Optional[int]:
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return max(0, (d - datetime.now(timezone.utc)).days)
    except Exception:
        return None


def _compute_match_score(template: Dict, user: Dict) -> float:
    """Weighted Match Engine: scores a proactive template against user profile."""
    score = 0.0
    weights = template.get("weights", {})
    profile = user.get("profile") or {}
    ntype = (user.get("newcomer_type") or "").lower()
    visa = (user.get("visa_type") or "").lower()
    profile_status = (profile.get("immigration_category") or "").lower()
    days = days_until(user.get("work_permit_expiry"))
    now = datetime.now(timezone.utc)
    city = (profile.get("city") or user.get("city") or "").lower()
    job_sector = (profile.get("job_sector") or user.get("job_sector") or "").lower()

    # Visa status weight
    if "visa_status" in weights:
        vs = weights["visa_status"]
        # Map user's newcomer_type/visa_type to our categories
        user_cat = None
        if ntype == "refugee" or profile_status in ("refugee", "refugee_claimant", "protected_person"):
            user_cat = "refugee"
        elif "pr" in visa or ntype == "permanent_resident" or profile_status == "permanent_resident":
            user_cat = "pr"
        elif "study" in visa or ntype == "student" or profile_status == "student":
            user_cat = "study_permit"
        elif "work" in visa or ntype == "worker" or profile_status in ("worker", "temp_foreign_worker", "visitor_work_permit", "tn_visa"):
            user_cat = "work_permit"
        elif ntype == "visitor" or profile_status == "visitor":
            user_cat = "visitor"

        if user_cat and user_cat in vs:
            score += vs[user_cat]

    # Days to expiry conditions
    if "days_to_expiry" in weights and days is not None:
        condition = weights["days_to_expiry"]
        if condition == "<=90" and days <= 90:
            score += 5.0
        elif condition == "<=180" and days <= 180:
            score += 3.0

    # Month range (for seasonal alerts like tax)
    if "month_range" in weights:
        rng = weights["month_range"]
        if rng[0] <= now.month <= rng[1]:
            score += 4.0

    # PR track
    if weights.get("pr_track"):
        cat = (profile.get("immigration_category") or "").lower()
        if cat in ("express_entry", "provincial_nominee"):
            score += 3.0

    # CRS score threshold
    if "score_below" in weights:
        pr_score = user.get("pr_score", 0)
        if pr_score and pr_score < weights["score_below"]:
            score += 3.0

    # Profile incomplete
    if weights.get("profile_incomplete") and not user.get("profile_completed"):
        score += 8.0

    # Job sector match
    if "job_sector" in weights and job_sector:
        js = weights["job_sector"]
        for sector_key, sector_score in js.items():
            if sector_key in job_sector:
                score += sector_score
                break

    # Days since arrival
    if "days_since_arrival" in weights:
        arrival = user.get("arrival_date") or user.get("created_at")
        if arrival:
            try:
                arr_dt = datetime.fromisoformat(str(arrival).replace("Z", "+00:00"))
                days_since = (now - arr_dt).days
                condition = weights["days_since_arrival"]
                if condition == "<=30" and days_since <= 30:
                    score += 4.0
            except Exception:
                pass

    # Canadian experience months
    if "canadian_experience_months" in weights:
        exp = user.get("canadian_experience_months", 0) or profile.get("canadian_experience_months", 0)
        condition = weights["canadian_experience_months"]
        if condition == ">=12" and exp and exp >= 12:
            score += 5.0

    # PR days (for citizenship eligibility)
    if "pr_days" in weights:
        pr_date = user.get("pr_landing_date")
        if pr_date:
            try:
                pr_dt = datetime.fromisoformat(str(pr_date).replace("Z", "+00:00"))
                pr_days = (now - pr_dt).days
                condition = weights["pr_days"]
                if condition == ">=1095" and pr_days >= 1095:
                    score += 6.0
            except Exception:
                pass

    return score


def _render_template(template: Dict, user: Dict) -> Dict:
    """Render a proactive template with user-specific variables."""
    days = days_until(user.get("work_permit_expiry"))
    profile = user.get("profile") or {}
    job_sector = (profile.get("job_sector") or user.get("job_sector") or "unknown").title()
    permit_type = (user.get("visa_type") or "permit").replace("_", " ")
    pr_score = user.get("pr_score", 0)

    title = template["title_template"].format(
        days=days or "?", permit_type=permit_type, score=pr_score, sector=job_sector
    )
    message = template["message_template"].format(
        days=days or "?", permit_type=permit_type, score=pr_score, sector=job_sector
    )

    return {
        "id": template["id"],
        "icon": template["icon"],
        "severity": template["severity"],
        "title": title,
        "message": message,
        "action_label": template["action_label"],
        "action_path": template["action_path"],
        "requires_confirmation": False,
    }


async def build_suggestions(user: dict) -> List[dict]:
    """Weighted Match Engine: proactive nudges scored and ranked by user relevance."""
    scored_templates = []
    for template in PROACTIVE_TEMPLATES:
        score = _compute_match_score(template, user)
        if score >= 3.0:  # Minimum relevance threshold
            scored_templates.append((score, template))

    # Sort by score descending
    scored_templates.sort(key=lambda x: x[0], reverse=True)

    # Render top 5
    suggestions = []
    for _, template in scored_templates[:5]:
        try:
            rendered = _render_template(template, user)
            suggestions.append(rendered)
        except Exception:
            logger.warning("Failed to render template %s", template["id"])
            continue

    # Fallback: always include at least one suggestion
    if not suggestions:
        suggestions.append({
            "id": "general_legal",
            "icon": "scale",
            "severity": "info",
            "title": "Find free or low-cost legal help",
            "message": "Regulated representatives (RCICs) and immigration lawyers — verified at college-ic.ca.",
            "action_label": "Find legal help",
            "action_path": "/app/legal",
            "requires_confirmation": False,
        })

    return suggestions


async def build_briefing(user: dict) -> dict:
    """Personalized AI briefing (cached 30 min per user) + weighted proactive suggestions.
    
    Sovereign tone: calm authority, no fluff, actionable.
    """
    wings = {**DEFAULT_WINGS, **user.get("wings", {})}
    suggestions = await build_suggestions(user)
    days = days_until(user.get("work_permit_expiry"))

    tone_map = {
        "sovereign": "calm, authoritative, and precisely professional — like a trusted counsellor",
        "friendly": "warm yet professional",
        "concise": "brief and decisive, no filler",
        "professional": "polished and formal",
    }

    facts = (
        f"Name: {user.get('name','there')}. From: {user.get('country_of_origin') or 'unknown'}. "
        f"Status: {user.get('newcomer_type') or 'newcomer'}. Pathway: {user.get('visa_type') or 'not established yet'}. "
        f"CRS/PR score: {user.get('pr_score',0)}. "
        f"Work permit days left: {days if days is not None else 'unknown'}. "
        f"City: {(user.get('profile') or {}).get('city') or 'not set'}. "
        f"Job sector: {(user.get('profile') or {}).get('job_sector') or 'not set'}. "
        f"Top priorities: {', '.join(s['title'] for s in suggestions[:3]) or 'none identified yet'}."
    )
    facts += profile_summary(user)
    uid = str(user["_id"])
    greeting = f"Here's what demands your attention today, {user.get('name','there').split(' ')[0]}."
    now = datetime.now(timezone.utc)
    cache_key = f"{wings.get('tone')}|{user.get('pr_score',0)}|{conversation_language(user)}|{(days // 30) if days is not None else 'x'}|{'-'.join(s['id'] for s in suggestions[:3])}"
    cached = await db.wings_cache.find_one({"user_id": uid})
    fresh = False
    if cached and cached.get("key") == cache_key and cached.get("expires"):
        try:
            fresh = datetime.fromisoformat(cached["expires"]) > now
        except Exception:
            fresh = False
    if fresh:
        greeting = cached["greeting"]
    else:
        try:
            system_prompt = (
                "You are Maple, the Newcomers in Canada Wingman. Speak with sovereign authority: "
                f"calm, {tone_map.get(wings.get('tone'), 'authoritative')}, and precisely actionable. "
                "Write a SHORT 2-sentence personal briefing (max 50 words) that greets the user by "
                "first name and identifies their single most urgent next step based on their situation. "
                "No lists, no markdown, no emojis. Documentary voice."
            )
            system_prompt += conversation_language_instruction(user)
            briefing = await _openai_briefing(system_prompt, f"User situation: {facts}\nWrite the briefing now.")
            greeting = briefing or _offline_briefing(user, suggestions, days)
            await db.wings_cache.update_one(
                {"user_id": uid},
                {"$set": {"user_id": uid, "key": cache_key, "greeting": greeting, "expires": (now + timedelta(minutes=30)).isoformat()}},
                upsert=True,
            )
        except Exception:
            logger.exception("wings briefing generation failed")
            greeting = _offline_briefing(user, suggestions, days)

    return {
        "greeting": greeting,
        "suggestions": suggestions,
        "wings": wings,
        "stats": {
            "pr_score": user.get("pr_score", 0),
            "work_permit_days": days,
            "visa_type": user.get("visa_type") or "Not set",
        },
    }
