"""
Memory Layer Service — User-controlled fact management
Allows users to view, edit, delete, and organize facts Maple remembers about them
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("maple.memory_layer")


class MemoryCategory(str, Enum):
    PERSONAL = "personal"  # Name, family, background
    VISA_STATUS = "visa_status"  # Current visa, expiry, plans
    GOALS = "goals"  # PR, citizenship, job, education
    CONSTRAINTS = "constraints"  # Budget, skills, health, language
    PREFERENCES = "preferences"  # Communication style, location, pace
    DEADLINES = "deadlines"  # Important dates they're tracking
    OUTCOMES = "outcomes"  # Past successful queries, resolutions
    CONTEXT = "context"  # Broader life situation


class MemoryConfidence(str, Enum):
    CERTAIN = "certain"  # Explicitly stated by user
    HIGH = "high"  # Inferred from multiple messages
    MEDIUM = "medium"  # Single message reference
    LOW = "low"  # Uncertain reference


class MemoryLayerService:
    """
    Manages companion memory — facts Maple learns and remembers about users.
    Users have full transparency and control over their memory.
    """

    async def get_user_memory(
        self,
        user_id: str,
        category: Optional[MemoryCategory] = None,
        db=None,
    ) -> List[Dict]:
        """
        Retrieve all facts Maple has learned about the user.
        """
        if db is None:
            return []

        try:
            query = {"user_id": str(user_id)}
            if category:
                query["category"] = category.value

            memories = await db.companion_memory.find(query).sort(
                "last_referenced", -1
            ).to_list(100)

            return memories
        except Exception as e:
            logger.error(f"Failed to retrieve user memory: {e}")
            return []

    async def add_memory_fact(
        self,
        user_id: str,
        fact: str,
        category: MemoryCategory,
        confidence: MemoryConfidence = MemoryConfidence.HIGH,
        source_message_id: Optional[str] = None,
        db=None,
    ) -> Dict:
        """
        Store a new fact about the user.
        """
        if db is None:
            return {}

        try:
            memory_doc = {
                "user_id": str(user_id),
                "fact": fact,
                "category": category.value,
                "confidence": confidence.value,
                "source_message_id": source_message_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_referenced": datetime.now(timezone.utc).isoformat(),
                "reference_count": 1,
                "user_verified": False,  # User hasn't verified this yet
            }

            result = await db.companion_memory.insert_one(memory_doc)

            memory_doc["_id"] = result.inserted_id
            logger.info(f"Memory fact added: user={user_id} fact={fact[:50]}")

            return memory_doc
        except Exception as e:
            logger.error(f"Failed to add memory fact: {e}")
            return {}

    async def update_memory_fact(
        self,
        memory_id: str,
        updates: Dict,
        db=None,
    ) -> bool:
        """
        Update an existing memory fact (e.g., mark as verified by user).
        """
        if db is None:
            return False

        try:
            updates["last_updated"] = datetime.now(timezone.utc).isoformat()

            result = await db.companion_memory.update_one(
                {"_id": memory_id},
                {"$set": updates},
            )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update memory fact: {e}")
            return False

    async def delete_memory_fact(
        self,
        memory_id: str,
        db=None,
    ) -> bool:
        """
        Delete a memory fact (user didn't want Maple to remember this).
        """
        if db is None:
            return False

        try:
            result = await db.companion_memory.delete_one({"_id": memory_id})
            logger.info(f"Memory fact deleted: {memory_id}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete memory fact: {e}")
            return False

    async def verify_memory_fact(
        self,
        memory_id: str,
        verified: bool,
        db=None,
    ) -> bool:
        """
        User verifies or disputes a memory fact.
        """
        if db is None:
            return False

        try:
            result = await db.companion_memory.update_one(
                {"_id": memory_id},
                {
                    "$set": {
                        "user_verified": verified,
                        "verified_at": datetime.now(timezone.utc).isoformat(),
                    }
                },
            )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to verify memory fact: {e}")
            return False

    async def get_memory_summary(self, user_id: str, db=None) -> Dict:
        """
        Get summary of user's memory profile (quick facts).
        """
        if db is None:
            return {}

        try:
            memories = await db.companion_memory.find({"user_id": str(user_id)}).to_list(1000)

            # Group by category
            summary = {}
            for category in MemoryCategory:
                facts = [m for m in memories if m["category"] == category.value]
                # Convert ObjectId to string in each fact
                for f in facts:
                    if "_id" in f:
                        f["_id"] = str(f["_id"])
                summary[category.value] = {
                    "count": len(facts),
                    "facts": facts[:5],  # Top 5 facts per category
                    "verified_count": len([f for f in facts if f.get("user_verified")]),
                }

            return summary
        except Exception as e:
            logger.error(f"Failed to get memory summary: {e}")
            return {}

    async def extract_system_memory_context(
        self,
        user_id: str,
        db=None,
    ) -> str:
        """
        Generate a compact memory context string for LLM system prompt.
        Example: "User: Indian national, 28, currently on Work Permit expires Dec 2024, 
                  targeting PR by 2025, interested in tech jobs in Toronto"
        """
        if db is None:
            return ""

        try:
            memories = await self.get_user_memory(user_id, db=db)

            # Filter to verified + high-confidence facts
            verified_memories = [
                m for m in memories
                if m.get("user_verified") or m.get("confidence") == "high"
            ]

            # Build context string by category
            context_parts = []
            for category in [
                MemoryCategory.PERSONAL,
                MemoryCategory.VISA_STATUS,
                MemoryCategory.GOALS,
                MemoryCategory.CONSTRAINTS,
            ]:
                facts = [
                    m["fact"] for m in verified_memories
                    if m["category"] == category.value
                ]
                if facts:
                    context_parts.append(f"{category.value}: {', '.join(facts[:3])}")

            return "\n".join(context_parts)
        except Exception as e:
            logger.error(f"Failed to extract memory context: {e}")
            return ""


memory_service = MemoryLayerService()
