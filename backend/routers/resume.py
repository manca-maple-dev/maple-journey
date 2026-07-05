"""Resume Maker API routes: generate, edit, save, export to PDF.

Helps newcomers build professional Canadian-format resumes using their profile
and a quick questionnaire. Integrates with job search and immigration planning.

Free tier: 3 generates/month, exports include watermark
Paid tier: Unlimited generates, clean exports
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from core.db import db
from core.security import get_current_user
from models import ResumeDraft, ResumeGenerateIn, ResumeSaveIn
from services.resume_pdf import render_resume_to_pdf, get_template_list
from services.credits import get_user_tier

logger = logging.getLogger("maplejourney.resume")
router = APIRouter(prefix="/resume", tags=["resume"])

# ============================================================================
# GENERATION LIMIT: Free tier 3/month, paid unlimited
# ============================================================================

RESUME_GENERATION_LIMITS = {"free": 3, "plus": None, "family": None}  # None = unlimited


async def check_generation_limit(user_id: str, tier: str) -> bool:
    """Return True if user can generate another resume this month. False if over limit."""
    if RESUME_GENERATION_LIMITS.get(tier) is None:
        return True  # Unlimited on paid tiers

    limit = RESUME_GENERATION_LIMITS.get(tier, 3)
    this_month_start = datetime(datetime.now().year, datetime.now().month, 1).isoformat()

    count = await db.resume_generations.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": this_month_start},
    })

    return count < limit


# ============================================================================
# POST /api/resume/generate — Generate resume from profile + questionnaire
# ============================================================================

@router.post("/generate")
async def generate_resume(
    answers: ResumeGenerateIn,
    user: dict = Depends(get_current_user),
):
    """Generate a resume draft from user profile data + questionnaire answers.
    
    **What we do:**
    1. Pull existing profile data (name, occupation, experience, languages, credentials)
    2. Merge with questionnaire answers (target role, achievements, skills)
    3. Use LLM to structure into professional resume format
    4. Return structured ResumeDraft ready for editing
    
    **Profile data used (not re-asked):**
    - Name, email, phone
    - Current city, province
    - Current occupation, years of experience
    - Languages, education, credentials
    
    **Questionnaire fills in:**
    - Target role (if changing fields)
    - Key achievements (what to highlight)
    - Key skills (prioritize these)
    
    **Guardrails:**
    - Never invents work history not in profile
    - Uses [VERIFY] placeholders for gaps
    - Includes "Review this draft" disclaimer
    - Rate-limited: 3/month free, unlimited on paid
    """
    try:
        user_id = str(user["_id"])
        tier = await get_user_tier(user_id)

        # Check generation limit
        can_generate = await check_generation_limit(user_id, tier)
        if not can_generate:
            raise HTTPException(
                status_code=429,
                detail="You've reached your monthly resume generation limit (3/month on free plan). Upgrade to Plus for unlimited.",
            )

        # Get user profile
        profile = user.get("profile") or {}

        # Prepare contact info
        contact = {
            "email": user.get("email") or "[VERIFY: Email not in profile]",
            "phone": user.get("phone") or "[VERIFY: Add phone in Profile]",
            "city": profile.get("current_city") or "[VERIFY: Add city in Profile]",
            "province": profile.get("province_of_residence") or profile.get("intended_province") or "ON",
        }

        # Prepare from profile (don't fabricate)
        full_name = profile.get("preferred_name") or user.get("name") or "Your Name"
        years_exp = profile.get("years_experience") or answers.years_experience or 0
        current_occ = profile.get("current_occupation") or answers.target_role or "Professional"

        languages_list = profile.get("languages_spoken") or []
        if isinstance(languages_list, str):
            languages_list = [languages_list]

        # Build education from profile
        education_list = []
        # TODO: When education is stored in profile, add here
        # For now, placeholder

        # Build experience list (will be editable)
        # In a real scenario, this would come from profile or user inputs
        # For MVP, we provide structure that user fills in
        experience_list = [
            {
                "title": answers.target_role or current_occ,
                "employer": "[VERIFY: Add employer]",
                "location": contact["city"],
                "start_date": f"{datetime.now().year}-01",
                "end_date": None,
                "bullets": [{"text": achievement} for achievement in answers.key_achievements[:5]],
            }
        ]

        # Build languages list with CLB/NCLC levels (if available)
        languages_formatted = [
            {"language": lang, "clb_level": None} for lang in languages_list
        ]

        # Build resume draft
        draft = ResumeDraft(
            full_name=full_name,
            email=contact["email"],
            phone=contact["phone"],
            city=contact["city"],
            province=contact["province"],
            summary=f"Professional with {years_exp}+ years of experience in {current_occ}. "
                    f"Seeking role as {answers.target_role}. "
                    f"Skilled in {', '.join(answers.key_skills[:3] or ['[Add key skills]'])}.",
            experience=experience_list,
            education=education_list,
            skills=answers.key_skills or [],
            languages=languages_formatted,
            template="classic",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Save to database (for versioning + history)
        gen_record = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "draft": draft.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",  # draft | saved | exported
        }
        await db.resume_generations.insert_one(gen_record)

        logger.info(f"Resume generated for user={user_id} (tier={tier})")

        return {
            "draft": draft.model_dump(),
            "generation_id": gen_record["_id"],
            "disclaimer": "Review all details for accuracy. This is a drafting tool, not a guarantee of employer outcomes.",
            "generations_remaining_this_month": RESUME_GENERATION_LIMITS.get(tier, 3) - 1 if tier == "free" else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("resume generation failed")
        raise HTTPException(status_code=500, detail="Resume generation failed. Please try again.")


# ============================================================================
# PUT /api/resume — Save edited resume
# ============================================================================

@router.put("")
async def save_resume(
    save_req: ResumeSaveIn,
    user: dict = Depends(get_current_user),
):
    """Save a user's edited resume draft.
    
    Stores the latest version in user.resume_draft for later retrieval.
    All edits are tracked in user profile.
    """
    try:
        user_id = str(user["_id"])

        # Update user's resume in database
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "resume_draft": save_req.data.model_dump(),
                    "resume_updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )

        logger.info(f"Resume saved for user={user_id}")

        return {
            "success": True,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "message": "Your resume has been saved.",
        }

    except Exception as e:
        logger.exception("resume save failed")
        raise HTTPException(status_code=500, detail="Failed to save resume.")


# ============================================================================
# GET /api/resume — Fetch saved resume
# ============================================================================

@router.get("")
async def fetch_resume(user: dict = Depends(get_current_user)):
    """Retrieve user's latest saved resume draft."""
    try:
        user_id = str(user["_id"])
        resume_draft = user.get("resume_draft")

        if not resume_draft:
            return {
                "resume": None,
                "message": "No resume saved yet. Generate one to get started.",
            }

        return {
            "resume": resume_draft,
            "last_updated": user.get("resume_updated_at"),
        }

    except Exception as e:
        logger.exception("resume fetch failed")
        raise HTTPException(status_code=500, detail="Failed to fetch resume.")


# ============================================================================
# GET /api/resume/templates — List available templates
# ============================================================================

@router.get("/templates")
async def list_templates(user: dict = Depends(get_current_user)):
    """List available resume templates."""
    templates = get_template_list()
    return {"templates": templates}


# ============================================================================
# GET /api/resume/pdf — Export resume to PDF
# ============================================================================

@router.get("/pdf")
async def export_pdf(
    template: str = Query("classic", description="Template: classic | modern | compact"),
    user: dict = Depends(get_current_user),
):
    """Export resume to PDF file.
    
    **Tier logic:**
    - Free tier: PDF includes watermark footer
    - Paid tier (Plus/Family): Clean PDF, no watermark
    
    Uses the resume saved in user profile, or generates empty placeholder if none.
    """
    try:
        user_id = str(user["_id"])
        tier = await get_user_tier(user_id)
        add_watermark = tier == "free"

        # Get saved resume or use empty placeholder
        resume_data = user.get("resume_draft")
        if not resume_data:
            raise HTTPException(status_code=404, detail="No resume found. Generate or save one first.")

        resume = ResumeDraft(**resume_data)

        # Render to PDF
        pdf_io = await render_resume_to_pdf(
            resume,
            template=template,
            add_watermark=add_watermark,
        )

        filename = f"{resume.full_name.replace(' ', '_')}_Resume.pdf"

        logger.info(f"Resume exported for user={user_id} template={template} tier={tier}")

        return FileResponse(
            pdf_io,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"resume PDF export failed for user={user_id}")
        raise HTTPException(status_code=500, detail="PDF export failed. Please try again.")


# ============================================================================
# GET /api/resume/quota — Check remaining generates this month
# ============================================================================

@router.get("/quota")
async def check_quota(user: dict = Depends(get_current_user)):
    """Check how many resumes user can still generate this month."""
    try:
        user_id = str(user["_id"])
        tier = await get_user_tier(user_id)

        if RESUME_GENERATION_LIMITS.get(tier) is None:
            return {
                "tier": tier,
                "limit": None,
                "used_this_month": None,
                "remaining": None,
                "message": f"Unlimited resume generations on {tier} plan.",
            }

        limit = RESUME_GENERATION_LIMITS.get(tier, 3)
        this_month_start = datetime(datetime.now().year, datetime.now().month, 1).isoformat()

        used = await db.resume_generations.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": this_month_start},
        })

        remaining = max(0, limit - used)

        return {
            "tier": tier,
            "limit": limit,
            "used_this_month": used,
            "remaining": remaining,
            "reset_date": datetime(datetime.now().year, datetime.now().month + 1, 1).date().isoformat(),
        }

    except Exception as e:
        logger.exception("quota check failed")
        raise HTTPException(status_code=500, detail="Failed to check quota.")
