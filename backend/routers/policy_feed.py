"""
Government Policy Feed API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user
from services.policy_feed import policy_engine
from core.db import db
from datetime import datetime, timezone
import logging

logger = logging.getLogger("maple.policy_api")
router = APIRouter(prefix="/assistant", tags=["policy-feed"])


@router.get("/policy-updates")
async def get_policy_updates(
    user: dict = Depends(get_current_user),
):
    """
    Get all recent government policy updates.
    Sorted by effective date, newest first.
    """
    try:
        updates = await policy_engine.fetch_policy_updates(db)

        return {
            "count": len(updates),
            "updates": updates,
        }
    except Exception as e:
        logger.error(f"Failed to get policy updates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch policy updates")


@router.get("/relevant-policies")
async def get_relevant_policies(
    user: dict = Depends(get_current_user),
):
    """
    Get policies relevant to current user's visa status and goals.
    Personalized based on user profile.
    """
    try:
        # Get user's full profile
        user_profile = await db.user_profiles.find_one({"user_id": str(user["_id"])})

        if not user_profile:
            return {"count": 0, "policies": []}

        policies = await policy_engine.get_relevant_policies(user_profile, db)

        return {
            "count": len(policies),
            "policies": policies,
        }
    except Exception as e:
        logger.error(f"Failed to get relevant policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch relevant policies")


@router.get("/urgent-policies")
async def get_urgent_policies(
    user: dict = Depends(get_current_user),
):
    """
    Get CRITICAL and HIGH priority policy changes affecting current user.
    These should be surfaced in UI immediately.
    """
    try:
        urgent = await policy_engine.surface_urgent_policies(user["_id"], db)

        return {
            "count": len(urgent),
            "urgent_policies": urgent,
        }
    except Exception as e:
        logger.error(f"Failed to get urgent policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch urgent policies")


@router.post("/policy-subscribe")
async def subscribe_to_policy_updates(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Subscribe user to policy update notifications.
    POST body: { categories: [...], severity_minimum: "high|medium|low" }
    """
    try:
        categories = body.get("categories", [])
        min_severity = body.get("severity_minimum", "high")

        # Update user's subscription preferences
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "policy_subscriptions": {
                        "categories": categories,
                        "min_severity": min_severity,
                        "subscribed_at": datetime.now(timezone.utc).isoformat(),
                    }
                }
            },
        )

        return {"subscribed": True, "settings": {"categories": categories, "min_severity": min_severity}}
    except Exception as e:
        logger.error(f"Failed to update policy subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to update subscription")


@router.post("/policy-read")
async def mark_policy_read(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Mark a policy update as read by user.
    Prevents duplicate notifications.
    """
    try:
        policy_id = body.get("policy_id")

        await db.user_policy_reads.insert_one({
            "user_id": str(user["_id"]),
            "policy_id": policy_id,
            "read_at": datetime.now(timezone.utc).isoformat(),
        })

        return {"marked_read": True, "policy_id": policy_id}
    except Exception as e:
        logger.error(f"Failed to mark policy as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark as read")
