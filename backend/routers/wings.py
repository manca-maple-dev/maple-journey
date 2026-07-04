"""Maple Wingman: settings + proactive briefing. Feature-flag contract endpoint."""
from fastapi import APIRouter, Depends

from core.db import db
from core.config import DEFAULT_WINGS, FEATURE_KEYS
from core.security import get_current_user
from models import WingsSettingsIn
from services.users import get_global_features, user_features
from services.wings import build_briefing

router = APIRouter(tags=["wings"])

COMPANION_DAILY_LIMITS = {
    "free": 20,
    "plus": 50,
    "family": None,
}


def _companion_opted_in(user: dict) -> bool:
    profile = user.get("profile") or {}
    return bool(profile.get("consent_maple_companion") or user.get("consent_maple_companion"))


async def _companion_usage_today(user: dict) -> dict:
    tier = user.get("tier", "free")
    limit = COMPANION_DAILY_LIMITS.get(tier, COMPANION_DAILY_LIMITS["free"])
    uid = str(user["_id"])
    from datetime import datetime, timezone

    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    used = await db.chat_messages.count_documents(
        {
            "user_id": uid,
            "channel": {"$in": ["whatsapp", "imessage"]},
            "role": "user",
            "created_at": {"$gte": start_of_day},
        }
    )
    return {
        "tier": tier,
        "limit": limit,
        "used": used,
        "remaining": None if limit is None else max(0, limit - used),
    }


@router.get("/features")
async def effective_features(user: dict = Depends(get_current_user)):
    """Effective flags = global toggle AND per-user toggle."""
    glob = await get_global_features()
    usr = user_features(user)
    return {k: bool(glob.get(k, True) and usr.get(k, True)) for k in FEATURE_KEYS}


@router.put("/wings/settings")
async def update_wings_settings(body: WingsSettingsIn, user: dict = Depends(get_current_user)):
    wings = {**DEFAULT_WINGS, **user.get("wings", {})}
    for k, v in body.model_dump().items():
        if v is not None:
            wings[k] = v
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"wings": wings}})
    return wings


@router.get("/wings/briefing")
async def wings_briefing(user: dict = Depends(get_current_user)):
    return await build_briefing(user)


@router.get("/wings/companion/status")
async def wings_companion_status(user: dict = Depends(get_current_user)):
    usage = await _companion_usage_today(user)
    return {
        "phone_verified": bool(user.get("phone_verified")),
        "opted_in": _companion_opted_in(user),
        "welcome_pending": bool(user.get("companion_welcome_pending", False)),
        "welcome_sent_at": user.get("companion_welcome_sent_at"),
        "welcome_channel": user.get("companion_welcome_channel", ""),
        "channels": {
            "whatsapp": bool(user.get("phone_verified")),
            "imessage": bool(user.get("phone_verified") or user.get("email")),
        },
        "usage": usage,
    }
