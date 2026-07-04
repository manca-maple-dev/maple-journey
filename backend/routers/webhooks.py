"""Off-App Bridge: WhatsApp and iMessage webhook endpoints.

Links incoming phone messages to the user's session_id and profile,
enabling Maple's sovereign intelligence to operate beyond the web app.
Implements the 'Off-App Bridge' pattern from the getwingman system.
"""
import os
import uuid
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from core.db import db
from core.config import SOVEREIGN_SYSTEM_PROMPT
from services.companion_memory import CompanionMemory
from services.profile import profile_summary, conversation_language, conversation_language_instruction
from services.rag import rag_search, enforce_citation_policy, grounded_fallback_response
from services.wings import companion_welcome_message

logger = logging.getLogger("maplejourney.webhooks")
router = APIRouter(prefix="/webhook", tags=["webhooks"])
companion_memory = CompanionMemory(db)

COMPANION_DAILY_LIMITS = {
    "free": 20,
    "plus": 50,
    "family": None,
}

IRPA_DISCLOSURE = (
    "Maple Journey provides cited information only, not legal representation or case-specific legal advice. "
    "For representation, use a regulated professional: https://laws-lois.justice.gc.ca/eng/acts/i-2.5/section-91.html"
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class WhatsAppInbound(BaseModel):
    """Parsed WhatsApp inbound message (Twilio format)."""
    from_phone: str
    body: str
    message_sid: Optional[str] = None


class IMessageInbound(BaseModel):
    """Parsed iMessage inbound (via relay service)."""
    sender_id: str  # Phone number or Apple ID
    body: str
    timestamp: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _resolve_user_by_phone(phone: str) -> Optional[dict]:
    """Look up a verified user by phone number."""
    normalized = phone.strip().replace(" ", "").replace("-", "")
    if not normalized.startswith("+"):
        normalized = "+" + normalized
    user = await db.users.find_one({"phone": normalized, "phone_verified": True})
    return user


def _companion_opted_in(user: dict) -> bool:
    profile = user.get("profile") or {}
    return bool(profile.get("consent_maple_companion") or user.get("consent_maple_companion"))


async def _messages_used_today(user: dict) -> int:
    uid = str(user["_id"])
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    return await db.chat_messages.count_documents(
        {
            "user_id": uid,
            "channel": {"$in": ["whatsapp", "imessage"]},
            "role": "user",
            "created_at": {"$gte": start_of_day},
        }
    )


async def _is_first_off_app_turn(session_id: str) -> bool:
    prior = await db.chat_messages.count_documents({"session_id": session_id, "role": "assistant", "channel": {"$in": ["whatsapp", "imessage"]}})
    return prior == 0


async def _log_companion_event(session_id: str, user_msg: str, ai_msg: str, channel: str):
    turn_index = await db.companion_events.count_documents({"session_id": session_id}) + 1
    now = datetime.now(timezone.utc).isoformat()
    msg_hash = hashlib.sha256(user_msg.encode("utf-8")).hexdigest() if user_msg else None
    cited = "[Source:" in (ai_msg or "")
    await db.companion_events.insert_one(
        {
            "session_id": session_id,
            "channel": channel,
            "turn_index": turn_index,
            "user_message_hash": msg_hash,
            "response_cited": cited,
            "user_follow_up": turn_index > 1,
            "timestamp": now,
        }
    )


async def _get_or_create_session(user: dict, channel: str) -> str:
    """Resolve unified companion session id across web/off-app channels."""
    return await companion_memory.resolve_channel_session(str(user["_id"]), channel=channel)


def _offline_companion_reply(message: str, user: dict, channel: str, rag_context: str) -> str:
    """Deterministic off-app reply used when OpenAI is unavailable.

    Keeps WhatsApp/iMessage usable before any provider keys are approved.
    """
    first_name = (user.get("name") or "there").split(" ")[0]
    permit = user.get("visa_type") or user.get("newcomer_type") or "your situation"
    city = (user.get("profile") or {}).get("city") or user.get("city") or "Canada"
    has_source = "[Source:" in rag_context
    language = conversation_language(user)
    if language == "French":
        opener = f"Salut {first_name}. Je suis Maple sur {channel}."
        if has_source:
            return (
                f"{opener} Je peux t’aider avec ta question sur {permit} à {city}. "
                "Voici l’étape la plus sûre: regarde les étapes officielles que j’ai jointes, rassemble les documents requis "
                "et envoie avant la date limite. Si tu veux, donne-moi un détail de plus et je vais préciser."
            )
        return (
            f"{opener} Je peux t’aider avec ta question sur {permit} à {city}. "
            "Je n’ai pas encore assez de détails vérifiés, donc l’étape la plus sûre est de vérifier la page IRCC officielle, "
            "confirmer ta date limite, puis m’envoyer le nom exact du permis ou du programme."
        )
    opener = f"Hi {first_name}. I’m Maple on {channel}."
    if has_source:
        return (
            f"{opener} I can help with your {permit} question in {city}. "
            "Here is the safest next move: review the official steps I attached, gather the required documents, "
            "and submit before any deadline. If you want, send me one more detail and I will narrow it down."
        )
    return (
        f"{opener} I can help with your {permit} question in {city}. "
        "I do not have enough verified source detail yet, so the safest next move is to check the official IRCC page, "
        "confirm your deadline, and send me the exact permit or program name for a tighter answer."
    )


async def _generate_maple_response(message: str, user: dict, session_id: str, channel: str) -> str:
    """Generate a RAG-grounded Maple response for off-app channels.
    
    Maintains sovereign authority even outside the web app.
    """
    # RAG retrieval
    rag_context = await rag_search(message, user)
    memory_context = await companion_memory.build_memory_brief(session_id)

    # Build system prompt with profile + RAG
    system = (
        SOVEREIGN_SYSTEM_PROMPT
        + profile_summary(user)
        + memory_context
        + rag_context
        + f"\n\nChannel: {channel}. Keep responses under 1500 characters for mobile readability. "
        "Maintain full sovereign authority and citation standards even in brief responses."
    )
    system += conversation_language_instruction(user)

    try:
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            reply_text = _offline_companion_reply(message, user, channel, rag_context)
            reply_text = f"{IRPA_DISCLOSURE}\n\n{reply_text}" if "[Source:" in rag_context else reply_text
            return reply_text

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=openai_key)
        model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1")
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message},
            ],
            temperature=0.3,
            max_tokens=500,
            top_p=0.9,
        )
        reply_text = (resp.choices[0].message.content or "").strip()
        if not reply_text:
            reply_text = _offline_companion_reply(message, user, channel, rag_context)
        reply_text, compliant, reason = enforce_citation_policy(reply_text)
        if not compliant:
            logger.warning("off-app citation policy fallback applied: user=%s channel=%s reason=%s", str(user.get("_id")), channel, reason)
        return reply_text
    except Exception:
        logger.exception("Off-app AI generation failed (channel=%s)", channel)
        reply_text = _offline_companion_reply(message, user, channel, rag_context)
        reply_text = f"{IRPA_DISCLOSURE}\n\n{reply_text}" if "[Source:" in rag_context else reply_text
        return reply_text


def _with_first_welcome(user: dict, channel: str, reply: str) -> tuple[str, bool]:
    """Add the first Maple welcome once, then keep later replies concise."""
    if user.get("companion_welcome_sent_at"):
        return reply, False
    welcome = companion_welcome_message(user, channel)
    return f"{welcome}\n\n{reply}", True


async def _persist_messages(uid: str, session_id: str, user_msg: str, ai_msg: str, channel: str):
    """Persist both user and assistant messages with channel metadata."""
    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {
            "id": str(uuid.uuid4()),
            "user_id": uid,
            "session_id": session_id,
            "role": "user",
            "content": user_msg,
            "created_at": now,
            "channel": channel,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": uid,
            "session_id": session_id,
            "role": "assistant",
            "content": ai_msg,
            "created_at": now,
            "channel": channel,
        },
    ]
    await db.chat_messages.insert_many(docs)
    await _log_companion_event(session_id, user_msg, ai_msg, channel)


# ---------------------------------------------------------------------------
# WhatsApp Webhook (Twilio)
# ---------------------------------------------------------------------------
@router.post("/whatsapp")
async def webhook_whatsapp(request: Request):
    """Inbound WhatsApp message -> Maple sovereign AI -> Twilio TwiML reply.
    
    Validates Twilio signature, resolves user by phone, generates RAG-grounded
    response, and persists the conversation linked to the user's profile.
    """
    from twilio.twiml.messaging_response import MessagingResponse
    from twilio.request_validator import RequestValidator

    form = await request.form()
    params = {k: v for k, v in form.items()}

    # Validate Twilio signature
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if auth_token:
        base = os.environ.get("WEBHOOK_BASE_URL")
        if base:
            url = base.rstrip("/") + "/api/webhook/whatsapp"
        else:
            proto = request.headers.get("x-forwarded-proto", "https")
            host = request.headers.get("host", "")
            url = f"{proto}://{host}{request.url.path}"
        signature = request.headers.get("X-Twilio-Signature", "")
        valid = RequestValidator(auth_token).validate(url, params, signature)
        if not valid:
            logger.warning("Rejected WhatsApp webhook: invalid Twilio signature (url=%s)", url)
            return Response(content="Forbidden", status_code=403)

    body_text = (params.get("Body") or "").strip()
    phone = (params.get("From") or "").replace("whatsapp:", "").strip()

    resp = MessagingResponse()

    # Resolve user
    user = await _resolve_user_by_phone(phone)
    if not user:
        resp.message(
            "Welcome to Maple, the Newcomers in Canada Wingman. "
            "To connect your account, verify this phone number in the app: "
            "Settings → Phone Verification. Once verified, I can assist you here "
            "with cited, authoritative immigration guidance."
        )
        return Response(content=str(resp), media_type="application/xml")

    if not _companion_opted_in(user):
        resp.message(
            "You're connected, but proactive Maple companion is currently off for your account. "
            "Enable it in Profile → Consents (\"Let Maple proactively check in\") to continue here."
        )
        return Response(content=str(resp), media_type="application/xml")

    tier = user.get("tier", "free")
    limit = COMPANION_DAILY_LIMITS.get(tier, COMPANION_DAILY_LIMITS["free"])
    used = await _messages_used_today(user)
    if limit is not None and used >= limit:
        resp.message(
            f"You've reached today's Maple companion limit ({limit}) for your current plan. "
            "You can continue tomorrow, or upgrade to increase your daily limit."
        )
        return Response(content=str(resp), media_type="application/xml")

    # Generate response
    session_id = await _get_or_create_session(user, "whatsapp")
    reply = await _generate_maple_response(body_text or "Hello", user, session_id, "whatsapp")
    reply, welcomed = _with_first_welcome(user, "WhatsApp", reply)
    if await _is_first_off_app_turn(session_id):
        reply = f"{IRPA_DISCLOSURE}\n\n{reply}"

    # Persist
    await _persist_messages(str(user["_id"]), session_id, body_text, reply, "whatsapp")
    try:
        await companion_memory.add_turn(
            session_id=session_id,
            user_id=str(user["_id"]),
            query=body_text,
            response=reply,
            retrieved_docs=[],
            model_used=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1"),
        )
    except Exception:
        logger.exception("failed to store off-app memory turn")
    if welcomed:
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"companion_welcome_pending": False, "companion_welcome_sent_at": datetime.now(timezone.utc).isoformat(), "companion_welcome_channel": "whatsapp"}})

    resp.message(reply)
    return Response(content=str(resp), media_type="application/xml")


# ---------------------------------------------------------------------------
# iMessage Webhook (via relay/bridge service)
# ---------------------------------------------------------------------------
@router.post("/imessage")
async def webhook_imessage(request: Request):
    """Inbound iMessage -> Maple sovereign AI -> JSON reply for relay service.
    
    Validates HMAC signature from the iMessage relay, resolves user by
    Apple ID or phone, generates RAG-grounded response, and returns JSON.
    The relay service is responsible for delivering the reply back to iMessage.
    """
    # Validate HMAC signature from relay service
    imessage_secret = os.environ.get("IMESSAGE_WEBHOOK_SECRET")
    if imessage_secret:
        signature = request.headers.get("X-Maple-Signature", "")
        body_bytes = await request.body()
        expected = hmac.new(
            imessage_secret.encode(), body_bytes, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            logger.warning("Rejected iMessage webhook: invalid HMAC signature")
            raise HTTPException(status_code=403, detail="Invalid signature")
        import json
        payload = json.loads(body_bytes)
    else:
        payload = await request.json()

    sender_id = (payload.get("sender_id") or payload.get("from") or "").strip()
    body_text = (payload.get("body") or payload.get("text") or "").strip()

    if not sender_id or not body_text:
        raise HTTPException(status_code=400, detail="Missing sender_id or body")

    # Resolve user by phone or Apple ID
    user = await _resolve_user_by_phone(sender_id)
    if not user:
        # Try lookup by email (Apple ID is often an email)
        user = await db.users.find_one({"email": sender_id.lower()})

    if not user:
        return {
            "status": "unlinked",
            "reply": (
                "I'm Maple, the Newcomers in Canada Wingman. To access personalized, "
                "cited immigration guidance here, please link your account in the app: "
                "Settings → Phone Verification."
            ),
            "session_id": None,
        }

    if not _companion_opted_in(user):
        return {
            "status": "consent-required",
            "reply": (
                "Your Maple companion consent is currently off. Enable it in Profile → Consents "
                "(\"Let Maple proactively check in\") to continue on iMessage."
            ),
            "session_id": None,
        }

    tier = user.get("tier", "free")
    limit = COMPANION_DAILY_LIMITS.get(tier, COMPANION_DAILY_LIMITS["free"])
    used = await _messages_used_today(user)
    if limit is not None and used >= limit:
        return {
            "status": "limit-reached",
            "reply": (
                f"You've reached today's Maple companion limit ({limit}) for your current plan. "
                "You can continue tomorrow, or upgrade to increase your daily limit."
            ),
            "session_id": None,
        }

    # Generate response
    session_id = await _get_or_create_session(user, "imessage")
    reply = await _generate_maple_response(body_text, user, session_id, "imessage")
    reply, welcomed = _with_first_welcome(user, "iMessage", reply)
    if await _is_first_off_app_turn(session_id):
        reply = f"{IRPA_DISCLOSURE}\n\n{reply}"

    # Persist
    await _persist_messages(str(user["_id"]), session_id, body_text, reply, "imessage")
    try:
        await companion_memory.add_turn(
            session_id=session_id,
            user_id=str(user["_id"]),
            query=body_text,
            response=reply,
            retrieved_docs=[],
            model_used=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1"),
        )
    except Exception:
        logger.exception("failed to store off-app memory turn")
    if welcomed:
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"companion_welcome_pending": False, "companion_welcome_sent_at": datetime.now(timezone.utc).isoformat(), "companion_welcome_channel": "imessage"}})

    return {
        "status": "ok",
        "reply": reply,
        "session_id": session_id,
        "user_id": str(user["_id"]),
    }


# ---------------------------------------------------------------------------
# Health / Status
# ---------------------------------------------------------------------------
@router.get("/status")
async def webhook_status():
    """Health check for webhook endpoints."""
    return {
        "status": "operational",
        "channels": ["whatsapp", "imessage"],
        "engine": "Maple Sovereign Intelligence",
        "version": "2.0",
    }
