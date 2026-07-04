"""Daily morning briefings & 30-day guided journey system.

Sends personalized notifications every morning with:
1. News & updates (IRCC, CRA, local)
2. Reminders (permits expiring, documents needed)
3. 30-day journey guidance (day-by-day prompts)
4. Action items & next steps

Scheduling: 8:00 AM user's local timezone
Integration: WhatsApp, SMS, Push notifications, email
"""
import asyncio
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
import logging
from enum import Enum

from core.db import db
from services.community_intelligence import get_official_211_resources
from services.research_agent import research_user_insights

logger = logging.getLogger("maplejourney.notifications")


class NotificationChannel(str, Enum):
    """Available notification delivery channels."""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    PUSH = "push"
    EMAIL = "email"
    IN_APP = "in-app"


class GuidedJourneyDay(dict):
    """Structure for 30-day journey prompts."""
    
    def __init__(self, day: int, title: str, action: str, maple_prompt: str, 
                 focus_area: str, checkpoint: Optional[str] = None):
        self.day = day
        self.title = title
        self.action = action
        self.maple_prompt = maple_prompt  # What Maple says to user
        self.focus_area = focus_area
        self.checkpoint = checkpoint
        super().__init__(
            day=day,
            title=title,
            action=action,
            maple_prompt=maple_prompt,
            focus_area=focus_area,
            checkpoint=checkpoint
        )


# ===== 30-DAY GUIDED JOURNEY =====
GUIDED_JOURNEY_30_DAYS = [
    # Week 1: Foundation
    GuidedJourneyDay(
        day=1,
        title="Welcome to MapleJourney!",
        action="Complete your profile",
        maple_prompt="Welcome to Canada! 🍁 I'm Maple, your AI companion. Let's start by understanding your journey. Can you tell me: What brings you to Canada (work, study, PR)? This helps me give you the most relevant guidance.",
        focus_area="onboarding",
        checkpoint="profile_started"
    ),
    GuidedJourneyDay(
        day=2,
        title="Your Immigration Status",
        action="Confirm your visa/permit type",
        maple_prompt="Great! Now let's clarify your current status. Are you on a work permit, study permit, visiting, or starting PR? This determines what benefits and next steps apply to you.",
        focus_area="status",
        checkpoint="status_confirmed"
    ),
    GuidedJourneyDay(
        day=3,
        title="Timeline Check",
        action="Set permit expiry reminder",
        maple_prompt="Let's make sure you don't miss deadlines. What's your permit expiry date? I'll track it and remind you 90 days before for renewal planning.",
        focus_area="timeline",
        checkpoint="expiry_date_set"
    ),
    GuidedJourneyDay(
        day=4,
        title="Find Your Community",
        action="Browse local resources",
        maple_prompt="You're not alone! I found settlement agencies, food banks, and community centers near you. Want to explore communities or settlement services?",
        focus_area="community",
        checkpoint="resources_viewed"
    ),
    GuidedJourneyDay(
        day=5,
        title="Language & Learning",
        action="Check ESL programs",
        maple_prompt="English/French skills open doors. There are government-funded free ESL programs near you. Interested? I can share details and application links.",
        focus_area="language",
        checkpoint="language_explored"
    ),
    GuidedJourneyDay(
        day=6,
        title="Healthcare Access",
        action="Register for provincial healthcare",
        maple_prompt="Your health matters. Most provinces provide free healthcare after a waiting period. Let's check: Have you registered for provincial health coverage? I'll guide the steps.",
        focus_area="health",
        checkpoint="healthcare_registered"
    ),
    GuidedJourneyDay(
        day=7,
        title="Week 1 Recap",
        action="Review progress",
        maple_prompt="🎉 Week 1 complete! You've set up your profile, confirmed your status, and discovered local resources. How are you feeling? Any questions about what's next?",
        focus_area="checkpoint",
        checkpoint="week1_complete"
    ),
    
    # Week 2: Essentials
    GuidedJourneyDay(
        day=8,
        title="Banking & Finances",
        action="Open a Canadian bank account",
        maple_prompt="A Canadian bank account is essential for work, rent, and building credit. Most banks welcome newcomers. Which province are you in? I can recommend options.",
        focus_area="financial",
        checkpoint="bank_research_started"
    ),
    GuidedJourneyDay(
        day=9,
        title="SIN & Taxes",
        action="Apply for Social Insurance Number",
        maple_prompt="You'll need a Social Insurance Number (SIN) for work and taxes. You can apply at Service Canada or online. Let's make sure you have one—have you applied yet?",
        focus_area="government-id",
        checkpoint="sin_status_checked"
    ),
    GuidedJourneyDay(
        day=10,
        title="Credential Recognition",
        action="Start credential assessment",
        maple_prompt="If you worked abroad, your credentials might be recognized here. This can boost your job prospects. What's your field? I can point you to recognition programs.",
        focus_area="employment",
        checkpoint="credential_research_started"
    ),
    GuidedJourneyDay(
        day=11,
        title="Job Search Prep",
        action="Update your resume for Canada",
        maple_prompt="Canadian resumes look different—chronological, no photo, 1-2 pages. I can suggest changes. Want to share your current resume, or should I explain the format?",
        focus_area="employment",
        checkpoint="resume_updated"
    ),
    GuidedJourneyDay(
        day=12,
        title="Finding Housing",
        action="Explore rental market",
        maple_prompt="Housing is often the biggest expense. Rent, utilities, and deposits vary by region. Where are you looking? I can help estimate costs and find resources.",
        focus_area="housing",
        checkpoint="housing_budget_set"
    ),
    GuidedJourneyDay(
        day=13,
        title="Transportation",
        action="Get transit pass/driver's license info",
        maple_prompt="Getting around: public transit is affordable in cities. For driving, you may need a provincial license or IDP. What's your transportation priority?",
        focus_area="settlement",
        checkpoint="transit_explored"
    ),
    GuidedJourneyDay(
        day=14,
        title="Week 2 Recap",
        action="Reflect on progress",
        maple_prompt="🎉 Halfway through week 2! You're setting up finances, exploring jobs, and finding housing. You're building real momentum. What's the biggest win so far?",
        focus_area="checkpoint",
        checkpoint="week2_complete"
    ),
    
    # Week 3: Growth
    GuidedJourneyDay(
        day=15,
        title="Networking",
        action="Join a professional group",
        maple_prompt="Connections matter in Canada. LinkedIn is huge here. Professional associations, meetups, and alumni groups are gold for jobs and friendships. Your field?",
        focus_area="professional",
        checkpoint="networking_started"
    ),
    GuidedJourneyDay(
        day=16,
        title="Benefit Exploration",
        action="Check if you qualify for benefits",
        maple_prompt="Did you know you might qualify for CPP, EI, child benefits, or tax credits? It depends on your status. Let me check what you might be eligible for.",
        focus_area="benefits",
        checkpoint="benefits_checked"
    ),
    GuidedJourneyDay(
        day=17,
        title="Family & Dependents",
        action="Explore family sponsorship (if applicable)",
        maple_prompt="Thinking about bringing family? PR holders can sponsor spouses and dependents. Want to understand the timeline and costs?",
        focus_area="family",
        checkpoint="family_plan_discussed"
    ),
    GuidedJourneyDay(
        day=18,
        title="PR Path",
        action="Understand pathway options",
        maple_prompt="Many people work toward permanent residence. Different programs (Express Entry, PNP, etc.) suit different profiles. Ready to explore your PR options?",
        focus_area="immigration",
        checkpoint="pr_pathway_explored"
    ),
    GuidedJourneyDay(
        day=19,
        title="Professional Development",
        action="Identify certification/upgrade needs",
        maple_prompt="Staying competitive: consider certifications, upgrading, or additional education. What would boost your career in Canada?",
        focus_area="professional",
        checkpoint="learning_plan_started"
    ),
    GuidedJourneyDay(
        day=20,
        title="Wellness Check",
        action="Mental health & community",
        maple_prompt="The first month is intense. How's your mental health? Canada has free counseling and support groups. Don't hesitate to reach out. 🧠",
        focus_area="mental-health",
        checkpoint="wellness_resources_viewed"
    ),
    GuidedJourneyDay(
        day=21,
        title="Week 3 Recap",
        action="Plan next chapter",
        maple_prompt="🎉 Three weeks in! You're networking, exploring benefits, and thinking long-term. You're not just arriving—you're integrating. Proud of you!",
        focus_area="checkpoint",
        checkpoint="week3_complete"
    ),
    
    # Week 4: Mastery
    GuidedJourneyDay(
        day=22,
        title="Financial Planning",
        action="Build 3-month emergency fund goal",
        maple_prompt="Smart move: saving. A 3-month emergency fund is the Canadian financial safety net. Let's plan how to build this while covering rent/food.",
        focus_area="financial",
        checkpoint="savings_goal_set"
    ),
    GuidedJourneyDay(
        day=23,
        title="Tax & CRA",
        action="Understand tax filing",
        maple_prompt="Tax season: you may need to file even if no income. Why? To qualify for benefits like CCB. Filing deadline is June 15. Want guidance?",
        focus_area="government",
        checkpoint="tax_planning_started"
    ),
    GuidedJourneyDay(
        day=24,
        title="Credit Building",
        action="Start Canadian credit history",
        maple_prompt="Canadian credit score is crucial for mortgages, rentals, and loans. Get a credit card, use it responsibly, and watch your score grow!",
        focus_area="financial",
        checkpoint="credit_research_started"
    ),
    GuidedJourneyDay(
        day=25,
        title="Housing Upgrade",
        action="Execute housing plans",
        maple_prompt="Ready to move? Or stay put? Either way, understanding rental laws, lease terms, and tenant rights protects you. Want a quick rundown?",
        focus_area="housing",
        checkpoint="housing_decision_made"
    ),
    GuidedJourneyDay(
        day=26,
        title="Job Target",
        action="Define 90-day employment goal",
        maple_prompt="Most newcomers land jobs within 90 days. Let's set your target: industry, salary range, timeline. What's realistic for your situation?",
        focus_area="employment",
        checkpoint="job_goal_set"
    ),
    GuidedJourneyDay(
        day=27,
        title="Cultural Integration",
        action="Plan cultural & social activities",
        maple_prompt="Canada's diverse! Festivals, sports, potlucks, volunteer opportunities. Joining communities combats isolation and accelerates integration. Interested?",
        focus_area="cultural",
        checkpoint="cultural_activities_planned"
    ),
    GuidedJourneyDay(
        day=28,
        title="Visa/Permit Confidence",
        action="Confirm you understand your status",
        maple_prompt="By now, you should understand your permit type, restrictions, renewal timeline, and pathways. Confidence check: clear on everything, or any lingering questions?",
        focus_area="status",
        checkpoint="status_confidence_checked"
    ),
    GuidedJourneyDay(
        day=29,
        title="30-Day Reflection",
        action="Celebrate & look ahead",
        maple_prompt="30 days! You've gone from arrival to integration. You have a bank account, discovered resources, understand your timeline, and have a plan. 🎉",
        focus_area="checkpoint",
        checkpoint="day30_celebration"
    ),
    GuidedJourneyDay(
        day=30,
        title="Your Next Chapter",
        action="Plan your next 90 days",
        maple_prompt="Month 1 is about foundation. Months 2-3 are about execution: job, housing, community. Want to set goals for the next phase? I'll track your progress!",
        focus_area="planning",
        checkpoint="month2_planning_started"
    ),
]


async def get_morning_briefing(user_id: str, user_profile: Dict) -> Dict:
    """
    Generate morning briefing for user at 8:00 AM local time.
    
    Returns: {
        headlines: List[str],
        reminders: List[str],
        journey_prompt: Optional[str],
        actions: List[str],
        timestamp: datetime
    }
    """
    now = datetime.utcnow()
    briefing = {
        "headlines": [],
        "reminders": [],
        "journey_prompt": None,
        "actions": [],
        "timestamp": now.isoformat(),
    }
    
    # Get user profile info
    province = user_profile.get("province", "ON")
    days_since_arrival = (now - datetime.fromisoformat(user_profile.get("arrival_date", now.isoformat()))).days
    permit_type = user_profile.get("permit_type", "unknown")
    
    # ===== NEWS & HEADLINES =====
    try:
        # Fetch latest IRCC updates
        ircc_updates = await db.news_updates.find({
            "source": "ircc",
            "created_at": {"$gte": now - timedelta(days=1)}
        }).to_list(3)
        
        for update in ircc_updates:
            briefing["headlines"].append(f"📰 {update['title']}: {update['summary'][:100]}")
    except Exception as e:
        logger.error(f"Failed to fetch IRCC updates: {e}")
        briefing["headlines"].append("📰 Check IRCC website for latest immigration updates")
    
    # ===== REMINDERS =====
    try:
        # Check permit expiry
        expiry_date = user_profile.get("permit_expiry")
        if expiry_date:
            days_until_expiry = (datetime.fromisoformat(expiry_date) - now).days
            if days_until_expiry <= 90 and days_until_expiry > 0:
                briefing["reminders"].append(f"⚠️ Your {permit_type} expires in {days_until_expiry} days. Renew soon!")
        
        # Check for incomplete onboarding
        if not user_profile.get("profile_completed"):
            briefing["reminders"].append("📝 Complete your profile to get personalized recommendations")
        
        # Check for missing documents
        missing_docs = user_profile.get("missing_documents", [])
        if missing_docs:
            briefing["reminders"].append(f"📄 Document needed: {missing_docs[0]}")
    except Exception as e:
        logger.error(f"Failed to generate reminders: {e}")
    
    # ===== 30-DAY GUIDED JOURNEY =====
    if days_since_arrival <= 30:
        journey_index = min(days_since_arrival, 29)  # Cap at day 30
        journey_day = GUIDED_JOURNEY_30_DAYS[journey_index]
        
        briefing["journey_prompt"] = {
            "day": journey_day["day"],
            "title": journey_day["title"],
            "maple_says": journey_day["maple_prompt"],
            "action_for_today": journey_day["action"],
            "focus_area": journey_day["focus_area"],
        }
    
    # ===== RESEARCH INSIGHTS (Maple Agent) =====
    try:
        research_insights = await research_user_insights(user_id, user_profile)
        briefing["research_insights"] = research_insights[:2]  # Top 2 insights
    except Exception as e:
        logger.error(f"Failed to fetch research insights: {e}")
        briefing["research_insights"] = []
    
    # ===== ACTION ITEMS =====
    briefing["actions"] = [
        "Check weather & transit delays" if province in ["ON", "BC"] else "Have a productive day!",
        "Review any new government updates",
        "Make progress on today's action item",
    ]
    
    return briefing


async def schedule_morning_notifications():
    """
    Background task: Check every user's timezone, send 8 AM briefing.
    
    Runs continuously. Checks every hour for users in their 8 AM window.
    """
    while True:
        try:
            now = datetime.utcnow()
            
            # Find all users and check their local 8 AM time
            users = await db.users.find({"notification_preferences.morning_briefing": True}).to_list(None)
            
            for user in users:
                try:
                    tz = user.get("timezone", "America/Toronto")  # Default to Toronto
                    # Calculate if it's 8 AM in their timezone
                    # (Simplified: just check if last_briefing_sent is more than 24 hours old)
                    
                    last_sent = user.get("last_briefing_sent")
                    if not last_sent or (now - datetime.fromisoformat(last_sent)).days >= 1:
                        # Send briefing
                        briefing = await get_morning_briefing(
                            str(user["_id"]),
                            user.get("profile", {})
                        )
                        
                        # Queue notification for delivery
                        await db.notification_queue.insert_one({
                            "user_id": str(user["_id"]),
                            "type": "morning_briefing",
                            "content": briefing,
                            "channels": user.get("notification_channels", ["in-app"]),
                            "created_at": now,
                            "sent": False,
                        })
                        
                        # Update last_briefing_sent
                        await db.users.update_one(
                            {"_id": user["_id"]},
                            {"$set": {"last_briefing_sent": now.isoformat()}}
                        )
                        
                        logger.info(f"Morning briefing queued for user {user['_id']}")
                
                except Exception as e:
                    logger.error(f"Error processing user {user.get('_id')}: {e}")
            
            # Check every hour
            await asyncio.sleep(3600)
        
        except Exception as e:
            logger.error(f"Error in morning notification scheduler: {e}")
            await asyncio.sleep(60)


def get_user_journey_day(days_since_arrival: int) -> Optional[GuidedJourneyDay]:
    """Get current guided journey day for user (if within 30 days)."""
    if 0 <= days_since_arrival < len(GUIDED_JOURNEY_30_DAYS):
        return GUIDED_JOURNEY_30_DAYS[days_since_arrival]
    return None
