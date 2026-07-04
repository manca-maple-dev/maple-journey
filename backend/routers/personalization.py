"""
Personalization API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user
from services.personalization import personalization_engine
from core.db import db
import logging

logger = logging.getLogger("maple.personalization_api")
router = APIRouter(prefix="/assistant", tags=["personalization"])


@router.post("/rank-alerts")
async def rank_alerts(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Get ranked list of alerts sorted by personalization score.
    POST body: { alerts: [...] }
    """
    try:
        alerts = body.get("alerts", [])
        ranked = await personalization_engine.rank_alerts(
            str(user["_id"]),
            alerts,
            db,
        )

        return {
            "count": len(ranked),
            "ranked_alerts": ranked,
        }
    except Exception as e:
        logger.error(f"Failed to rank alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to rank alerts")


@router.post("/rank-resources")
async def rank_resources(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Get ranked list of resources sorted by personalization score.
    POST body: { resources: [...], resource_type?: "shelter|legal_aid|etc" }
    """
    try:
        resources = body.get("resources", [])
        resource_type = body.get("resource_type")

        ranked = await personalization_engine.rank_resources(
            str(user["_id"]),
            resources,
            resource_type,
            db,
        )

        return {
            "count": len(ranked),
            "ranked_resources": ranked,
        }
    except Exception as e:
        logger.error(f"Failed to rank resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to rank resources")


@router.post("/rank-policies")
async def rank_policies(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Get ranked list of policies sorted by personalization score.
    POST body: { policies: [...] }
    """
    try:
        policies = body.get("policies", [])

        ranked = await personalization_engine.rank_policies(
            str(user["_id"]),
            policies,
            db,
        )

        return {
            "count": len(ranked),
            "ranked_policies": ranked,
        }
    except Exception as e:
        logger.error(f"Failed to rank policies: {e}")
        raise HTTPException(status_code=500, detail="Failed to rank policies")


@router.get("/personalization-score")
async def get_personalization_score(
    user: dict = Depends(get_current_user),
):
    """
    Get user's personalization settings and engagement score.
    """
    try:
        prefs = await db.user_preferences.find_one({"user_id": str(user["_id"])})
        engagement = await db.user_engagement.find_one({"user_id": str(user["_id"])})

        return {
            "preferences": prefs or {},
            "engagement_scores": engagement.get("scores", {}) if engagement else {},
        }
    except Exception as e:
        logger.error(f"Failed to get personalization score: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch personalization score")
