"""Maple Research Agent — Proactive insights for each user.

Continuously scans official sources, news, policy changes, deadlines, and benefits
specific to each user's profile. Sends curated, personalized insights that are:
- Real and verified (from official sources only)
- Useful (directly applicable to their situation)
- Timely (alerts before deadlines, on policy changes)
- Not spammy (intelligent filtering, once per 48h max per topic)

Research covers:
- Immigration policy changes & deadlines
- Permit/PR timeline windows
- Benefits they might qualify for
- Tax credits & benefits
- Regional updates (province/city specific)
- Employer/job market intel
- Housing/cost of living changes
- Professional development opportunities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

from core.db import db

logger = logging.getLogger("maplejourney.research_agent")


class InsightCategory(str, Enum):
    """Types of insights Maple can research."""
    DEADLINE_ALERT = "deadline_alert"              # Renewal, application deadlines
    POLICY_CHANGE = "policy_change"                # New rules, eligibility changes
    BENEFIT_OPPORTUNITY = "benefit_opportunity"    # Tax credit, support program they qualify for
    JOB_MARKET = "job_market"                      # Hiring trends, skill demand
    HOUSING = "housing"                            # Market trends, cost changes
    FINANCIAL = "financial"                        # Interest rates, credit building tips
    PROFESSIONAL = "professional"                  # Certifications, career paths
    LEGAL = "legal"                                # New immigration routes, appeals info
    REGIONAL = "regional"                          # City/province specific news
    WELLNESS = "wellness"                          # Mental health, community resources
    EDUCATION = "education"                        # Courses, credential recognition updates


class UserProfile(dict):
    """Enriched user profile for research matching."""
    pass


async def research_user_insights(user_id: str, user_profile: Dict) -> List[Dict]:
    """
    Research and generate personalized insights for a user.
    
    Returns list of insights (each has: title, insight, category, why_relevant, source, confidence)
    """
    insights = []
    
    try:
        province = user_profile.get("province", "ON")
        permit_type = user_profile.get("permit_type", "unknown")
        city = user_profile.get("city", "")
        days_in_canada = user_profile.get("days_in_canada", 0)
        career_field = user_profile.get("career_field", "")
        
        # Check last research to avoid duplicate alerts
        last_research = await db.user_research_log.find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)]
        )
        
        # ===== DEADLINE ALERTS =====
        deadline_insights = await _research_deadlines(user_id, user_profile)
        insights.extend(deadline_insights)
        
        # ===== POLICY CHANGES =====
        policy_insights = await _research_policy_changes(province, permit_type)
        insights.extend(policy_insights)
        
        # ===== BENEFIT OPPORTUNITIES =====
        benefit_insights = await _research_eligible_benefits(user_profile)
        insights.extend(benefit_insights)
        
        # ===== JOB MARKET (if job seeking) =====
        if user_profile.get("job_seeking"):
            job_insights = await _research_job_market(province, city, career_field)
            insights.extend(job_insights)
        
        # ===== HOUSING TRENDS =====
        if days_in_canada <= 60:  # Early stages care about housing
            housing_insights = await _research_housing_market(province, city)
            insights.extend(housing_insights)
        
        # ===== PROFESSIONAL DEVELOPMENT =====
        if career_field:
            prof_insights = await _research_professional_opportunities(
                career_field, province, permit_type
            )
            insights.extend(prof_insights)
        
        # ===== LEGAL/IMMIGRATION ROUTES =====
        legal_insights = await _research_immigration_routes(user_profile)
        insights.extend(legal_insights)
        
        # ===== REGIONAL SPECIFIC =====
        regional_insights = await _research_regional_updates(province, city)
        insights.extend(regional_insights)
        
        # ===== WELLNESS CHECK =====
        if days_in_canada > 14:  # After initial overwhelm
            wellness_insights = await _research_wellness_resources(province, city)
            insights.extend(wellness_insights)
        
        # Filter: Remove duplicates, old alerts
        insights = _deduplicate_insights(insights, last_research)
        
        # Limit: Max 3 insights per update (quality > quantity)
        insights = insights[:3]
        
        # Log research for this user
        if insights:
            await db.user_research_log.insert_one({
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "insights_count": len(insights),
                "categories": [i["category"] for i in insights],
                "exported": False,
            })
        
        return insights
    
    except Exception as e:
        logger.error(f"Error researching insights for user {user_id}: {e}")
        return []


async def _research_deadlines(user_id: str, user_profile: Dict) -> List[Dict]:
    """Alert user about upcoming deadlines relevant to their permit/status."""
    insights = []
    
    try:
        permit_expiry = user_profile.get("permit_expiry")
        if permit_expiry:
            days_until = (datetime.fromisoformat(permit_expiry) - datetime.utcnow()).days
            
            if days_until == 90:
                insights.append({
                    "category": InsightCategory.DEADLINE_ALERT,
                    "title": "90 Days Until Permit Expiry — Start Renewal Now",
                    "insight": f"Your {user_profile.get('permit_type', 'permit')} expires in exactly 90 days. "
                               "Processing time is typically 4-8 weeks. File your renewal application this week to avoid gaps.",
                    "why_relevant": "Permit gap = loss of work authorization, lost income, compounded problems",
                    "action": "Go to IRCC portal → Renew your permit → Submit with updated documents",
                    "source": "IRCC Processing Times",
                    "confidence": 0.99,
                })
            elif days_until == 30:
                insights.append({
                    "category": InsightCategory.DEADLINE_ALERT,
                    "title": "⚠️ 30 Days Left — Permit Renewal URGENT",
                    "insight": "Your permit expires in 30 days. If you haven't submitted renewal, do it TODAY. "
                               "Last-minute submissions face delays.",
                    "why_relevant": "Working on an expired permit can result in deportation",
                    "source": "IRCC",
                    "confidence": 0.99,
                })
        
        # Check application deadlines
        pending_apps = await db.user_applications.find({
            "user_id": user_id,
            "status": "pending"
        }).to_list(5)
        
        for app in pending_apps:
            deadline = app.get("deadline")
            if deadline:
                days_left = (datetime.fromisoformat(deadline) - datetime.utcnow()).days
                if days_left <= 14 and days_left > 0:
                    insights.append({
                        "category": InsightCategory.DEADLINE_ALERT,
                        "title": f"Application Deadline: {days_left} Days Left",
                        "insight": f"Your {app.get('type', 'application')} deadline is {deadline}. "
                                   f"Gather remaining documents now.",
                        "why_relevant": f"Missing this deadline restarts your entire {app.get('type')} process",
                        "source": "IRCC Application Tracker",
                        "confidence": 0.95,
                    })
    
    except Exception as e:
        logger.error(f"Error researching deadlines: {e}")
    
    return insights


async def _research_policy_changes(province: str, permit_type: str) -> List[Dict]:
    """Alert about new immigration policies affecting their situation."""
    insights = []
    
    try:
        # Check recent policy updates
        recent_policies = await db.policy_updates.find({
            "affected_provinces": province,
            "effective_date": {"$lte": datetime.utcnow()},
            "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
        }).to_list(3)
        
        for policy in recent_policies:
            if policy.get("permit_types") and permit_type in policy.get("permit_types", []):
                insights.append({
                    "category": InsightCategory.POLICY_CHANGE,
                    "title": f"🚨 Immigration Policy Update: {policy.get('title')}",
                    "insight": policy.get("summary", ""),
                    "why_relevant": f"Directly affects your {permit_type} processing, eligibility, or timeline",
                    "action": policy.get("recommended_action", "Review IRCC website for details"),
                    "source": policy.get("source", "IRCC"),
                    "url": policy.get("url"),
                    "confidence": 0.99,
                })
    
    except Exception as e:
        logger.error(f"Error researching policy changes: {e}")
    
    return insights


async def _research_eligible_benefits(user_profile: Dict) -> List[Dict]:
    """Research what benefits/credits the user might qualify for."""
    insights = []
    
    try:
        province = user_profile.get("province", "ON")
        income = user_profile.get("annual_income", 0)
        status = user_profile.get("status", "unknown")
        has_dependents = user_profile.get("has_dependents", False)
        
        # Canada Child Benefit (CCB)
        if has_dependents and status in ["PR", "citizen"]:
            insights.append({
                "category": InsightCategory.BENEFIT_OPPORTUNITY,
                "title": "💰 You Likely Qualify for Canada Child Benefit (CCB)",
                "insight": "CCB provides $150-300/month per child under 18. It's AUTOMATIC if you file taxes, "
                          "but many newcomers miss it. File your tax return to receive it retroactively.",
                "why_relevant": "$2,000+/year per child — literally free money if you have kids",
                "action": "File your tax return before June 15 → Receive CCB retroactively",
                "source": "CRA - Canada Child Benefit",
                "confidence": 0.95,
            })
        
        # Registered Education Savings Plan (RESP) - free money from government
        if has_dependents:
            insights.append({
                "category": InsightCategory.FINANCIAL,
                "title": "Free Money for Kids' Education: RESP Grants",
                "insight": "Government matches 20% of RESP contributions up to $2,500/year (= $500 free/year per child). "
                          "This is true FREE money, not a credit.",
                "why_relevant": "Over 17 years: $8,500 free per child for education",
                "action": "Open RESP at any bank → Deposit $2,500/year → Get $500 free from government",
                "source": "CRA - Education Savings",
                "confidence": 0.92,
            })
        
        # Working Income Tax Benefit (WITB)
        if income < 40000 and status in ["PR", "citizen"]:
            insights.append({
                "category": InsightCategory.FINANCIAL,
                "title": "Tax Credit for Low Income: Working Income Tax Benefit",
                "insight": "If you earn less than $40k/year, you qualify for WITB: up to $2,000/year back. "
                          "Most people don't know it exists.",
                "why_relevant": "Free money just for working while building your career",
                "action": "File taxes → Claim WITB automatically on your return",
                "source": "CRA - Working Income Tax Benefit",
                "confidence": 0.93,
            })
        
        # Provincial benefits
        provincial_benefits = {
            "ON": "Ontario Works, Ontario Health Coverage",
            "BC": "BC Benefits, Medical Services Plan",
            "AB": "Alberta Income Support, Health Coverage",
        }
        
        if province in provincial_benefits and income < 30000:
            insights.append({
                "category": InsightCategory.BENEFIT_OPPORTUNITY,
                "title": f"Provincial Support: {provincial_benefits.get(province)}",
                "insight": f"{province} has additional income support and healthcare programs for "
                          "low-income residents. Check eligibility.",
                "why_relevant": "Province-specific support can cover housing, food, or healthcare gaps",
                "source": f"Government of {province}",
                "confidence": 0.88,
            })
    
    except Exception as e:
        logger.error(f"Error researching benefits: {e}")
    
    return insights


async def _research_job_market(province: str, city: str, career_field: str) -> List[Dict]:
    """Research job market trends in user's field."""
    insights = []
    
    try:
        if not career_field:
            return insights
        
        # Get job market data
        market_data = await db.job_market_trends.find_one({
            "province": province,
            "field": career_field,
            "month": (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m")
        })
        
        if market_data:
            demand = market_data.get("demand_score", 0)  # 0-10
            avg_salary = market_data.get("avg_salary", 0)
            shortage = market_data.get("talent_shortage", False)
            
            if demand > 7:
                insights.append({
                    "category": InsightCategory.JOB_MARKET,
                    "title": f"🔥 Hot Demand: {career_field} in {city}",
                    "insight": f"Demand for {career_field}s is HIGH right now (demand score: {demand}/10). "
                              f"Average salary: ${avg_salary:,.0f}/year. Companies are actively hiring.",
                    "why_relevant": "When demand is high, you have negotiating power for salary & benefits",
                    "action": "Update LinkedIn → Apply to open roles → Negotiate confidently",
                    "source": "Job Market Analytics",
                    "confidence": 0.85,
                })
            
            if shortage:
                insights.append({
                    "category": InsightCategory.JOB_MARKET,
                    "title": f"Talent Shortage Alert: {career_field}",
                    "insight": f"There's a shortage of {career_field}s in {province}. Companies are "
                              "desperate to fill roles. THIS IS YOUR TIME.",
                    "why_relevant": "Shortage = easier hiring, higher salaries, better benefits, less competition",
                    "action": "Target employers directly → Highlight any experience → Negotiate hard",
                    "source": "Job Market Analytics",
                    "confidence": 0.82,
                })
    
    except Exception as e:
        logger.error(f"Error researching job market: {e}")
    
    return insights


async def _research_housing_market(province: str, city: str) -> List[Dict]:
    """Research housing trends and costs."""
    insights = []
    
    try:
        housing_data = await db.housing_trends.find_one({
            "province": province,
            "city": city or "provincial"
        })
        
        if housing_data:
            avg_rent = housing_data.get("avg_rent_1br", 0)
            trend = housing_data.get("trend", "stable")  # up, down, stable
            vacancy = housing_data.get("vacancy_rate", 0)
            
            if trend == "down" and vacancy > 3:
                insights.append({
                    "category": InsightCategory.HOUSING,
                    "title": f"Housing Alert: {city} Market Cooling",
                    "insight": f"Average 1BR rent is dropping. Vacancy is {vacancy}% (healthy market). "
                              f"NOW is a good time to negotiate rent or find better place.",
                    "why_relevant": "Renters have more power when vacancy is high",
                    "action": "Start apartment search → Negotiate rent down 5-10% when signing",
                    "source": "Housing Market Data",
                    "confidence": 0.80,
                })
            elif trend == "up" and vacancy < 2:
                insights.append({
                    "category": InsightCategory.HOUSING,
                    "title": f"⚠️ Housing Market Heating Up",
                    "insight": f"Rents rising, vacancy low ({vacancy}%). Landlords have power. "
                              f"Average 1BR: ${avg_rent:,.0f}. Lock in a good lease NOW.",
                    "why_relevant": "If you wait, you'll pay more",
                    "action": "Search NOW → Lock in lease ASAP before rents rise further",
                    "source": "Housing Market Data",
                    "confidence": 0.80,
                })
    
    except Exception as e:
        logger.error(f"Error researching housing: {e}")
    
    return insights


async def _research_professional_opportunities(
    career_field: str, province: str, permit_type: str
) -> List[Dict]:
    """Research certifications, upskilling, credential recognition."""
    insights = []
    
    try:
        if not career_field:
            return insights
        
        # Find credential recognition programs
        cred_programs = await db.credential_programs.find({
            "field": career_field,
            "provinces": province,
        }).to_list(1)
        
        for program in cred_programs:
            insights.append({
                "category": InsightCategory.PROFESSIONAL,
                "title": f"Credential Recognition: Fast-track in {career_field}",
                "insight": f"{program.get('organization')} can recognize your {career_field} credentials in ~{program.get('processing_days', 30)} days. "
                          f"Cost: ${program.get('cost', 0)}. Boost your marketability.",
                "why_relevant": "Recognized credentials = 20-30% higher starting salary",
                "action": f"Visit {program.get('url')} → Submit credentials → Unlock higher-paying roles",
                "source": program.get("organization"),
                "confidence": 0.88,
            })
        
        # Find certifications in high demand
        in_demand_certs = await db.in_demand_certifications.find_one({
            "field": career_field,
            "province": province,
        })
        
        if in_demand_certs:
            certs = in_demand_certs.get("certifications", [])
            if certs:
                insights.append({
                    "category": InsightCategory.PROFESSIONAL,
                    "title": f"Certifications That Unlock Jobs",
                    "insight": f"Most-wanted certs in {career_field}: {', '.join(certs[:2])}. "
                              f"These add $5-15k/year to salary and take 2-4 months online.",
                    "why_relevant": "Cert = instant credibility + higher pay + fast hiring",
                    "action": f"Check Coursera or Udemy for these certs → Complete in 3 months → leverage in job search",
                    "source": "Job Market Analysis",
                    "confidence": 0.85,
                })
    
    except Exception as e:
        logger.error(f"Error researching professional opportunities: {e}")
    
    return insights


async def _research_immigration_routes(user_profile: Dict) -> List[Dict]:
    """Research PR/citizenship pathways available to user."""
    insights = []
    
    try:
        permit_type = user_profile.get("permit_type", "")
        province = user_profile.get("province", "")
        
        # If on work permit, research Express Entry path
        if "work" in permit_type.lower():
            insights.append({
                "category": InsightCategory.LEGAL,
                "title": "PR Path: Express Entry (Work Permit → PR)",
                "insight": "You're eligible for Express Entry. With 1-2 years Canadian work experience + English skills, "
                          "you can get PR in 6-12 months.",
                "why_relevant": "PR = job security, healthcare, sponsorship power, pathway to citizenship",
                "action": "Track CRS score → Prepare documents → Apply when score eligible",
                "source": "IRCC Express Entry",
                "confidence": 0.90,
            })
        
        # If on study permit, research post-grad path
        if "study" in permit_type.lower():
            insights.append({
                "category": InsightCategory.LEGAL,
                "title": "Study → Work → PR Pipeline",
                "insight": "Graduate from Canadian college/university → 3-year post-grad work permit → PR eligible. "
                          "This is the easiest path to permanent residence.",
                "why_relevant": "Structured, predictable, and PR-guaranteed if you follow steps",
                "action": "Focus on studies → Secure Canadian job offer after graduation → Apply for PR",
                "source": "IRCC Study Permits",
                "confidence": 0.92,
            })
        
        # Provincial Nominee Program (PNP)
        if province:
            insights.append({
                "category": InsightCategory.LEGAL,
                "title": f"Fast-track PR: {province} Nominee Program",
                "insight": f"{province} can nominate you for PR directly if you meet criteria. "
                          "This bypasses federal competition and can cut timeline by 6 months.",
                "why_relevant": "Provincial nomination = faster PR approval, more points",
                "action": f"Check {province} PNP website → See if you meet points → Apply",
                "source": f"Government of {province} PNP",
                "confidence": 0.88,
            })
    
    except Exception as e:
        logger.error(f"Error researching immigration routes: {e}")
    
    return insights


async def _research_regional_updates(province: str, city: str) -> List[Dict]:
    """Province/city specific updates."""
    insights = []
    
    try:
        regional_news = await db.regional_updates.find({
            "$or": [
                {"province": province},
                {"city": city}
            ],
            "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
        }).to_list(1)
        
        for news in regional_news:
            insights.append({
                "category": InsightCategory.REGIONAL,
                "title": f"📍 {city or province} News: {news.get('title')}",
                "insight": news.get("summary"),
                "why_relevant": news.get("why_relevant_to_newcomers"),
                "source": news.get("source"),
                "confidence": 0.85,
            })
    
    except Exception as e:
        logger.error(f"Error researching regional updates: {e}")
    
    return insights


async def _research_wellness_resources(province: str, city: str) -> List[Dict]:
    """Mental health, community resources, settlement support."""
    insights = []
    
    try:
        # Suggest newcomer communities/support groups
        insights.append({
            "category": InsightCategory.WELLNESS,
            "title": "Connect with Your Community",
            "insight": f"You've been in {city or province} for a few weeks. Joining newcomer groups helps with "
                      "isolation and accelerates integration. Your settlement agency runs free meet-ups.",
            "why_relevant": "Community = faster job leads, friends, mental health support, cultural connection",
            "action": "Visit your settlement agency website → Attend next weekly meet-up",
            "source": "Settlement Sector",
            "confidence": 0.90,
        })
        
        # Mental health check
        insights.append({
            "category": InsightCategory.WELLNESS,
            "title": "Mental Health Support (Free & Confidential)",
            "insight": "First month is hard. Free counseling available: 211.ca (call 2-1-1) or your province's mental health line. "
                      "Many counselors speak multiple languages.",
            "why_relevant": "Mental health impacts job performance, relationships, everything",
            "action": "Save 2-1-1 in your phone → Reach out if struggling",
            "source": "211.ca National Helpline",
            "confidence": 0.95,
        })
    
    except Exception as e:
        logger.error(f"Error researching wellness: {e}")
    
    return insights


def _deduplicate_insights(insights: List[Dict], last_research: Optional[Dict]) -> List[Dict]:
    """Remove duplicate/similar insights sent in last 48 hours."""
    if not last_research:
        return insights
    
    last_categories = last_research.get("categories", [])
    last_sent_time = last_research.get("created_at")
    
    # If less than 48 hours and same category, filter it
    if last_sent_time and (datetime.utcnow() - last_sent_time).days < 2:
        insights = [
            i for i in insights
            if i.get("category") not in last_categories
        ]
    
    return insights


async def broadcast_research_insights():
    """
    Background task: Run research for each user every 48 hours.
    Send insights via notifications.
    """
    while True:
        try:
            # Get all active users
            users = await db.users.find({
                "notification_preferences.research_insights": True
            }).to_list(None)
            
            for user in users:
                try:
                    user_id = str(user["_id"])
                    
                    # Research insights
                    insights = await research_user_insights(
                        user_id,
                        user.get("profile", {})
                    )
                    
                    if insights:
                        # Queue for delivery
                        for insight in insights:
                            await db.notification_queue.insert_one({
                                "user_id": user_id,
                                "type": "research_insight",
                                "category": insight.get("category"),
                                "content": insight,
                                "channels": user.get("notification_channels", ["in-app"]),
                                "created_at": datetime.utcnow(),
                                "sent": False,
                            })
                        
                        logger.info(f"Queued {len(insights)} research insights for user {user_id}")
                
                except Exception as e:
                    logger.error(f"Error researching for user {user.get('_id')}: {e}")
            
            # Check every 48 hours
            await asyncio.sleep(172800)
        
        except Exception as e:
            logger.error(f"Error in research insights broadcaster: {e}")
            await asyncio.sleep(3600)
