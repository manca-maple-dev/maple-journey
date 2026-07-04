"""Smart community & settlement resources API.

Provides personalized recommendations based on user profile, with real data
from official sources and intelligent prioritization.
"""
from fastapi import APIRouter, Depends, Query
from core.security import get_current_user
from core.db import db, clean
from services.community_intelligence import (
    get_personalized_communities,
    get_official_211_resources,
    track_community_interest,
    PROVINCIAL_SETTLEMENT_AGENCIES,
    HEALTH_SERVICES,
    LANGUAGE_PROGRAMS,
    EMPLOYMENT_SERVICES,
)

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/personalized")
async def get_personalized(
    user: dict = Depends(get_current_user),
    province: str = Query(None, description="Override user's province"),
    city: str = Query(None, description="Override user's city"),
):
    """
    Get personalized community recommendations based on user profile.
    
    Smart features:
    - Prioritizes resources based on newcomer type & stage (refugee, worker, student)
    - Shows employment help if job-seeking
    - Highlights family services if applicable
    - Emergency resources always visible
    - Language availability filters
    - Province-specific settlement agencies
    """
    user_id = str(user["_id"])
    profile = user.get("profile", {})
    
    recommendations = await get_personalized_communities(
        user_id=user_id,
        user_profile=profile,
        province=province,
        city=city,
    )
    
    return {
        "user_profile": recommendations["user_profile"],
        "personalization_reasons": recommendations["personalization_reasons"],
        "recommendations": recommendations["recommendations"],
        "timestamp": recommendations["timestamp"],
    }


@router.get("/categories")
async def get_categories():
    """Get smart category descriptions with reasoning."""
    return {
        "categories": {
            "worship": {
                "title": "Places of worship",
                "desc": "Find faith communities that welcome newcomers",
                "why_smart": "Built relationships strengthen settlement",
                "for": "spiritual cultural community-building"
            },
            "grocery": {
                "title": "Ethnic groceries & restaurants",
                "desc": "Familiar foods and cultural hubs in your neighbourhood",
                "why_smart": "Cultural connection reduces isolation",
                "for": "cultural health mental-wellbeing"
            },
            "foodbank": {
                "title": "Food banks & community meals",
                "desc": "Free food programs with zero judgment",
                "why_smart": "Saves money while building community",
                "for": "emergency financial community"
            },
            "shelter": {
                "title": "Shelters & housing help",
                "desc": "Emergency and transitional housing support",
                "why_smart": "Housing is the foundation of settlement",
                "for": "emergency housing settlement"
            },
            "cultural": {
                "title": "Settlement & cultural centres",
                "desc": "Organizations designed specifically for newcomers",
                "why_smart": "Staffed by people who understand your journey",
                "for": "settlement cultural community"
            },
            "health": {
                "title": "Community health centres",
                "desc": "Medical care with interpretation and newcomer knowledge",
                "why_smart": "Navigate healthcare system with support",
                "for": "health legal settlement"
            },
            "language": {
                "title": "ESL & language programs",
                "desc": "Free government-funded English and French classes",
                "why_smart": "Language = Employment + Confidence + Community",
                "for": "employment education settlement"
            },
            "childcare": {
                "title": "Childcare & family support",
                "desc": "Daycare, parenting, school enrollment help",
                "why_smart": "Enables parents to work/study while kids thrive",
                "for": "family employment education"
            },
            "jobsupport": {
                "title": "Job help & credential recognition",
                "desc": "Resume, interviews, credential assessment",
                "why_smart": "Employment is often the #1 priority",
                "for": "employment economic settlement"
            },
            "education": {
                "title": "Schools & tutoring",
                "desc": "School enrollment, tutoring, adult learning",
                "why_smart": "Education accelerates integration",
                "for": "education family settlement"
            },
            "mentalhealth": {
                "title": "Mental health support",
                "desc": "Counselling, crisis lines, trauma services",
                "why_smart": "Mental health is foundation for everything",
                "for": "health mental-health crisis"
            },
            "settlement": {
                "title": "Settlement agencies",
                "desc": "Comprehensive support: housing, jobs, legal, language",
                "why_smart": "One-stop shop for new arrivals",
                "for": "settlement comprehensive newcomer"
            }
        },
        "description": "Each category explains WHY it matters for newcomers and WHAT benefit it provides"
    }


@router.get("/resources")
async def get_resources_by_category(
    user: dict = Depends(get_current_user),
    province: str = Query("ON", description="Province code (ON, BC, AB, QC, MB, NS, NB, SK, PE, NL)"),
    city: str = Query("", description="City name for location-specific resources"),
):
    """
    Get all real resources organized by category for a given province.
    
    Returns actual provider names and descriptions from official sources:
    - Settlement agencies (province-specific)
    - Health services (by province/city)
    - Language programs (province-specific)
    - Employment services (province-specific)
    - Emergency resources (national)
    """
    resources = {
        "settlement": [],
        "health": [],
        "language": [],
        "jobsupport": [],
        "mentalhealth": [],
    }
    
    # ===== SETTLEMENT AGENCIES (Province-specific) =====
    if province in PROVINCIAL_SETTLEMENT_AGENCIES:
        resources["settlement"] = [
            {
                "id": agency["name"].lower().replace(" ", "-"),
                "name": agency["name"],
                "type": agency["type"],
                "languages": agency["languages"],
                "focus_areas": agency["focus"],
                "description": f"{agency['type'].title()} organization - Specializes in {', '.join(agency['focus'])}",
                "icon": _icon_for_type(agency["type"]),
                "verified": True,
                "source": "Government of Canada Settlement Directory",
            }
            for agency in PROVINCIAL_SETTLEMENT_AGENCIES[province]
        ]
    
    # ===== HEALTH SERVICES (Province + City) =====
    if province in HEALTH_SERVICES:
        health_providers = []
        if city and city in HEALTH_SERVICES[province]:
            for service in HEALTH_SERVICES[province][city]:
                health_providers.append({
                    "id": service.lower().replace(" ", "-"),
                    "name": service,
                    "type": "Health & Mental Health",
                    "description": "Community health centre with cultural competency and interpretation services",
                    "city": city,
                    "languages": ["EN", "FR"],
                    "icon": "HeartPulse",
                    "verified": True,
                    "source": "Provincial Health Directory",
                })
        resources["health"] = health_providers
    
    # ===== LANGUAGE PROGRAMS (Province-specific) =====
    if province in LANGUAGE_PROGRAMS:
        resources["language"] = [
            {
                "id": program.lower().replace(" ", "-"),
                "name": program,
                "type": "Language Training",
                "description": "Government-funded English or French language program for newcomers",
                "languages": ["EN", "FR"],
                "cost": "Free or subsidized",
                "icon": "Languages",
                "verified": True,
                "source": f"Government of {province} - Language Services",
            }
            for program in LANGUAGE_PROGRAMS.get(province, [])
        ]
    
    # ===== EMPLOYMENT SERVICES (Province-specific) =====
    if province in EMPLOYMENT_SERVICES:
        resources["jobsupport"] = [
            {
                "id": service.lower().replace(" ", "-"),
                "name": service,
                "type": "Employment Support",
                "description": "Resume help, interview prep, credential recognition, and job matching for newcomers",
                "languages": ["EN", "FR"],
                "icon": "BriefcaseBusiness",
                "verified": True,
                "source": f"Government of {province} - Employment Services",
            }
            for service in EMPLOYMENT_SERVICES.get(province, [])
        ]
    
    # ===== EMERGENCY & MENTAL HEALTH (National) =====
    resources["mentalhealth"] = [
        {
            "id": "211-ca",
            "name": "211.ca",
            "type": "Emergency & Crisis Support",
            "description": "Call or chat 24/7 for food, shelter, mental health crisis, and community services",
            "action": "Call 2-1-1 or text 211",
            "languages": ["EN", "FR", "Multiple"],
            "cost": "Free",
            "icon": "AlertTriangle",
            "verified": True,
            "source": "Canada's National Helpline",
            "hours": "24/7",
        },
        {
            "id": "crisis-text-line",
            "name": "Crisis Text Line",
            "type": "Mental Health Crisis",
            "description": "Confidential text support for mental health crisis and emotional distress",
            "action": "Text HOME to 741741",
            "languages": ["EN"],
            "cost": "Free",
            "icon": "Phone",
            "verified": True,
            "source": "Crisis Text Line Canada",
            "hours": "24/7",
        }
    ]
    
    return {
        "province": province,
        "city": city if city else "All cities",
        "resources": resources,
        "total_count": sum(len(v) for v in resources.values()),
        "data_sources": [
            "Government of Canada Settlement Directory",
            "Provincial Health Services",
            "Provincial Employment Programs",
            "211.ca National Database",
        ]
    }



@router.get("/settlement-agencies")
async def get_settlement_agencies(province: str = Query(..., description="Province code (ON, BC, AB, etc)")):
    """
    Get official provincial settlement agencies.
    
    These are verified, government-recognized organizations that help newcomers
    with integration, housing, employment, legal matters, etc.
    """
    if province not in PROVINCIAL_SETTLEMENT_AGENCIES:
        return {"error": f"Province {province} not found", "available": list(PROVINCIAL_SETTLEMENT_AGENCIES.keys())}
    
    agencies = PROVINCIAL_SETTLEMENT_AGENCIES[province]
    return {
        "province": province,
        "count": len(agencies),
        "agencies": [
            {
                "name": a["name"],
                "type": a["type"],
                "languages": a["languages"],
                "focus_areas": a["focus"],
                "icon": _icon_for_type(a["type"]),
            }
            for a in agencies
        ]
    }


@router.get("/211-resources")
async def search_211(
    query: str = Query(..., description="What to search for (e.g. 'food bank', 'mental health')"),
    province: str = Query(..., description="Province code"),
):
    """
    Search 211.ca for real-time community resources.
    
    211.ca is Canada's official helpline for community, social, and health services.
    Results are up-to-date and verified.
    """
    result = await get_official_211_resources(query, province)
    return result


@router.post("/track-interest")
async def track_interest(
    user: dict = Depends(get_current_user),
    category: str = Query(...),
    action: str = Query("viewed", description="viewed, clicked, saved, etc"),
):
    """Track user interest in communities to improve personalization."""
    user_id = str(user["_id"])
    await track_community_interest(user_id, category, action)
    return {"status": "tracked"}


@router.get("/nearby-map-search")
async def generate_map_search(
    category: str = Query(...),
    city: str = Query(...),
):
    """
    Generate a smart map search URL with proper formatting.
    
    Opens OpenStreetMap, Google Maps, or 211.ca based on category.
    """
    search_params = {
        "worship": f"place of worship in {city}",
        "grocery": f"ethnic grocery supermarket in {city}",
        "foodbank": f"food bank in {city}",
        "shelter": f"shelter emergency housing in {city}",
        "cultural": f"settlement agency community centre in {city}",
        "health": f"community health centre clinic in {city}",
        "language": f"ESL English language classes in {city}",
        "childcare": f"childcare daycare in {city}",
        "jobsupport": f"employment centre resume help in {city}",
        "education": f"school enrollment tutoring in {city}",
        "mentalhealth": f"mental health counselling crisis in {city}",
        "settlement": f"settlement agency in {city}",
    }
    
    query = search_params.get(category, f"{category} in {city}")
    
    return {
        "category": category,
        "city": city,
        "search_query": query,
        "urls": {
            "openstreetmap": f"https://www.openstreetmap.org/search?query={query.replace(' ', '+')}",
            "google_maps": f"https://www.google.com/maps/search/{query.replace(' ', '+')}",
            "211": f"https://www.211.ca/" if category in ["foodbank", "shelter", "mentalhealth"] else None,
        }
    }


def _icon_for_type(agency_type: str) -> str:
    """Map agency type to icon name."""
    mapping = {
        "multi-service": "Users",
        "refugee": "Shield",
        "emergency": "AlertTriangle",
        "health": "HeartPulse",
        "employment": "BriefcaseBusiness",
        "cultural": "Heart",
        "food": "Utensils",
        "housing": "Home",
    }
    return mapping.get(agency_type, "MapPin")
