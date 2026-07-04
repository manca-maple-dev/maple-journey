"""
Government Policy Feed Engine — Monitors & surfaces policy changes
Tracks: Immigration policy, funding caps, processing times, eligibility criteria
Integrates: IRCC official feeds, provincial regulations, bilateral agreements
"""
import logging
import re
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger("maple.policy_feed")


class PolicyCategory(str, Enum):
    IMMIGRATION_LEVEL = "immigration_level"
    VISA_ELIGIBILITY = "visa_eligibility"
    PROCESSING_TIME = "processing_time"
    FUNDING_CAP = "funding_cap"
    PATHWAY_CHANGE = "pathway_change"
    EXPIRY_DATE = "expiry_date"
    FEE_CHANGE = "fee_change"
    DOCUMENT_REQUIREMENT = "document_requirement"


class PolicySeverity(str, Enum):
    CRITICAL = "critical"  # Affects user immediately
    HIGH = "high"  # Significant change coming
    MEDIUM = "medium"  # Should monitor
    LOW = "low"  # FYI


@dataclass
class PolicyAlert:
    id: str
    category: PolicyCategory
    title: str
    summary: str
    effective_date: str
    severity: PolicySeverity
    affected_pathways: List[str]
    source_url: str
    last_checked: str


class GovernmentPolicyEngine:
    """
    Tracks government policy changes and surfaces them to affected users.
    Example: "TR-to-PR cap dropped to 30k" → surface to all Open Work Permit holders
    """

    def __init__(self):
        self.policy_categories = PolicyCategory
        self.severity_levels = PolicySeverity

    async def fetch_policy_updates(self, db=None) -> List[PolicyAlert]:
        """
        Fetch latest policy updates from monitored sources.
        In production: IRCC RSS, provincial ministry sites, Orders-in-Council
        """
        if db is None:
            return []

        try:
            # Query recent policy updates (last 7 days)
            updates = await db.policy_updates.find({
                "last_checked": {
                    "$gte": datetime.now(timezone.utc).isoformat()
                }
            }).sort("effective_date", -1).to_list(50)

            return updates
        except Exception as e:
            logger.error(f"Failed to fetch policy updates: {e}")
            return []

    async def get_relevant_policies(
        self,
        user_profile: Dict,
        db=None,
    ) -> List[PolicyAlert]:
        """
        Return policies relevant to user's current pathway and plans.
        """
        if db is None:
            return []

        try:
            # Get user's pathways
            current_visa = user_profile.get("current_visa_type")
            target_pathway = user_profile.get("target_pathway")  # "PR", "citizenship"
            country = user_profile.get("country_of_residence", "canada")
            province = user_profile.get("province", "ON")

            # Build query for relevant policies
            query = {
                "country": country,
                "$or": [
                    {"affected_pathways": current_visa},
                    {"affected_pathways": target_pathway},
                ]
            }

            # Add province-specific policies
            if province:
                query["$or"].append({"province": province})

            policies = await db.policy_updates.find(query).sort(
                "severity_weight", -1
            ).to_list(10)

            return policies
        except Exception as e:
            logger.error(f"Failed to get relevant policies: {e}")
            return []

    async def surface_urgent_policies(self, user_id: str, db=None) -> List[PolicyAlert]:
        """
        Get CRITICAL and HIGH severity policies that need immediate user attention.
        """
        if db is None:
            return []

        try:
            user = await db.users.find_one({"_id": user_id})
            if not user:
                return []

            query = {
                "$or": [
                    {"affected_pathways": user.get("current_visa_type")},
                    {"affected_pathways": user.get("target_pathway")},
                ],
                "severity": {"$in": ["critical", "high"]},
                "effective_date": {
                    "$lte": datetime.now(timezone.utc).isoformat()
                }
            }

            policies = await db.policy_updates.find(query).sort(
                "effective_date", -1
            ).to_list(5)

            return policies
        except Exception as e:
            logger.error(f"Failed to surface urgent policies: {e}")
            return []

    async def inject_policy_context(
        self,
        user_id: str,
        system_prompt: str,
        db=None,
    ) -> str:
        """
        Inject relevant policy context into LLM system prompt.
        Example: "As of Jan 2024, TR-to-PR cap is 30,000 per year"
        """
        try:
            policies = await self.surface_urgent_policies(user_id, db)

            if not policies:
                return system_prompt

            policy_context = "\n### RECENT POLICY UPDATES:\n"
            for policy in policies[:3]:
                policy_context += f"- [{policy['category']}] {policy['title']} (Effective: {policy['effective_date']})\n"
                policy_context += f"  Summary: {policy['summary'][:150]}...\n"

            return system_prompt + "\n" + policy_context
        except Exception as e:
            logger.error(f"Failed to inject policy context: {e}")
            return system_prompt


policy_engine = GovernmentPolicyEngine()
