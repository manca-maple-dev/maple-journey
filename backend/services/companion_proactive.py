"""Phase 3+: Proactive Companion Actions

Like Wingman, send alerts, reminders, and daily briefings WITHOUT waiting for user messages.
Enables:
- Daily immigration news briefing (WhatsApp)
- Work permit renewal reminders (calendar-aware)
- New job matches alerts (from jobs/search)
- Community event notifications
- Status check-ins ("How's the application going?")
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
import anthropic

from core.db import db
from core.config import SYSTEM_PROMPT
from services.rag_v2 import rag_search_v2
from services.companion_memory import CompanionMemory
from services.twilio_service import send_whatsapp

logger = logging.getLogger("maplejourney.companion_proactive")


class CompanionProactiveActions:
    """Send unsolicited but valuable messages to users."""
    
    def __init__(self, db_conn):
        self.db = db_conn
        self.memory = CompanionMemory(db_conn)
        self.proactive_coll = db_conn.proactive_actions
    
    async def ensure_indexes(self):
        """Create indexes for proactive action tracking."""
        await self.proactive_coll.create_index("user_id")
        await self.proactive_coll.create_index("action_type")  # daily_brief, renewal_reminder, job_alert, etc.
        await self.proactive_coll.create_index("next_trigger_at")
        await self.proactive_coll.create_index("enabled")
    
    async def send_daily_briefing(self, user_id: str, phone: str) -> Dict[str, Any]:
        """Send personalized daily immigration news summary at 8 AM user time.
        
        Returns:
            { success, message_id, topics_count, sent_at }
        """
        logger.info(f"Sending daily briefing to user {user_id}")
        
        try:
            # Fetch user profile
            user = await self.db.users.find_one({"_id": user_id})
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Build personalized query based on user's immigration category
            category = user.get("immigration_category", "express_entry")
            province = user.get("province", "Ontario")
            
            query = f"Latest immigration news and updates for {category} in {province}"
            
            # RAG search with temporal boost
            retrieved_docs, score = await rag_search_v2(
                query,
                {"category": category, "province": province}
            )
            
            # Summarize using Claude
            client = anthropic.Anthropic()
            
            briefing_prompt = f"""You are Maple, a helpful immigration assistant. Create a SHORT 2-3 sentence daily briefing 
for a newcomer interested in {category} in {province}.

Key updates today:
{chr(10).join([f"- {doc['title']}" for doc in retrieved_docs[:3]])}

Format:
- Lead with the most important news
- Keep it scannable (WhatsApp friendly)
- End with "Need details? Just ask!"
            """
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": briefing_prompt}]
            )
            
            briefing_text = response.content[0].text
            
            # Send via WhatsApp
            await send_whatsapp(phone, f"📰 Daily Briefing\n\n{briefing_text}")
            
            # Log action
            await self.proactive_coll.insert_one({
                "_id": str(uuid4()),
                "user_id": user_id,
                "action_type": "daily_briefing",
                "triggered_at": datetime.now(timezone.utc),
                "next_trigger_at": (datetime.now(timezone.utc) + timedelta(days=1)),
                "status": "sent",
                "docs_used": len(retrieved_docs),
            })
            
            return {
                "success": True,
                "message_id": str(uuid4()),
                "topics_count": len(retrieved_docs),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        
        except Exception as e:
            logger.exception("Daily briefing error")
            return {"success": False, "error": str(e)}
    
    async def send_renewal_reminder(self, user_id: str, phone: str) -> Dict[str, Any]:
        """Send work permit / study permit / visitor record expiry reminder.
        
        Returns:
            { success, document_type, days_remaining, sent_at }
        """
        logger.info(f"Sending renewal reminder to user {user_id}")
        
        try:
            user = await self.db.users.find_one({"_id": user_id})
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Check document expiry dates
            work_permit_expiry = user.get("work_permit_expiry")
            study_permit_expiry = user.get("study_permit_expiry")
            visitor_record_expiry = user.get("visitor_record_expiry")
            
            now = datetime.now(timezone.utc)
            alerts = []
            
            # Work permit expiry in 30, 60, 90 days
            if work_permit_expiry:
                expiry_dt = datetime.fromisoformat(work_permit_expiry)
                days_left = (expiry_dt - now).days
                if 0 < days_left <= 90:
                    alerts.append(("Work Permit", days_left))
            
            if study_permit_expiry:
                expiry_dt = datetime.fromisoformat(study_permit_expiry)
                days_left = (expiry_dt - now).days
                if 0 < days_left <= 90:
                    alerts.append(("Study Permit", days_left))
            
            if visitor_record_expiry:
                expiry_dt = datetime.fromisoformat(visitor_record_expiry)
                days_left = (expiry_dt - now).days
                if 0 < days_left <= 90:
                    alerts.append(("Visitor Record", days_left))
            
            if not alerts:
                return {"success": False, "reason": "No documents expiring soon"}
            
            # Build message
            msg_lines = ["⏰ Expiry Reminders:\n"]
            for doc_type, days in alerts:
                msg_lines.append(f"• {doc_type}: {days} days left")
            
            msg_lines.append("\n🔗 Start renewal: https://maplejourney.ca/app/chat")
            
            message = "\n".join(msg_lines)
            await send_whatsapp(phone, message)
            
            # Log
            for doc_type, days in alerts:
                await self.proactive_coll.insert_one({
                    "_id": str(uuid4()),
                    "user_id": user_id,
                    "action_type": "renewal_reminder",
                    "document_type": doc_type,
                    "days_remaining": days,
                    "triggered_at": datetime.now(timezone.utc),
                    "next_trigger_at": (datetime.now(timezone.utc) + timedelta(days=7)),
                    "status": "sent",
                })
            
            return {
                "success": True,
                "alerts": alerts,
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        
        except Exception as e:
            logger.exception("Renewal reminder error")
            return {"success": False, "error": str(e)}
    
    async def send_job_alert(self, user_id: str, phone: str) -> Dict[str, Any]:
        """Send new job matches based on user's profile preferences.
        
        Returns:
            { success, jobs_count, sent_at }
        """
        logger.info(f"Sending job alert to user {user_id}")
        
        try:
            user = await self.db.users.find_one({"_id": user_id})
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get user's saved job preferences
            prefs = user.get("job_alert_prefs", {})
            if not prefs.get("enabled"):
                return {"success": False, "reason": "User disabled job alerts"}
            
            location = prefs.get("location", user.get("province"))
            category = prefs.get("job_category", "")
            
            # Search jobs
            job_docs = await self.db.jobs.find({
                "location": {"$regex": location, "$options": "i"},
                "posted_at": {"$gt": datetime.now(timezone.utc) - timedelta(days=3)},
            }).limit(3).to_list(None)
            
            if not job_docs:
                return {"success": False, "reason": "No new jobs matching preferences"}
            
            # Format message
            msg_lines = [f"💼 {len(job_docs)} New Jobs in {location}\n"]
            for job in job_docs:
                msg_lines.append(f"• {job.get('title', 'Job')}")
                msg_lines.append(f"  {job.get('company')}")
            
            msg_lines.append("\n👉 View all: https://maplejourney.ca/app/jobs")
            
            message = "\n".join(msg_lines)
            await send_whatsapp(phone, message)
            
            # Log
            await self.proactive_coll.insert_one({
                "_id": str(uuid4()),
                "user_id": user_id,
                "action_type": "job_alert",
                "jobs_count": len(job_docs),
                "triggered_at": datetime.now(timezone.utc),
                "next_trigger_at": (datetime.now(timezone.utc) + timedelta(days=1)),
                "status": "sent",
            })
            
            return {
                "success": True,
                "jobs_count": len(job_docs),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        
        except Exception as e:
            logger.exception("Job alert error")
            return {"success": False, "error": str(e)}
    
    async def send_status_checkin(self, user_id: str, phone: str) -> Dict[str, Any]:
        """Send friendly check-in: "How's your application going?"
        
        Returns:
            { success, message_id, sent_at }
        """
        logger.info(f"Sending status check-in to user {user_id}")
        
        try:
            user = await self.db.users.find_one({"_id": user_id})
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get recent session info
            recent_session = await self.db.companion_sessions.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            
            if recent_session:
                last_query = recent_session.get("last_query", "")
                msg = f"👋 Hi! Following up on your question about {last_query[:30]}...\n\n"
                msg += "Any other questions? Just reply here!"
            else:
                msg = "👋 Hi! Haven't heard from you in a bit.\n\n"
                msg += "How's your immigration journey going? Need help with anything?"
            
            await send_whatsapp(phone, msg)
            
            # Log
            await self.proactive_coll.insert_one({
                "_id": str(uuid4()),
                "user_id": user_id,
                "action_type": "status_checkin",
                "triggered_at": datetime.now(timezone.utc),
                "next_trigger_at": (datetime.now(timezone.utc) + timedelta(days=7)),
                "status": "sent",
            })
            
            return {
                "success": True,
                "message_id": str(uuid4()),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }
        
        except Exception as e:
            logger.exception("Status check-in error")
            return {"success": False, "error": str(e)}
