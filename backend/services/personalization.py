"""
Personalization Engine — Smart ranking of alerts, resources, policies by user impact
Learns from user behavior: what they click, what they ignore, what they ask about
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("maple.personalization")


class RankingFactor(str, Enum):
    URGENCY = "urgency"  # Days until deadline
    PERSONAL_RELEVANCE = "personal_relevance"  # Matches user pathway
    IMPACT = "impact"  # How much this affects user
    EFFORT = "effort"  # How much work to handle this
    ENGAGEMENT = "engagement"  # User's past interest in similar items


class PersonalizationEngine:
    """
    Smart ranking engine for alerts, resources, policies.
    Learns from: clicks, dismissals, open times, follow-ups, search queries
    """

    def __init__(self):
        self.factor_weights = {
            RankingFactor.URGENCY: 0.30,
            RankingFactor.PERSONAL_RELEVANCE: 0.25,
            RankingFactor.IMPACT: 0.20,
            RankingFactor.EFFORT: 0.15,
            RankingFactor.ENGAGEMENT: 0.10,
        }

    async def rank_alerts(
        self,
        user_id: str,
        alerts: List[Dict],
        db=None,
    ) -> List[Dict]:
        """
        Rank alerts by personalized relevance score.
        High score = show first.
        """
        if db is None or not alerts:
            return alerts

        try:
            # Get user preferences
            user_prefs = await db.user_preferences.find_one({"user_id": str(user_id)})
            user_history = await self._get_user_engagement_history(user_id, db)

            scored_alerts = []
            for alert in alerts:
                score = await self._calculate_relevance_score(
                    alert,
                    user_prefs or {},
                    user_history,
                )
                alert["personalization_score"] = score
                scored_alerts.append(alert)

            # Sort by score (high first)
            scored_alerts.sort(key=lambda a: a["personalization_score"], reverse=True)
            return scored_alerts
        except Exception as e:
            logger.error(f"Failed to rank alerts: {e}")
            return alerts

    async def rank_resources(
        self,
        user_id: str,
        resources: List[Dict],
        resource_type: Optional[str] = None,
        db=None,
    ) -> List[Dict]:
        """
        Rank resources (shelters, legal aid, etc) by user needs.
        Consider: distance, hours, languages, past usage, ratings.
        """
        if db is None or not resources:
            return resources

        try:
            user_profile = await db.user_profiles.find_one({"user_id": str(user_id)})
            user_history = await self._get_user_resource_history(user_id, db)

            scored_resources = []
            for resource in resources:
                score = await self._calculate_resource_score(
                    resource,
                    user_profile or {},
                    user_history,
                )
                resource["personalization_score"] = score
                scored_resources.append(resource)

            scored_resources.sort(key=lambda r: r["personalization_score"], reverse=True)
            return scored_resources
        except Exception as e:
            logger.error(f"Failed to rank resources: {e}")
            return resources

    async def rank_policies(
        self,
        user_id: str,
        policies: List[Dict],
        db=None,
    ) -> List[Dict]:
        """
        Rank government policies by user impact.
        High impact to user = high score.
        """
        if db is None or not policies:
            return policies

        try:
            user_profile = await db.user_profiles.find_one({"user_id": str(user_id)})
            user_history = await self._get_user_engagement_history(user_id, db)

            scored_policies = []
            for policy in policies:
                score = await self._calculate_policy_score(
                    policy,
                    user_profile or {},
                    user_history,
                )
                policy["personalization_score"] = score
                scored_policies.append(policy)

            scored_policies.sort(key=lambda p: p["personalization_score"], reverse=True)
            return scored_policies
        except Exception as e:
            logger.error(f"Failed to rank policies: {e}")
            return policies

    async def _calculate_relevance_score(
        self,
        alert: Dict,
        user_prefs: Dict,
        user_history: Dict,
    ) -> float:
        """
        Calculate personalization score for an alert (0-100).
        """
        score = 0.0

        # Urgency: days until deadline (exponential weight)
        days_until = alert.get("days_until", 90)
        urgency_score = min(100, 100 * (30 / (days_until + 1)))
        score += urgency_score * self.factor_weights[RankingFactor.URGENCY]

        # Personal relevance: matches user's visa type/pathway
        user_visa = user_prefs.get("current_visa_type", "")
        alert_relevant_to = alert.get("relevant_to", [])
        relevance_score = 50 if user_visa in alert_relevant_to else 10
        score += relevance_score * self.factor_weights[RankingFactor.PERSONAL_RELEVANCE]

        # Impact: how much this affects user
        impact_score = alert.get("impact_score", 50)  # 1-100
        score += impact_score * self.factor_weights[RankingFactor.IMPACT]

        # Effort: inversely weighted (low effort = high score)
        effort_level = alert.get("effort_level", 50)  # 1-100 (higher = harder)
        effort_score = 100 - effort_level
        score += effort_score * self.factor_weights[RankingFactor.EFFORT]

        # Engagement: user's past interest in similar alerts
        engagement_score = user_history.get(alert.get("category"), 0)
        score += engagement_score * self.factor_weights[RankingFactor.ENGAGEMENT]

        return min(100, score)

    async def _calculate_resource_score(
        self,
        resource: Dict,
        user_profile: Dict,
        user_history: Dict,
    ) -> float:
        """
        Calculate personalization score for a resource (0-100).
        """
        score = 0.0

        # Distance: closer = higher score
        distance_km = resource.get("distance_km", 50)
        distance_score = max(10, 100 * (1 / (1 + distance_km)))
        score += distance_score * 0.30

        # Hours/availability: open when user needs
        hours = resource.get("hours", {})
        availability_score = 70 if hours.get("24_hours") else 50
        score += availability_score * 0.20

        # Languages: matches user language
        user_languages = user_profile.get("languages", ["en"])
        resource_languages = resource.get("languages", ["en"])
        lang_match = any(lang in resource_languages for lang in user_languages)
        language_score = 80 if lang_match else 30
        score += language_score * 0.15

        # Past usage: user has used this type before
        resource_type = resource.get("type", "")
        past_usage_score = user_history.get(resource_type, 0)
        score += past_usage_score * 0.20

        # Rating: community rating if available
        rating = resource.get("rating", 3.5) / 5 * 100
        score += rating * 0.15

        return min(100, score)

    async def _calculate_policy_score(
        self,
        policy: Dict,
        user_profile: Dict,
        user_history: Dict,
    ) -> float:
        """
        Calculate personalization score for a policy (0-100).
        """
        score = 0.0

        # Severity: critical/urgent = high score
        severity = policy.get("severity", "medium")
        severity_map = {
            "critical": 100,
            "high": 80,
            "medium": 50,
            "low": 20,
        }
        severity_score = severity_map.get(severity, 50)
        score += severity_score * 0.25

        # Affected pathway: matches user current/target pathway
        affected_pathways = policy.get("affected_pathways", [])
        user_visa = user_profile.get("current_visa_type", "")
        user_target = user_profile.get("target_pathway", "")
        pathway_match = user_visa in affected_pathways or user_target in affected_pathways
        pathway_score = 80 if pathway_match else 20
        score += pathway_score * 0.35

        # Timing: effective soon = higher score
        from datetime import datetime
        effective_date = policy.get("effective_date")
        days_until_effective = 90
        if effective_date:
            try:
                eff_dt = datetime.fromisoformat(effective_date)
                now_dt = datetime.now(timezone.utc)
                days_until_effective = (eff_dt - now_dt).days
            except:
                pass

        timing_score = min(100, 100 * (30 / (days_until_effective + 1)))
        score += timing_score * 0.20

        # Engagement: user's interest in this policy category
        category = policy.get("category", "")
        engagement_score = user_history.get(category, 0)
        score += engagement_score * 0.20

        return min(100, score)

    async def _get_user_engagement_history(self, user_id: str, db) -> Dict:
        """
        Get user's engagement patterns (what they click, ignore, ask about).
        """
        try:
            history = await db.user_engagement.find_one({"user_id": str(user_id)})
            if history:
                return history.get("scores", {})
            return {}
        except Exception as e:
            logger.error(f"Failed to get engagement history: {e}")
            return {}

    async def _get_user_resource_history(self, user_id: str, db) -> Dict:
        """
        Get user's resource usage history.
        """
        try:
            history = await db.user_resource_usage.find_one({"user_id": str(user_id)})
            if history:
                return history.get("resource_scores", {})
            return {}
        except Exception as e:
            logger.error(f"Failed to get resource history: {e}")
            return {}


personalization_engine = PersonalizationEngine()
