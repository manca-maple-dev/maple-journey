"""
Benefits Discovery & Free Application Guide Router
Helps newcomers find and apply for government benefits without paying agents
"""
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel

from core.security import get_current_user
from services.benefits_guide import BenefitsGuideService

logger = logging.getLogger("benefits_router")
router = APIRouter(prefix="/benefits", tags=["benefits"])


class UserProfileIn(BaseModel):
    age: Optional[int] = None
    annual_income: Optional[float] = None
    has_children: Optional[bool] = False
    immigration_status: Optional[str] = None  # e.g., "citizen", "permanent_resident", "refugee"


# ========== PUBLIC ENDPOINTS (no auth required) ==========

@router.get("/all")
async def get_all_benefits():
    """
    Get complete list of all benefits with FREE application guides.
    
    Returns all available benefits with:
    - Eligibility criteria
    - How to apply for FREE
    - Free resources
    - Estimated yearly value
    - What NOT to pay for
    """
    benefits = await BenefitsGuideService.get_all_benefits()
    return {
        "total_benefits": len(benefits),
        "benefits": benefits,
        "note": "All benefits shown can be obtained for FREE - never pay agents for these"
    }


@router.get("/{benefit_id}")
async def get_benefit_details(benefit_id: str):
    """
    Get detailed information about a specific benefit.
    
    Example: /benefits/canada_child_benefit
    
    Returns:
    - Full eligibility requirements
    - Step-by-step FREE application process
    - Free resources and phone numbers
    - Monthly/yearly amount
    - Common scams to avoid
    """
    benefit = await BenefitsGuideService.get_benefit(benefit_id)
    if not benefit:
        return {"error": f"Benefit '{benefit_id}' not found"}
    
    return {
        "benefit": benefit,
        "warning": "⚠️  This benefit is FREE to apply for - never pay agents or consultants",
        "direct_contact": _get_direct_contact(benefit_id)
    }


@router.get("/{benefit_id}/free-application")
async def get_free_application_guide(benefit_id: str):
    """
    Get step-by-step guide to apply for benefit completely for FREE.
    
    This endpoint removes all middlemen and shows the direct government path.
    """
    guide = await BenefitsGuideService.get_how_to_get_free(benefit_id)
    return {
        **guide,
        "do_not_pay": "These services are always provided for FREE by government"
    }


@router.get("/category/{category}")
async def get_benefits_by_category(category: str = Path(..., description="tax, settlement, employment, housing, education, healthcare, legal")):
    """
    Get all benefits in a specific category.
    
    Categories:
    - tax: Tax benefits, credits
    - settlement: Settlement allowances, programs
    - employment: Job and income support
    - housing: Rent subsidies, housing programs
    - education: Student aid, grants
    - healthcare: Medical, prescription assistance
    - legal: Legal aid services
    """
    all_benefits = await BenefitsGuideService.get_all_benefits()
    filtered = [b for b in all_benefits if b.get("category") == category]
    
    return {
        "category": category,
        "count": len(filtered),
        "benefits": filtered
    }


@router.get("/avoid/scams")
async def get_common_scams():
    """
    Get list of common SCAMS where agents charge money for FREE services.
    
    For each scam:
    - How much they charge
    - What it actually costs (FREE)
    - How to get it for FREE
    - Direct government contact
    """
    scams = await BenefitsGuideService.get_free_alternatives()
    
    total_scam_value = sum([
        int(s["cost"].replace("$", "").split("-")[-1].replace(",", ""))
        for s in scams
    ])
    
    return {
        "warning": "🚨 Do NOT pay agents for these services - they are FREE from government",
        "common_scams": scams,
        "potential_money_saved": f"${total_scam_value:,}+ if you avoid these scams",
        "how_to_report_scam": {
            "rcmp": "1-888-773-8888",
            "consumer_protection": "Contact your provincial consumer protection office",
            "scam_alert": "https://www.antifraudcentre.ca"
        }
    }


# ========== AUTHENTICATED ENDPOINTS ==========

@router.post("/assess-my-eligibility")
async def assess_my_eligibility(
    profile: UserProfileIn,
    user: dict = Depends(get_current_user)
):
    """
    Personalized benefit eligibility assessment.
    
    Based on user profile, shows:
    - All benefits they likely qualify for
    - Total potential yearly value
    - Priority order (what to apply for first)
    - Free resources tailored to their situation
    """
    assessment = await BenefitsGuideService.calculate_total_potential_value(profile.dict())
    
    return {
        "your_profile": profile.dict(),
        "assessment": assessment,
        "action_plan": _create_action_plan(assessment["eligible_benefits"]),
        "important_note": "All these benefits are FREE to apply for - use the phone numbers and websites provided"
    }


@router.get("/my-benefits")
async def get_personalized_benefits(user: dict = Depends(get_current_user)):
    """
    Get benefits tailored to authenticated user's profile.
    
    Uses user's stored profile information to show:
    - Most relevant benefits
    - Personalized application steps
    - Free resources in their area (from 211.ca)
    """
    # Get user profile from database
    user_profile = user.get("profile", {})
    
    if not user_profile:
        return {
            "message": "Please complete your profile first to see personalized benefits",
            "next_step": "Fill out your immigration status, age, family size at /domain/profile"
        }
    
    assessment = await BenefitsGuideService.calculate_total_potential_value(user_profile)
    
    return {
        "your_potential_annual_value": assessment["total_potential_value"],
        "eligible_benefits": assessment["eligible_benefits"],
        "recommended_first_steps": assessment["next_steps"],
        "critical_deadlines": _get_critical_deadlines(assessment["eligible_benefits"])
    }


@router.post("/track-application")
async def track_application_status(
    benefit_id: str = Query(...),
    status: str = Query(..., description="started, submitted, approved, rejected, appeal"),
    user: dict = Depends(get_current_user)
):
    """
    Track personal benefits application progress.
    
    Help users monitor their applications and know what to do next.
    """
    logger.info(f"Tracking application: user={user['_id']} benefit={benefit_id} status={status}")
    
    benefit = await BenefitsGuideService.get_benefit(benefit_id)
    if not benefit:
        return {"error": "Benefit not found"}
    
    next_steps = {
        "started": f"Call the program office to confirm they received your application",
        "submitted": f"Wait 4-6 weeks for processing. Check status online.",
        "approved": f"Congratulations! Start receiving {benefit['name']}. Set calendar reminder for annual renewals.",
        "rejected": f"Request detailed reason. Appeal deadline is typically 30 days. Use free legal aid.",
        "appeal": f"Contact legal aid service or community legal clinic (FREE help)"
    }
    
    return {
        "benefit": benefit["name"],
        "current_status": status,
        "next_step": next_steps.get(status, "Contact program office"),
        "free_help_phone": _get_help_phone(benefit_id),
        "free_legal_help": "Contact legal aid in your province for appeals"
    }


# ========== HELPER FUNCTIONS ==========

def _get_direct_contact(benefit_id: str) -> Dict[str, str]:
    """Get direct government contact for benefit"""
    contacts = {
        "canada_child_benefit": {
            "phone": "1-800-959-8281",
            "website": "https://www.canada.ca/ccb",
            "online": "https://www.canada.ca/myaccount"
        },
        "gis_benefit": {
            "phone": "1-800-277-9914",
            "website": "https://www.canada.ca/gis"
        },
        "resettlement_allowance": {
            "phone": "1-888-242-2342",
            "website": "https://www.canada.ca/ircc"
        },
        "student_financial_aid": {
            "phone": "1-888-815-4514",
            "website": "https://www.canada.ca/studentloans"
        },
        "legal_aid": {
            "website": "https://www.211.ca",
            "note": "Search 'legal aid' in your province"
        }
    }
    return contacts.get(benefit_id, {"website": "https://www.211.ca"})


def _get_help_phone(benefit_id: str) -> str:
    """Get phone number to call for help"""
    phones = {
        "canada_child_benefit": "1-800-959-8281",
        "gis_benefit": "1-800-277-9914",
        "resettlement_allowance": "1-888-242-2342",
        "student_financial_aid": "1-888-815-4514",
    }
    return phones.get(benefit_id, "Call 1-800-O-CANADA (1-800-622-6232)")


def _create_action_plan(eligible_benefits: list) -> list:
    """Create prioritized action plan"""
    priority_order = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3}
    sorted_benefits = sorted(
        eligible_benefits,
        key=lambda x: priority_order.get(x.get("priority", "MEDIUM"), 99)
    )
    
    action_plan = []
    for i, benefit in enumerate(sorted_benefits, 1):
        action_plan.append({
            "step": i,
            "benefit": benefit["benefit"],
            "priority": benefit["priority"],
            "estimated_value": benefit["value"],
            "action": f"Get free guide at /benefits/{benefit['benefit'].lower().replace(' ', '_')}/free-application"
        })
    
    return action_plan


def _get_critical_deadlines(eligible_benefits: list) -> list:
    """Get application deadlines for benefits"""
    deadlines = []
    
    for benefit in eligible_benefits:
        if "CCB" in benefit["benefit"]:
            deadlines.append({
                "benefit": benefit["benefit"],
                "deadline": "ASAP - back payments go back 11 months",
                "impact": "You may be missing thousands in payments"
            })
        elif "GIS" in benefit["benefit"]:
            deadlines.append({
                "benefit": benefit["benefit"],
                "deadline": "Age 65 - apply before birthday",
                "impact": "Late applications mean delayed benefits"
            })
        elif "Resettlement" in benefit["benefit"]:
            deadlines.append({
                "benefit": benefit["benefit"],
                "deadline": "Within 12 months of arrival",
                "impact": "One-time payment - don't miss deadline"
            })
    
    return deadlines
