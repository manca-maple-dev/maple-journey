"""User serialization and feature-flag resolution."""
from typing import Dict

from core.config import DEFAULT_FEATURES, FEATURE_KEYS, DEFAULT_WINGS, SETTINGS_ID
from core.db import db


async def get_global_features() -> Dict[str, bool]:
    doc = await db.app_settings.find_one({"_id": SETTINGS_ID})
    if not doc:
        await db.app_settings.insert_one({"_id": SETTINGS_ID, "features": DEFAULT_FEATURES.copy()})
        return DEFAULT_FEATURES.copy()
    merged = DEFAULT_FEATURES.copy()
    merged.update({k: v for k, v in doc.get("features", {}).items() if k in FEATURE_KEYS})
    return merged


def user_features(user: dict) -> Dict[str, bool]:
    merged = DEFAULT_FEATURES.copy()
    merged.update({k: v for k, v in user.get("features", {}).items() if k in FEATURE_KEYS})
    return merged


def serialize_user(user: dict) -> dict:
    wings = {**DEFAULT_WINGS, **user.get("wings", {})}
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", "user"),
        "country_of_origin": user.get("country_of_origin", ""),
        "newcomer_type": user.get("newcomer_type", ""),
        "visa_type": user.get("visa_type", ""),
        "pr_score": user.get("pr_score", 0),
        "tier": user.get("tier", "free"),
        "tier_expires_at": user.get("tier_expires_at"),
        "work_permit_expiry": user.get("work_permit_expiry"),
        "avatar": user.get("avatar", ""),
        "phone": user.get("phone", ""),
        "phone_verified": user.get("phone_verified", False),
        "companion_welcome_pending": bool(user.get("companion_welcome_pending", False)),
        "companion_welcome_sent_at": user.get("companion_welcome_sent_at"),
        "companion_welcome_channel": user.get("companion_welcome_channel", ""),
        "profile": user.get("profile") or {},
        "profile_completed": bool(user.get("profile_completed")),
        "features": user_features(user),
        "wings": wings,
        "created_at": user.get("created_at"),
    }
