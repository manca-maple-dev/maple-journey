"""Auth: register, login, current user, profile updates, password reset."""
import os
import secrets
import hashlib
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from core.db import db
from core.config import DEFAULT_FEATURES
from core.security import hash_password, verify_password, create_access_token, get_current_user
from core.crypto import encrypt, decrypt
from models import RegisterIn, LoginIn, ProfileUpdate, SecureIdsIn, ForgotPasswordIn, ResetPasswordIn, ChangePasswordIn
from services.users import serialize_user

try:
    from services.email_service import send_email_safe
except ImportError:
    async def send_email_safe(*args, **kwargs):
        return False

from services.credits import ensure_wallet
from services.companion_welcome import send_welcome_message

router = APIRouter(tags=["auth"])


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.post("/auth/register")
async def register(body: RegisterIn, background_tasks: BackgroundTasks):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    doc = {
        "email": email,
        "password_hash": hash_password(body.password),
        "name": body.name,
        "phone": body.phone or "",  # Phone optional at signup
        "phone_verified": False,
        "role": "user",
        "country_of_origin": body.country_of_origin or "",
        "newcomer_type": body.newcomer_type or "",
        "visa_type": "",
        "pr_score": 0,
        "work_permit_expiry": (datetime.now(timezone.utc) + timedelta(days=420)).isoformat(),
        "features": DEFAULT_FEATURES.copy(),
        "companion_welcome_pending": True,  # Mark welcome as pending
        "companion_welcome_sent_at": None,
        "companion_welcome_channel": "",
        "enabled_channels": ["web"],  # Start with web, add other channels when welcome is sent
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    res = await db.users.insert_one(doc)
    doc["_id"] = res.inserted_id
    await ensure_wallet(str(res.inserted_id), tier="free")
    token = create_access_token(str(res.inserted_id), email, "user")
    
    # Send email welcome
    background_tasks.add_task(send_email_safe, email, "welcome", name=body.name)
    
    # Send WhatsApp/SMS welcome message if phone provided (or mark pending)
    if body.phone and body.phone.strip():
        background_tasks.add_task(send_welcome_message, str(res.inserted_id), body.phone)
    
    return {"token": token, "user": serialize_user(doc)}


@router.post("/auth/login")
async def login(body: LoginIn):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(user["_id"]), email, user.get("role", "user"))
    return {"token": token, "user": serialize_user(user)}


@router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return serialize_user(user)


@router.put("/auth/profile")
async def update_profile(body: ProfileUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
    fresh = await db.users.find_one({"_id": user["_id"]})
    return serialize_user(fresh)


@router.get("/auth/secure-ids")
async def get_secure_ids(user: dict = Depends(get_current_user)):
    enc = user.get("secure_ids") or {}
    return {
        "ircc_file_number": decrypt(enc.get("ircc_file_number", "")),
        "ucis_or_foreign_id": decrypt(enc.get("ucis_or_foreign_id", "")),
    }


@router.put("/auth/secure-ids")
async def set_secure_ids(body: SecureIdsIn, user: dict = Depends(get_current_user)):
    enc = dict(user.get("secure_ids") or {})
    if body.ircc_file_number is not None:
        enc["ircc_file_number"] = encrypt(body.ircc_file_number)
    if body.ucis_or_foreign_id is not None:
        enc["ucis_or_foreign_id"] = encrypt(body.ucis_or_foreign_id)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"secure_ids": enc}})
    return {"ok": True}


@router.get("/auth/export")
async def export_data(user: dict = Depends(get_current_user)):
    q = await db.questionnaires.find_one({"user_id": str(user["_id"])})
    return {
        "account": serialize_user(user),
        "questionnaire": (q or {}).get("answers"),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


@router.delete("/auth/account")
async def delete_account(background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    uid = str(user["_id"])
    email, name = user.get("email"), user.get("name", "")
    await db.users.delete_one({"_id": user["_id"]})
    for coll in ("questionnaires", "chat_messages", "saved_jobs", "payment_transactions", "wings_cache"):
        await db[coll].delete_many({"user_id": uid})
    if email:
        background_tasks.add_task(send_email_safe, email, "account_deleted", name=name)
    return {"ok": True}


@router.post("/auth/forgot-password")
async def forgot_password(body: ForgotPasswordIn, background_tasks: BackgroundTasks):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if user:
        raw = secrets.token_urlsafe(32)
        await db.password_reset_tokens.insert_one({
            "token_hash": _hash_token(raw),
            "user_id": str(user["_id"]),
            "email": email,
            "used": False,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        })
        base = os.environ.get("APP_BASE_URL", "").rstrip("/")
        reset_url = f"{base}/reset-password?token={raw}"
        background_tasks.add_task(send_email_safe, email, "password_reset", name=user.get("name", ""), reset_url=reset_url)
    # Always succeed to avoid revealing whether an account exists.
    return {"ok": True}


@router.post("/auth/reset-password")
async def reset_password(body: ResetPasswordIn, background_tasks: BackgroundTasks):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    doc = await db.password_reset_tokens.find_one({"token_hash": _hash_token(body.token), "used": False})
    exp = doc.get("expires_at") if doc else None
    if exp is not None and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if not doc or exp is None or exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired")
    user = await db.users.find_one({"_id": ObjectId(doc["user_id"])})
    if not user:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": hash_password(body.password)}})
    await db.password_reset_tokens.update_one({"_id": doc["_id"]}, {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}})
    background_tasks.add_task(send_email_safe, user["email"], "password_changed", name=user.get("name", ""))
    return {"ok": True}


@router.post("/auth/change-password")
async def change_password(body: ChangePasswordIn, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not verify_password(body.current_password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"password_hash": hash_password(body.new_password)}})
    if user.get("email"):
        background_tasks.add_task(send_email_safe, user["email"], "password_changed", name=user.get("name", ""))
    return {"ok": True}
