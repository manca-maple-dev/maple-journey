"""Multi-channel messaging integration.

Supports WhatsApp (Twilio), SMS, and push notifications (iMessage via Firebase).
"""
from fastapi import APIRouter, Depends, Body
from core.security import get_current_user
from core.db import db
import os
import httpx
import json
from typing import Optional

router = APIRouter(prefix="/messaging", tags=["messaging"])

# === TWILIO SETUP ===
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")  # format: whatsapp:+1234567890

# === FIREBASE SETUP (for iMessage/push) ===
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")


@router.post("/whatsapp/send")
async def send_whatsapp_message(
    user: dict = Depends(get_current_user),
    body: dict = Body(...),
):
    """Send WhatsApp message via Twilio.
    
    Body:
    {
        "to": "+1234567890",
        "message": "Hello! 👋",
        "template": "welcome" // optional: predefined templates
    }
    """
    to_number = body.get("to", "").strip()
    message = body.get("message", "").strip()
    template = body.get("template")

    if not to_number or not message:
        return {"error": "Missing 'to' or 'message'"}

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {"error": "WhatsApp not configured"}

    # Format: whatsapp:+1234567890
    if not to_number.startswith("+"):
        to_number = "+" + to_number
    to_whatsapp = f"whatsapp:{to_number}"

    try:
        async with httpx.AsyncClient() as client:
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                auth=auth,
                data={
                    "From": TWILIO_WHATSAPP_NUMBER,
                    "To": to_whatsapp,
                    "Body": message,
                },
            )
            result = response.json()
            
            # Log to database
            await db.messaging_logs.insert_one({
                "user_id": user.get("_id"),
                "channel": "whatsapp",
                "to": to_number,
                "message": message,
                "status": "sent" if response.status_code == 201 else "failed",
                "twilio_sid": result.get("sid"),
                "created_at": __import__("datetime").datetime.utcnow(),
            })
            
            return {
                "status": "sent" if response.status_code == 201 else "failed",
                "message_sid": result.get("sid"),
                "to": to_number,
            }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@router.post("/sms/send")
async def send_sms_message(
    user: dict = Depends(get_current_user),
    body: dict = Body(...),
):
    """Send SMS via Twilio (fallback for iMessage).
    
    Body:
    {
        "to": "+1234567890",
        "message": "Hello!"
    }
    """
    to_number = body.get("to", "").strip()
    message = body.get("message", "").strip()

    if not to_number or not message:
        return {"error": "Missing 'to' or 'message'"}

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {"error": "SMS not configured"}

    if not to_number.startswith("+"):
        to_number = "+" + to_number

    try:
        async with httpx.AsyncClient() as client:
            auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                auth=auth,
                data={
                    "From": os.environ.get("TWILIO_PHONE_NUMBER", ""),
                    "To": to_number,
                    "Body": message,
                },
            )
            result = response.json()
            
            # Log to database
            await db.messaging_logs.insert_one({
                "user_id": user.get("_id"),
                "channel": "sms",
                "to": to_number,
                "message": message,
                "status": "sent" if response.status_code == 201 else "failed",
                "twilio_sid": result.get("sid"),
                "created_at": __import__("datetime").datetime.utcnow(),
            })
            
            return {
                "status": "sent" if response.status_code == 201 else "failed",
                "message_sid": result.get("sid"),
                "to": to_number,
            }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@router.post("/push/send")
async def send_push_notification(
    user: dict = Depends(get_current_user),
    body: dict = Body(...),
):
    """Send push notification via Firebase (works for iMessage on web/iOS).
    
    Body:
    {
        "device_token": "firebase_device_token",
        "title": "Settlement Alert",
        "body": "New resources available in Toronto",
        "icon": "settlement"
    }
    """
    device_token = body.get("device_token", "").strip()
    title = body.get("title", "MapleJourney")
    message_body = body.get("body", "")
    icon = body.get("icon", "default")

    if not device_token or not message_body:
        return {"error": "Missing device_token or body"}

    if not FIREBASE_API_KEY or not FIREBASE_PROJECT_ID:
        return {"error": "Firebase not configured"}

    try:
        payload = {
            "message": {
                "token": device_token,
                "notification": {
                    "title": title,
                    "body": message_body,
                },
                "webpush": {
                    "fcmOptions": {
                        "link": "https://mapljourney.app/app/communities",
                    },
                    "notification": {
                        "icon": f"https://mapljourney.app/icons/{icon}.png",
                        "badge": "https://mapljourney.app/badge.png",
                    },
                },
                "apns": {
                    "payload": {
                        "aps": {
                            "alert": {
                                "title": title,
                                "body": message_body,
                            },
                            "sound": "default",
                            "badge": 1,
                        }
                    }
                },
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://fcm.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/messages:send",
                headers={"Authorization": f"Bearer {FIREBASE_API_KEY}"},
                json=payload,
            )
            
            result = response.json() if response.status_code == 200 else {"error": response.text}
            
            # Log to database
            await db.messaging_logs.insert_one({
                "user_id": user.get("_id"),
                "channel": "push",
                "device_token": device_token,
                "title": title,
                "message": message_body,
                "status": "sent" if response.status_code == 200 else "failed",
                "firebase_id": result.get("name"),
                "created_at": __import__("datetime").datetime.utcnow(),
            })
            
            return {
                "status": "sent" if response.status_code == 200 else "failed",
                "message_id": result.get("name"),
                "device_token": device_token,
            }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@router.get("/whatsapp/webhook")
async def whatsapp_webhook_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    """Verify Twilio WhatsApp webhook."""
    verify_token = os.environ.get("TWILIO_WEBHOOK_VERIFY_TOKEN", "maplejour")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge)
    return {"error": "Invalid token"}


@router.post("/whatsapp/webhook")
async def whatsapp_webhook_received(body: dict = Body(...)):
    """Receive incoming WhatsApp messages from Twilio."""
    from_number = body.get("From", "").replace("whatsapp:", "")
    message_text = body.get("Body", "").strip()
    message_sid = body.get("MessageSid")
    
    # Store incoming message
    await db.messaging_logs.insert_one({
        "channel": "whatsapp",
        "direction": "inbound",
        "from": from_number,
        "message": message_text,
        "message_sid": message_sid,
        "created_at": __import__("datetime").datetime.utcnow(),
    })
    
    # Route directly to Maple companion so users can text Maple without opening the app
    from routers.companion import handle_whatsapp_inbound, WhatsAppMessage
    await handle_whatsapp_inbound(
        WhatsAppMessage(
            from_phone=from_number,
            body=message_text,
            message_sid=message_sid or "",
            num_media=int(body.get("NumMedia", 0) or 0),
        ),
        None,
    )

    return {
        "status": "received",
        "message_sid": message_sid,
    }


@router.post("/imessage/webhook")
async def imessage_webhook_received(body: dict = Body(...)):
    """Receive incoming iMessage (SMS) messages from Twilio.
    
    iMessage on iPhone appears as SMS messages via Twilio.
    This endpoint handles inbound messages from iPhone users via iMessage transport.
    """
    from_number = body.get("From", "")
    message_text = body.get("Body", "").strip()
    message_sid = body.get("MessageSid")
    num_media = body.get("NumMedia", 0)
    
    # Normalize phone number
    if from_number.startswith("+"):
        phone = from_number
    else:
        phone = "+" + from_number if from_number else ""
    
    # Store incoming message
    await db.messaging_logs.insert_one({
        "channel": "imessage",
        "direction": "inbound",
        "from": phone,
        "message": message_text,
        "message_sid": message_sid,
        "has_media": num_media > 0,
        "created_at": __import__("datetime").datetime.utcnow(),
    })
    
    # Route directly to Maple companion so users can text Maple without opening the app
    from routers.companion import handle_imessage_inbound, iMessageMessage
    await handle_imessage_inbound(
        iMessageMessage(
            from_phone=phone,
            body=message_text,
            message_sid=message_sid or "",
            num_media=int(num_media or 0),
        ),
        None,
    )

    return {
        "status": "received",
        "message_sid": message_sid,
        "channel": "imessage",
    }


@router.post("/imessage/send")
async def send_imessage_message(
    user: dict = Depends(get_current_user),
    body: dict = Body(...),
):
    """Send iMessage via SMS transport (appears as iMessage on iPhone).
    
    Body:
    {
        "to": "+1234567890",
        "message": "Hello from Maple!"
    }
    
    Note: SMS delivery is used as transport. On iPhone, this will appear as iMessage
    (if user has iCloud account). On Android, appears as regular SMS.
    """
    to_number = body.get("to", "").strip()
    message = body.get("message", "").strip()
    
    if not to_number or not message:
        return {"error": "Missing 'to' or 'message'"}
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {"error": "iMessage not configured"}
    
    # Normalize phone
    if not to_number.startswith("+"):
        to_number = "+" + to_number
    
    try:
        from services.twilio_service import send_imessage
        
        result = await send_imessage(to_number, message)
        
        # Log to database
        await db.messaging_logs.insert_one({
            "user_id": str(user.get("_id")),
            "channel": "imessage",
            "direction": "outbound",
            "to": to_number,
            "message": message,
            "status": "sent",
            "twilio_sid": result.sid,
            "created_at": __import__("datetime").datetime.utcnow(),
        })
        
        return {
            "status": "sent",
            "message_sid": result.sid,
            "to": to_number,
            "channel": "imessage",
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@router.get("/channels/status")
async def messaging_channels_status(user: dict = Depends(get_current_user)):
    """Check which channels are configured."""
    return {
        "channels": {
            "whatsapp": {
                "configured": bool(TWILIO_ACCOUNT_SID),
                "provider": "Twilio",
                "status": "ready" if TWILIO_ACCOUNT_SID else "needs_setup",
                "webhook": "/api/webhook/whatsapp-inbound",
                "description": "24/7 companion via WhatsApp"
            },
            "imessage": {
                "configured": bool(TWILIO_ACCOUNT_SID),
                "provider": "Twilio (SMS → iMessage on iPhone)",
                "status": "ready" if TWILIO_ACCOUNT_SID else "needs_setup",
                "webhook": "/api/webhook/imessage-inbound",
                "description": "Companion via iMessage (appears as iMessage on iPhone, SMS on Android)"
            },
            "sms": {
                "configured": bool(TWILIO_ACCOUNT_SID),
                "provider": "Twilio",
                "status": "ready" if TWILIO_ACCOUNT_SID else "needs_setup",
                "description": "Fallback SMS channel"
            },
            "push": {
                "configured": bool(FIREBASE_API_KEY),
                "provider": "Firebase",
                "status": "ready" if FIREBASE_API_KEY else "needs_setup",
                "description": "Push notifications for web/app"
            }
        },
        "companion": {
            "active_channels": ["whatsapp", "imessage"],
            "session_memory": True,
            "multi_turn": True,
            "grounded_ai": True
        }
    }
