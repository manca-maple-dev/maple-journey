"""
Proactive Triggers Scheduler — Background job that surfaces deadlines in chat.
Runs every 6 hours. Checks user deadlines and injects into next chat response.
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger("maple.proactive_scheduler")


class ProactiveTriggerScheduler:
    """
    Background scheduler that:
    1. Evaluates all users for upcoming deadlines
    2. Marks which ones should be surfaced next time user chats
    3. Injects deadline alerts naturally into chat responses
    """

    def __init__(self, db):
        self.db = db
        self.running = False

    async def start(self):
        """Start background scheduler."""
        self.running = True
        logger.info("Proactive scheduler started")
        # Will be called by FastAPI startup event
        asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        """Stop background scheduler."""
        self.running = False
        logger.info("Proactive scheduler stopped")

    async def _scheduler_loop(self):
        """Run every 6 hours."""
        while self.running:
            try:
                await self.evaluate_all_users()
                # Sleep 6 hours
                await asyncio.sleep(6 * 3600)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)  # Retry after 1 min

    async def evaluate_all_users(self):
        """Scan all users for upcoming deadlines."""
        from services.deadline_engine import deadline_engine

        try:
            users = await self.db.users.find({}).to_list(10000)
            logger.info(f"Evaluating {len(users)} users for deadlines")

            for user in users:
                try:
                    triggers = await deadline_engine.evaluate_user(user)
                    
                    if triggers:
                        # Store in user_deadlines collection
                        await self.db.user_deadlines.update_one(
                            {"user_id": str(user["_id"])},
                            {
                                "$set": {
                                    "user_id": str(user["_id"]),
                                    "triggers": [t.to_dict() for t in triggers],
                                    "last_evaluated": datetime.now(timezone.utc).isoformat(),
                                    "pending_count": len([t for t in triggers if not t.surfaced_in_chat]),
                                }
                            },
                            upsert=True,
                        )
                        
                        logger.debug(f"user_id={user['_id']} found {len(triggers)} deadlines")
                except Exception as e:
                    logger.warning(f"Error evaluating user {user['_id']}: {e}")

        except Exception as e:
            logger.error(f"Failed to evaluate all users: {e}")

    async def get_next_alert_for_user(self, user_id: str) -> Optional[str]:
        """
        Get the next alert to surface for this user.
        Returns the chat message if one exists.
        Marks it as surfaced so it won't be repeated.
        """
        deadlines_doc = await self.db.user_deadlines.find_one({"user_id": str(user_id)})
        
        if not deadlines_doc or not deadlines_doc.get("triggers"):
            return None

        triggers = deadlines_doc.get("triggers", [])
        
        # Find unsurfaced, critical/urgent deadlines
        for trigger_dict in triggers:
            if trigger_dict.get("surfaced_in_chat"):
                continue

            # Reconstruct trigger object
            from services.deadline_engine import DeadlineTrigger, DeadlineType
            
            try:
                trigger = DeadlineTrigger(
                    user_id=trigger_dict["user_id"],
                    deadline_type=DeadlineType(trigger_dict["deadline_type"]),
                    due_date=datetime.fromisoformat(trigger_dict["due_date"]),
                    description=trigger_dict["description"],
                    context=trigger_dict.get("context", {}),
                )
                
                # Only surface critical/urgent in next chat
                if trigger.severity().value in ["critical", "urgent"]:
                    # Mark as surfaced
                    await self.db.user_deadlines.update_one(
                        {"user_id": str(user_id), "triggers.deadline_type": trigger.deadline_type.value},
                        {"$set": {"triggers.$.surfaced_in_chat": True}},
                    )
                    
                    return trigger.chat_message()
            except Exception as e:
                logger.warning(f"Error reconstructing trigger: {e}")

        return None

    async def inject_into_system_prompt(self, user_id: str, base_system_prompt: str) -> str:
        """
        Inject proactive deadline alert into the system prompt.
        So Maple naturally brings it up at the start of the conversation.
        """
        alert = await self.get_next_alert_for_user(user_id)
        
        if not alert:
            return base_system_prompt

        injection = (
            f"\n\n⚠️ PROACTIVE ALERT FOR THIS USER:\n"
            f"{alert}\n"
            f"Bring this up naturally at the start of the conversation if it seems relevant. "
            f"If the user is asking about something completely different, wait for them to finish "
            f"before introducing this deadline.\n"
        )
        
        return base_system_prompt + injection


proactive_scheduler: Optional[ProactiveTriggerScheduler] = None


def initialize_scheduler(db):
    """Called on app startup."""
    global proactive_scheduler
    proactive_scheduler = ProactiveTriggerScheduler(db)
    asyncio.create_task(proactive_scheduler.start())
    logger.info("Proactive scheduler initialized")


async def get_scheduler() -> Optional[ProactiveTriggerScheduler]:
    """Get the scheduler instance."""
    return proactive_scheduler
