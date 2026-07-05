"""Phase 3: Companion Integration for WhatsApp + iMessage

Complete webhook handlers for multi-channel messaging with:
- Per-user session routing
- Companion memory persistence (multi-turn context)
- Citation validation (IRPA s.91)
- Law change alerts
- Support for WhatsApp and iMessage channels

Routes:
- POST /webhook/whatsapp-inbound → Process WhatsApp messages
- POST /webhook/imessage-inbound → Process iMessage (SMS) messages
- POST /webhook/law-change → Monitor & dispatch alerts
"""

import os
import logging
import hashlib
import hmac
import asyncio
import base64
from datetime import datetime, timezone
from typing import Optional
import httpx
from pymongo.errors import DuplicateKeyError

from fastapi import APIRouter, HTTPException, Request, Response, BackgroundTasks
from pydantic import BaseModel

from core.db import db
from core.config import SYSTEM_PROMPT, SOVEREIGN_SYSTEM_PROMPT
from services.companion_memory import CompanionMemory
from services.citation_validator import CitationValidator
from services.twilio_service import send_whatsapp, send_imessage, send_message_by_channel
import anthropic

logger = logging.getLogger("maplejourney.companion")

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# Initialize services
companion_memory = CompanionMemory(db)
citation_validator = CitationValidator()


async def ensure_webhook_indexes() -> None:
    """Indexes for webhook idempotency and lightweight retention."""
    await db.webhook_message_dedup.create_index(
        [("channel", 1), ("message_sid", 1)],
        unique=True,
        sparse=True,
    )
    await db.webhook_message_dedup.create_index("created_at", expireAfterSeconds=14 * 24 * 60 * 60)


async def _claim_inbound_message(channel: str, message_sid: str) -> bool:
    """Return False when an inbound message was already processed."""
    if not message_sid:
        return True
    try:
        await db.webhook_message_dedup.insert_one(
            {
                "channel": channel,
                "message_sid": message_sid,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return True
    except DuplicateKeyError:
        return False


def _twilio_webhook_url(request: Request) -> str:
    """Build externally visible URL used by Twilio signature validation."""
    base = os.getenv("WEBHOOK_BASE_URL", "").strip().rstrip("/")
    if base:
        return f"{base}{request.url.path}"
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    return f"{proto}://{host}{request.url.path}"


def _validate_twilio_signature(url: str, params: dict, signature: str, auth_token: str) -> bool:
    """Validate Twilio webhook signature with SDK when available, fallback to compatible HMAC."""
    if not auth_token or not signature:
        return False

    try:
        from twilio.request_validator import RequestValidator

        return RequestValidator(auth_token).validate(url, params, signature)
    except Exception:
        payload = url + "".join(f"{k}{v}" for k, v in sorted(params.items()))
        digest = hmac.new(auth_token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1).digest()
        expected = base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected, signature or "")


async def _anthropic_completion(system_prompt: str, user_query: str) -> tuple[str, int]:
    """Run Anthropic completion without blocking the event loop."""

    def _call_anthropic() -> tuple[str, int]:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_query}],
        )
        text = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens

    return await asyncio.to_thread(_call_anthropic)


class WhatsAppMessage(BaseModel):
    """Inbound WhatsApp message from Twilio."""
    from_phone: str
    body: str
    message_sid: str
    num_media: int = 0


class iMessageMessage(BaseModel):
    """Inbound iMessage (SMS transport) from Twilio."""
    from_phone: str
    body: str
    message_sid: str
    num_media: int = 0


class LawChangeAlert(BaseModel):
    """Law change detected by monitor."""
    title: str
    summary: str
    effective_date: str
    source_url: str
    affected_categories: list[str]  # ["express_entry", "work_permit", ...]


# === SHARED HANDLER (both WhatsApp and iMessage use this) ===
async def _handle_companion_message(
    from_phone: str,
    query: str,
    channel: str = "whatsapp",
    message_sid: str = None,
) -> dict:
    """Process companion message from any channel.
    
    Args:
        from_phone: User's phone number
        query: User's message text
        channel: 'whatsapp' or 'imessage'
        message_sid: Twilio message ID for logging
    
    Returns:
        { ok, session_id, turns }
    """
    
    logger.info(f"{channel.upper()} inbound from {from_phone}: {query[:50]}...")
    
    try:
        # 1. Resolve user
        user = await db.users.find_one({"phone": from_phone, "phone_verified": True})
        if not user:
            response_text = "👋 Hi! I don't have your profile yet. Please visit maplejourney.ca to get started with Maple."
            await send_message_by_channel(from_phone, response_text, channel)
            return {"ok": True}
        
        # 2. Get/create session
        session = await companion_memory.get_or_create_session(
            str(user["_id"]),
            channel=channel
        )
        session_id = session["session_id"]
        
        # Store channel preference if user hasn't enabled it yet
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$addToSet": {"enabled_channels": channel}},
        )
        
        # 3. Get recent context (last 3 turns)
        recent_context = await companion_memory.get_recent_context(session_id, num_turns=3)
        
        # Build context prompt
        context_prompt = ""
        if recent_context:
            context_prompt = "\n\n=== Recent Conversation ===\n"
            for ctx in recent_context:
                context_prompt += f"User (turn {ctx['turn']}): {ctx['query']}\nMaple: {ctx['response']}\n\n"
        
        # 4. Retrieve documents + get response
        from services.rag_v2 import rag_search_v2

        retrieved_docs, score = await rag_search_v2(
            query,
            {
                "province": user.get("province"),
                "category": user.get("immigration_category")
            }
        )
        
        # Build system prompt with context
        system_with_context = SOVEREIGN_SYSTEM_PROMPT + context_prompt
        
        # Run LLM call off-thread so webhook workers stay responsive.
        response_text, tokens_used = await _anthropic_completion(system_with_context, query)
        
        # 5. Validate citations
        citation_ok, citation_msg = await citation_validator.enforce_or_reject(
            response_text,
            allow_uncited=False
        )
        if not citation_ok:
            logger.warning(f"Citation validation failed: {citation_msg}")
            response_text = f"{response_text}\n\n⚠️ Note: This response needs proper citations. Please visit maplejourney.ca for the full answer."
        
        # 6. Store turn
        await companion_memory.add_turn(
            session_id=session_id,
            user_id=str(user["_id"]),
            query=query,
            response=response_text,
            retrieved_docs=retrieved_docs,
            model_used="claude-3-5-sonnet-20241022",
            tokens_used=tokens_used,
        )
        
        # 7. Send response (split into chunks if > 1600 chars)
        chunks = [response_text[i:i+1600] for i in range(0, len(response_text), 1600)]
        for chunk in chunks:
            await send_message_by_channel(from_phone, chunk, channel)
        
        logger.info(f"{channel.upper()} response sent to {from_phone}")
        return {"ok": True, "session_id": session_id, "turns": session["turn_count"] + 1}
    
    except Exception as e:
        logger.exception(f"{channel.upper()} handler error")
        await send_message_by_channel(
            from_phone,
            "❌ Something went wrong. Please try again or visit maplejourney.ca",
            channel
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp-inbound")
async def handle_whatsapp_inbound(message: WhatsAppMessage, background_tasks: BackgroundTasks):
    """Process WhatsApp message from user via Twilio."""
    result = await _handle_companion_message(
        from_phone=message.from_phone,
        query=message.body.strip(),
        channel="whatsapp",
        message_sid=message.message_sid,
    )
    return result


@router.post("/imessage-inbound")
async def handle_imessage_inbound(message: iMessageMessage, background_tasks: BackgroundTasks):
    """Process iMessage message from user via Twilio SMS.
    
    iMessage messages arrive as SMS via Twilio.
    On iPhone, SMS with iCloud account displays as iMessage.
    On Android, displays as regular SMS.
    """
    result = await _handle_companion_message(
        from_phone=message.from_phone,
        query=message.body.strip(),
        channel="imessage",
        message_sid=message.message_sid,
    )
    return result


@router.post("/law-change")
async def handle_law_change_alert(alert: LawChangeAlert, background_tasks: BackgroundTasks):
    """Broadcast law change alert to relevant users.
    
    Called by law change monitor (background job).
    Finds users interested in affected categories and sends WhatsApp alert.
    """
    
    logger.info(f"Law change alert: {alert.title}")
    
    try:
        # Find users interested in affected categories
        query = {
            "phone_verified": True,
            "immigration_category": {"$in": alert.affected_categories}
        }
        
        users = await db.users.find(query).to_list(None)
        logger.info(f"Broadcasting to {len(users)} users")
        
        # Format alert message
        alert_message = f"""⚡ **Important Update**\n\n{alert.title}\n\nEffective: {alert.effective_date}\n\n{alert.summary}\n\n📖 Learn more: {alert.source_url}"""
        
        # Send to each user
        for user in users:
            phone = user.get("phone")
            if phone:
                try:
                    await send_whatsapp(phone, alert_message)
                except Exception as e:
                    logger.warning(f"Failed to send to {phone}: {str(e)}")
        
        return {"ok": True, "sent": len(users)}
    
    except Exception as e:
        logger.exception("Law change handler error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/law-change-monitor")
async def trigger_law_change_monitor(background_tasks: BackgroundTasks):
    """Trigger background job to check for new law changes.
    
    Called by cron job (e.g., every 6 hours).
    Polls IRCC RSS, compares with stored laws, dispatches alerts.
    """
    
    logger.info("Starting law change monitor...")
    
    try:
        # TODO: Implement law change detection
        # 1. Fetch IRCC RSS feed
        # 2. Extract new policies
        # 3. Compare with db.laws (last_checked timestamp)
        # 4. For each new law, call handle_law_change_alert()
        
        # Placeholder
        return {"ok": True, "checked": 0, "new": 0}
    
    except Exception as e:
        logger.exception("Law change monitor error")
        raise HTTPException(status_code=500, detail=str(e))


# Webhook verification (Twilio requires HMAC validation)
def verify_twilio_request(request: Request, body: bytes) -> bool:
    """Verify request is from Twilio."""
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    signature = request.headers.get("X-Twilio-Signature", "")

    try:
        decoded = body.decode("utf-8")
        params = {}
        for item in decoded.split("&"):
            if "=" in item:
                k, v = item.split("=", 1)
                params[k] = v
        return _validate_twilio_signature(_twilio_webhook_url(request), params, signature, auth_token)
    except Exception:
        return False


@router.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    """Twilio WhatsApp webhook (for incoming messages & status updates)."""
    
    body = await request.body()
    form_data = await request.form()
    params = {k: v for k, v in form_data.items()}

    # Verify Twilio signature
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    signature = request.headers.get("X-Twilio-Signature", "")
    if not _validate_twilio_signature(_twilio_webhook_url(request), params, signature, auth_token):
        logger.warning("Invalid Twilio signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    from_phone = form_data.get("From", "").replace("whatsapp:", "")
    body_text = form_data.get("Body", "")
    message_sid = form_data.get("MessageSid", "")
    num_media = int(form_data.get("NumMedia", 0))

    if not await _claim_inbound_message("whatsapp", message_sid):
        logger.info("Duplicate WhatsApp webhook ignored sid=%s", message_sid)
        return Response(content="", media_type="text/plain")
    
    if not body_text:
        return Response(content="", media_type="text/plain")
    
    # Process message
    message = WhatsAppMessage(
        from_phone=from_phone,
        body=body_text,
        message_sid=message_sid,
        num_media=num_media,
    )
    
    await handle_whatsapp_inbound(message, BackgroundTasks())
    
    # Return empty 200 OK to Twilio
    return Response(content="", media_type="text/plain")


@router.post("/imessage-webhook")
async def imessage_webhook(request: Request):
    """Twilio SMS webhook used as iMessage/SMS inbound channel."""

    body = await request.body()
    form_data = await request.form()
    params = {k: v for k, v in form_data.items()}

    # Verify Twilio signature
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    signature = request.headers.get("X-Twilio-Signature", "")
    if not _validate_twilio_signature(_twilio_webhook_url(request), params, signature, auth_token):
        logger.warning("Invalid Twilio signature")
        raise HTTPException(status_code=403, detail="Invalid signature")

    from_phone = (form_data.get("From", "") or "").strip()
    body_text = (form_data.get("Body", "") or "").strip()
    message_sid = (form_data.get("MessageSid", "") or "").strip()
    num_media = int(form_data.get("NumMedia", 0) or 0)

    if not await _claim_inbound_message("imessage", message_sid):
        logger.info("Duplicate iMessage webhook ignored sid=%s", message_sid)
        return Response(content="", media_type="text/plain")

    if not body_text:
        return Response(content="", media_type="text/plain")

    # Process message
    message = iMessageMessage(
        from_phone=from_phone,
        body=body_text,
        message_sid=message_sid,
        num_media=num_media,
    )

    await handle_imessage_inbound(message, BackgroundTasks())

    # Return empty 200 OK to Twilio
    return Response(content="", media_type="text/plain")
