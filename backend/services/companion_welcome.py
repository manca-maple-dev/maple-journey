"""Companion welcome message service.

When a user registers, Maple sends them a personalized welcome message
via WhatsApp/SMS so they can start chatting immediately without opening the app.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from core.db import db
from services.twilio_service import send_whatsapp, send_imessage, send_message_by_channel
from services.companion_memory import CompanionMemory

logger = logging.getLogger("maplejourney.companion_welcome")


async def send_welcome_message(user_id: str, phone: str = None) -> Dict[str, Any]:
    """Send personalized welcome message to new user.
    
    Args:
        user_id: User ID
        phone: Phone number (if not provided, fetched from user doc)
    
    Returns:
        {
            "ok": bool,
            "message_id": str,
            "channel": str,
            "sent_to": str
        }
    """
    try:
        # Fetch user
        user = await db.users.find_one({"_id": user_id})
        if not user:
            logger.warning(f"User {user_id} not found for welcome")
            return {"ok": False, "error": "User not found"}
        
        # Use provided phone or from user doc
        phone = (phone or user.get("phone", "")).strip()
        if not phone:
            logger.warning(f"No phone on file for user {user_id}")
            return {"ok": False, "error": "No phone number", "note": "User can enable WhatsApp/SMS later in settings"}
        
        # Normalize phone
        if not phone.startswith("+"):
            phone = "+" + phone
        
        # Generate personalized welcome message
        name = user.get("name", "there").split()[0]  # First name only
        country = user.get("country_of_origin", "")
        newcomer_type = user.get("newcomer_type", "").title()
        
        welcome_msg = f"""👋 **Welcome to Maple!** 🍁

Hi {name}! I'm Maple, your 24/7 immigration companion.

I'm here to help you navigate life in Canada with personalized guidance based on your situation:
• Country of origin: {country or 'TBD'}
• Immigration path: {newcomer_type or 'To be determined'}

**You can ask me about:**
✓ Work permits & renewals
✓ Study permits & extensions  
✓ PR eligibility & Express Entry
✓ Provincial Nominee Programs (PNP)
✓ Settlement services & resources
✓ Your rights & responsibilities
✓ Application timelines & processes

**Just reply here anytime** — no app needed, no charge for basic questions. I remember our conversation and get smarter about your situation over time.

**Get started:**
1. Tell me more about your immigration goal
2. Ask anything — I'll ground my answers in official sources
3. I'll proactively send updates if your situation changes

Questions? Reply or visit maplejourney.ca

Let's go! 🚀
— Maple"""
        
        # Create initial session for this user
        companion_memory = CompanionMemory(db)
        session = await companion_memory.get_or_create_session(
            str(user_id),
            channel="whatsapp"  # Default to WhatsApp first
        )
        session_id = session["session_id"]
        
        # Send via WhatsApp
        try:
            result = send_whatsapp(phone, welcome_msg)
            channel = "whatsapp"
            logger.info(f"Welcome message sent via WhatsApp to {user_id}")
        except Exception as e:
            logger.warning(f"WhatsApp send failed ({e}), trying SMS/iMessage...")
            try:
                result = send_imessage(phone, welcome_msg)
                channel = "imessage"
                logger.info(f"Welcome message sent via SMS/iMessage to {user_id}")
            except Exception as e2:
                logger.exception(f"Both WhatsApp and SMS failed for user {user_id}")
                return {"ok": False, "error": f"Failed to send via both channels: {str(e2)}"}
        
        # Mark welcome as sent in user doc
        await db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "companion_welcome_pending": False,
                    "companion_welcome_sent_at": datetime.now(timezone.utc).isoformat(),
                    "companion_welcome_channel": channel,
                    "enabled_channels": ["web", channel],
                }
            }
        )
        
        # Store the welcome message in companion session for context
        await companion_memory.add_turn(
            session_id=session_id,
            user_id=str(user_id),
            query="[SYSTEM] User registered",
            response=welcome_msg,
            retrieved_docs=[],
            model_used="maple-welcome",
            tokens_used=0,
        )
        
        return {
            "ok": True,
            "message_id": getattr(result, "sid", "unknown"),
            "channel": channel,
            "sent_to": phone,
            "session_id": session_id,
        }
    
    except Exception as e:
        logger.exception(f"Welcome message send error")
        return {"ok": False, "error": str(e)}


async def generate_personalized_welcome_text(user: Dict[str, Any]) -> str:
    """Generate welcome text based on user's profile.
    
    This is called to create a custom intro message.
    """
    name = user.get("name", "there").split()[0]
    country = user.get("country_of_origin", "")
    newcomer_type = user.get("newcomer_type", "")
    province = user.get("province", "")
    category = user.get("immigration_category", "")
    
    # Build profile summary
    profile_items = []
    if country:
        profile_items.append(f"from {country}")
    if newcomer_type:
        profile_items.append(f"as a {newcomer_type.lower()}")
    if province:
        profile_items.append(f"in {province}")
    if category:
        profile_items.append(f"interested in {category.replace('_', ' ').title()}")
    
    profile_text = ", ".join(profile_items) if profile_items else "interested in immigration to Canada"
    
    return f"""Hi {name}! 👋🍁

I'm Maple, your 24/7 immigration companion. You're {profile_text}, and I'm here to help.

Just text me questions anytime—I'll give you grounded, personalized answers based on your situation. No app needed!"""


async def check_welcome_needed(user_id: str) -> bool:
    """Check if welcome message still needs to be sent.
    
    Returns True if:
    - User is new (within last 5 minutes)
    - Welcome is marked as pending
    - User has a phone number
    """
    user = await db.users.find_one({"_id": user_id})
    if not user:
        return False
    
    # Check if welcome is pending and user has phone
    pending = user.get("companion_welcome_pending", True)
    has_phone = bool(user.get("phone", "").strip())
    
    # Skip if already sent or no phone
    if not pending or not has_phone:
        return False
    
    # Skip if already tried and failed too many times
    sent_at = user.get("companion_welcome_sent_at")
    if sent_at:
        return False
    
    return True
