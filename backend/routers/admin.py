"""Admin console APIs: stats, user & feature management, content, catalog, announcements."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from core.db import db, clean
from core.config import FEATURE_KEYS, SETTINGS_ID
from core.security import require_admin
from models import UserFeatureUpdate, AdminUserPatch, ResourceIn, BenefitIn, AnnouncementIn, LegalResourceIn, TestEmailIn
from services.users import serialize_user, get_global_features, user_features
from services.email_service import send_email_safe

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(admin: dict = Depends(require_admin)):
    total_users = await db.users.count_documents({"role": "user"})
    total_assessments = await db.questionnaires.count_documents({})
    total_chats = await db.chat_messages.count_documents({"role": "user"})
    glob = await get_global_features()
    usage = {k: await db.users.count_documents({"role": "user", f"features.{k}": {"$ne": False}}) for k in FEATURE_KEYS}
    return {
        "total_users": total_users,
        "total_assessments": total_assessments,
        "total_chats": total_chats,
        "global_features": glob,
        "feature_usage": usage,
    }


@router.get("/users")
async def admin_users(admin: dict = Depends(require_admin)):
    items = await db.users.find({}).sort("created_at", -1).to_list(1000)
    return [serialize_user(u) for u in items]


@router.put("/users/{user_id}/features")
async def admin_update_user_features(user_id: str, body: UserFeatureUpdate, admin: dict = Depends(require_admin)):
    target = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    feats = user_features(target)
    feats.update({k: v for k, v in body.features.items() if k in FEATURE_KEYS})
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"features": feats}})
    fresh = await db.users.find_one({"_id": ObjectId(user_id)})
    return serialize_user(fresh)


@router.put("/users/{user_id}")
async def admin_patch_user(user_id: str, body: AdminUserPatch, admin: dict = Depends(require_admin)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    fresh = await db.users.find_one({"_id": ObjectId(user_id)})
    return serialize_user(fresh)


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: str, admin: dict = Depends(require_admin)):
    await db.users.delete_one({"_id": ObjectId(user_id), "role": {"$ne": "admin"}})
    return {"ok": True}


@router.get("/features")
async def admin_get_features(admin: dict = Depends(require_admin)):
    return await get_global_features()


@router.put("/features")
async def admin_set_features(body: UserFeatureUpdate, admin: dict = Depends(require_admin)):
    glob = await get_global_features()
    glob.update({k: v for k, v in body.features.items() if k in FEATURE_KEYS})
    await db.app_settings.update_one({"_id": SETTINGS_ID}, {"$set": {"features": glob}}, upsert=True)
    return glob


# ----- Content management -----
@router.get("/content")
async def admin_get_content(admin: dict = Depends(require_admin)):
    doc = await db.content.find_one({"_id": "landing"})
    return doc.get("data", {}) if doc else {}


@router.put("/content")
async def admin_set_content(body: Dict[str, Any], admin: dict = Depends(require_admin)):
    await db.content.update_one({"_id": "landing"}, {"$set": {"data": body}}, upsert=True)
    return body


# ----- Resources -----
@router.post("/resources")
async def admin_add_resource(body: ResourceIn, admin: dict = Depends(require_admin)):
    doc = {"id": str(uuid.uuid4()), **body.model_dump()}
    await db.resources.insert_one(doc)
    return clean(doc)


@router.delete("/resources/{item_id}")
async def admin_del_resource(item_id: str, admin: dict = Depends(require_admin)):
    await db.resources.delete_one({"id": item_id})
    return {"ok": True}


# ----- Benefits -----
@router.post("/benefits")
async def admin_add_benefit(body: BenefitIn, admin: dict = Depends(require_admin)):
    doc = {"id": str(uuid.uuid4()), **body.model_dump()}
    await db.benefits.insert_one(doc)
    return clean(doc)


@router.delete("/benefits/{item_id}")
async def admin_del_benefit(item_id: str, admin: dict = Depends(require_admin)):
    await db.benefits.delete_one({"id": item_id})
    return {"ok": True}


# ----- Legal resources -----
@router.post("/legal-resources")
async def admin_add_legal_resource(body: LegalResourceIn, admin: dict = Depends(require_admin)):
    doc = {"id": str(uuid.uuid4()), **body.model_dump()}
    await db.legal_resources.insert_one(doc)
    return clean(doc)


@router.delete("/legal-resources/{item_id}")
async def admin_del_legal_resource(item_id: str, admin: dict = Depends(require_admin)):
    await db.legal_resources.delete_one({"id": item_id})
    return {"ok": True}


# ----- Announcements -----
@router.post("/announcements")
async def admin_add_announcement(body: AnnouncementIn, admin: dict = Depends(require_admin)):
    doc = {"id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat(), **body.model_dump()}
    await db.announcements.insert_one(doc)
    return clean(doc)


@router.delete("/announcements/{item_id}")
async def admin_del_announcement(item_id: str, admin: dict = Depends(require_admin)):
    await db.announcements.delete_one({"id": item_id})
    return {"ok": True}


# ----- Email -----
@router.post("/email/test")
async def admin_test_email(body: TestEmailIn, background_tasks: BackgroundTasks, admin: dict = Depends(require_admin)):
    to = (body.to or admin["email"])
    background_tasks.add_task(send_email_safe, to, "test", name=admin.get("name", "Team"))
    return {"ok": True, "to": to}


@router.post("/announcements/{item_id}/broadcast")
async def admin_broadcast_announcement(item_id: str, background_tasks: BackgroundTasks, admin: dict = Depends(require_admin)):
    ann = await db.announcements.find_one({"id": item_id})
    if not ann:
        raise HTTPException(status_code=404, detail="Announcement not found")
    recipients = await db.users.find({"role": "user"}, {"email": 1, "name": 1}).to_list(5000)
    for u in recipients:
        if u.get("email"):
            background_tasks.add_task(send_email_safe, u["email"], "announcement",
                                     name=u.get("name", ""), title=ann.get("title", ""), body_text=ann.get("body", ""))
    return {"ok": True, "recipients": len(recipients)}
