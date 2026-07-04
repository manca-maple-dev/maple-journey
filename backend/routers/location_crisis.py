"""
Location & Crisis API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from core.security import get_current_user
from services.location_awareness import location_engine, ResourceType
from services.crisis_escalation import crisis_escalation
from core.db import db
import logging

logger = logging.getLogger("maple.location_crisis_api")
router = APIRouter(prefix="/assistant", tags=["location-crisis"])


@router.post("/nearby-resources")
async def get_nearby_resources(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Find nearby resources (shelters, legal aid, health clinics, etc.)
    POST body: { latitude, longitude, resource_type, radius_km }
    """
    try:
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        resource_type_str = body.get("resource_type")
        radius_km = body.get("radius_km", 5)

        if not latitude or not longitude:
            raise HTTPException(status_code=400, detail="latitude and longitude required")

        resource_type = None
        if resource_type_str:
            try:
                resource_type = ResourceType(resource_type_str)
            except ValueError:
                pass

        resources = await location_engine.find_nearby_resources(
            latitude=latitude,
            longitude=longitude,
            resource_type=resource_type,
            radius_km=radius_km,
            db=db,
        )

        return {
            "count": len(resources),
            "resources": resources,
            "location": {"latitude": latitude, "longitude": longitude},
        }
    except Exception as e:
        logger.error(f"Failed to find nearby resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to find resources")


@router.post("/crisis-check")
async def check_for_crisis(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Check message for crisis language.
    If detected, return immediate hotline info.
    POST body: { message, country }
    """
    try:
        message = body.get("message", "")
        country = body.get("country", "canada")

        # Detect crisis
        crisis_type = crisis_escalation.detect_crisis(message)

        if crisis_type:
            # Return immediate help
            help_info = await crisis_escalation.get_immediate_help(crisis_type, country)

            # Log alert for audit
            await crisis_escalation.log_crisis_alert(
                user_id=user["_id"],
                crisis_type=crisis_type,
                message_preview=message[:100],
                country=country,
                db=db,
            )

            return help_info
        else:
            return {"crisis_detected": False}

    except Exception as e:
        logger.error(f"Crisis check failed: {e}")
        # Fail safe: return hotline info
        return {
            "crisis_detected": True,
            "error": "Safety check error — please call 911 or emergency services",
        }


@router.post("/emergency-resources")
async def get_emergency_resources(
    body: dict,
    user: dict = Depends(get_current_user),
):
    """
    Get critical resources for emergency type (DV, health, food, shelter, legal).
    POST body: { latitude, longitude, emergency_type, country }
    """
    try:
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        emergency_type = body.get("emergency_type")
        country = body.get("country", "canada")

        if not emergency_type:
            raise HTTPException(status_code=400, detail="emergency_type required")

        resources = await location_engine.get_urgent_resources(
            latitude=latitude,
            longitude=longitude,
            emergency_type=emergency_type,
            db=db,
        )

        return {
            "emergency_type": emergency_type,
            "count": len(resources),
            "resources": resources[:5],  # Top 5 closest
        }
    except Exception as e:
        logger.error(f"Failed to get emergency resources: {e}")
        raise HTTPException(status_code=500, detail="Failed to find emergency resources")
