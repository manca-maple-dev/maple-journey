"""Twilio messaging: phone OTP verification + Maple on WhatsApp (inbound webhook)."""
import os
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request, Response

from core.db import db
from core.config import SYSTEM_PROMPT
from core.security import get_current_user
from models import PhoneIn, OtpVerifyIn
from services.twilio_service import normalize_phone, send_otp, check_otp, send_whatsapp, twilio_config_status
from services.wings import companion_welcome_message

logger = logging.getLogger("maplejourney.messaging")
router = APIRouter(tags=["messaging"])


@router.get("/messaging/config")
async def messaging_config():
    return twilio_config_status()


async def _send_companion_welcome_whatsapp(user: dict) -> bool:
    """Send the first Maple companion WhatsApp welcome once."""
    if not user.get("phone_verified") or not user.get("phone"):
        return False
    if not (user.get("consent_maple_companion") or (user.get("profile") or {}).get("consent_maple_companion")):
        return False
    if user.get("companion_welcome_sent_at"):
        return False
    text = companion_welcome_message(user, "WhatsApp")
    try:
        await send_whatsapp(user["phone"], text)
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "companion_welcome_pending": False,
                "companion_welcome_sent_at": datetime.now(timezone.utc).isoformat(),
                "companion_welcome_channel": "whatsapp",
            }},
        )
        return True
    except Exception:
        logger.exception("companion welcome whatsapp failed")
        return False


@router.post("/phone/send-otp")
async def send_otp_route(body: PhoneIn, user: dict = Depends(get_current_user)):
    phone = normalize_phone(body.phone)
    if len(phone) < 8:
        raise HTTPException(status_code=400, detail="Enter a valid number with country code, e.g. +14155551234")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"pending_phone": phone}})
    try:
        send_otp(phone)
    except RuntimeError as exc:
        logger.warning("send_otp unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("send_otp failed")
        raise HTTPException(status_code=502, detail="Could not send the code. Check the number and try again.")
    return {"ok": True, "phone": phone}


@router.post("/phone/verify-otp")
async def verify_otp_route(body: OtpVerifyIn, user: dict = Depends(get_current_user)):
    phone = normalize_phone(body.phone)
    pending = user.get("pending_phone")
    if pending and phone != pending:
        raise HTTPException(status_code=400, detail="This code was requested for a different number.")
    try:
        res = check_otp(phone, body.code.strip())
    except RuntimeError as exc:
        logger.warning("verify_otp unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("verify_otp failed")
        raise HTTPException(status_code=502, detail="Verification failed. Request a new code.")
    if res.status != "approved":
        raise HTTPException(status_code=400, detail="That code isn't correct or has expired.")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"phone": phone, "phone_verified": True}, "$unset": {"pending_phone": ""}})
    fresh = await db.users.find_one({"_id": user["_id"]}) or user
    await _send_companion_welcome_whatsapp(fresh)
    return {"ok": True, "phone": phone, "phone_verified": True}


@router.post("/whatsapp/test")
async def whatsapp_test(user: dict = Depends(get_current_user)):
    if not user.get("phone_verified"):
        raise HTTPException(status_code=400, detail="Verify your phone number first.")
    if not (user.get("consent_maple_companion") or (user.get("profile") or {}).get("consent_maple_companion")):
        raise HTTPException(status_code=400, detail="Enable Maple companion consent first.")
    try:
        sent = await _send_companion_welcome_whatsapp(user)
        if not sent:
            raise HTTPException(status_code=400, detail="Could not send the welcome message yet.")
    except RuntimeError as exc:
        logger.warning("whatsapp_test unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("whatsapp_test failed")
        raise HTTPException(status_code=502, detail="Couldn't send the WhatsApp message. Make sure you've joined the sandbox from this number.")
    return {"ok": True}


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """Legacy endpoint kept for compatibility.

    Delegates to the canonical /api/webhook/whatsapp handler so all channels
    share one security, consent, grounding, and rate-limit policy.
    """
    from routers.webhooks import webhook_whatsapp as canonical_whatsapp_webhook

    return await canonical_whatsapp_webhook(request)
