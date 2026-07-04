"""Companion operations API.

Phase bundle:
- 2: Approval-required action framework
- 3: Proactive follow-up scheduler
- 4: Unified omnichannel session resolution
"""

import os
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from bson import ObjectId

from core.security import get_current_user
from services.companion_memory import CompanionMemory
from services.companion_ops import propose_action, list_actions, decide_action, schedule_followup, run_due_followups
from services.companion_proactive import CompanionProactiveActions
from services.companion_workflows import CompanionWorkflow
from services.companion_welcome import send_welcome_message
from services.credits import wallet_summary, action_cost, should_meter_tier, classify_query, auto_refill_daily
from core.db import db

router = APIRouter(tags=["companion-ops"])
companion_memory = CompanionMemory(db)
proactive = CompanionProactiveActions(db)
workflows = CompanionWorkflow(db)


def _json_safe(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


class ActionProposalIn(BaseModel):
    action_type: str
    title: str
    payload: dict = {}
    channel: str = "web"


class ActionDecisionIn(BaseModel):
    decision: str  # approve | reject
    note: str = ""


class FollowupIn(BaseModel):
    message: str
    minutes_from_now: int = 60
    channel: str = "whatsapp"
    metadata: dict = {}


@router.get("/companion/session")
async def companion_session(channel: str = Query(default="web"), user: dict = Depends(get_current_user)):
    session_id = await companion_memory.resolve_channel_session(str(user["_id"]), channel=channel)
    return {"session_id": session_id, "channel": channel}


@router.get("/companion/credits")
async def companion_credits(user: dict = Depends(get_current_user)):
    uid = str(user["_id"])
    tier = user.get("tier", "free")
    summary = await wallet_summary(uid, tier=tier)
    summary["metering_active"] = should_meter_tier(tier)
    summary["policy"] = "subscription-first: paid tiers are unlimited"
    return summary


@router.get("/companion/credits/classify")
async def companion_classify_query(message: str = Query(default=""), user: dict = Depends(get_current_user)):
    """Preview the credit cost for a message before sending it.

    Returns the complexity level and cost so the UI can show the user
    what a message will cost before they hit send.
    """
    complexity, cost = classify_query(message)
    uid = str(user["_id"])
    tier = user.get("tier", "free")
    metered = should_meter_tier(tier)

    balance = 0
    if metered:
        from services.credits import ensure_wallet
        wallet = await ensure_wallet(uid, tier=tier)
        balance = int(wallet.get("balance", 0))

    return {
        "complexity": complexity,
        "cost": cost,
        "balance": balance,
        "can_afford": (not metered) or (balance >= cost),
        "metered": metered,
    }


@router.get("/companion/credits/history")
async def companion_credit_history(limit: int = 50, user: dict = Depends(get_current_user)):
    rows = await db.credit_ledger.find({"user_id": str(user["_id"])}).sort("created_at", -1).to_list(min(200, max(1, limit)))
    for r in rows:
        r.pop("_id", None)
    return _json_safe(rows)


@router.post("/companion/actions/propose")
async def companion_propose_action(body: ActionProposalIn, user: dict = Depends(get_current_user)):
    from services.credits import debit_credits

    cost = action_cost(body.action_type)
    tier = user.get("tier", "free")
    debit = {"ok": True, "balance": None}
    if should_meter_tier(tier):
        debit = await debit_credits(
            user_id=str(user["_id"]),
            amount=cost,
            reason="companion-action-proposed",
            meta={"action_type": body.action_type, "channel": body.channel},
        )
        if not debit.get("ok"):
            raise HTTPException(status_code=402, detail={"error": "insufficient-credits", "needed": cost, "balance": debit.get("balance", 0)})

    doc = await propose_action(user, body.action_type, body.title, body.payload, channel=body.channel)
    return _json_safe({
        **doc,
        "credits_debited": cost if should_meter_tier(tier) else 0,
        "credits_balance": debit.get("balance"),
        "metering_active": should_meter_tier(tier),
    })


@router.get("/companion/actions")
async def companion_list_actions(status: str | None = None, limit: int = 50, user: dict = Depends(get_current_user)):
    rows = await list_actions(user, status=status, limit=min(200, max(1, limit)))
    return _json_safe(rows)


@router.post("/companion/actions/{action_id}/decision")
async def companion_decide_action(action_id: str, body: ActionDecisionIn, user: dict = Depends(get_current_user)):
    try:
        return await decide_action(user, action_id, body.decision, note=body.note)
    except KeyError:
        raise HTTPException(status_code=404, detail="Action not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== CHANNEL MANAGEMENT ==========
# Users can chat via Web (app), WhatsApp, SMS, or iMessage
# All channels share the same unified session and memory


@router.get("/companion/channels")
async def companion_channels(user: dict = Depends(get_current_user)):
    """Get user's enabled communication channels and session info.
    
    Returns:
        {
            "enabled_channels": ["web", "whatsapp", "imessage"],
            "sessions_by_channel": {
                "web": {...},
                "whatsapp": {...},
                "imessage": {...}
            },
            "unified_session": "session_id_shared_across_channels"
        }
    """
    user_id = str(user["_id"])
    enabled = user.get("enabled_channels", ["web"])
    
    # Get/create unified session (same for all channels)
    unified_session = await companion_memory.resolve_channel_session(user_id, channel="web")
    
    sessions = {}
    for channel in enabled:
        try:
            session = await companion_memory.resolve_channel_session(user_id, channel=channel)
            sessions[channel] = {
                "channel": channel,
                "session_id": session,
                "status": "connected",
            }
        except Exception as e:
            sessions[channel] = {
                "channel": channel,
                "status": "error",
                "error": str(e),
            }
    
    return {
        "enabled_channels": enabled,
        "sessions_by_channel": sessions,
        "unified_session": unified_session,
        "note": "All channels share the same conversation history and memory.",
    }


@router.post("/companion/channels/enable")
async def companion_enable_channel(channel: str = Query(...), user: dict = Depends(get_current_user)):
    """Enable a communication channel (whatsapp, imessage, sms).
    
    User must have verified phone number on file.
    """
    channel = (channel or "").strip().lower()
    valid_channels = ["whatsapp", "imessage", "sms", "web"]
    
    if channel not in valid_channels:
        raise HTTPException(status_code=400, detail=f"Invalid channel. Valid: {valid_channels}")
    
    user_id = user.get("_id")
    phone = user.get("phone")
    
    if channel != "web" and not phone:
        raise HTTPException(status_code=400, detail="Phone number required to enable messaging channels")
    
    # Add to enabled channels
    await db.users.update_one(
        {"_id": user_id},
        {
            "$addToSet": {"enabled_channels": channel},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    
    # Create/get session for this channel
    session_id = await companion_memory.resolve_channel_session(str(user_id), channel=channel)
    
    return {
        "status": "enabled",
        "channel": channel,
        "session_id": session_id,
        "message": f"✅ {channel.title()} channel enabled! Messages will be sent to {phone if phone else 'your app'}.",
    }


@router.post("/companion/channels/disable")
async def companion_disable_channel(channel: str = Query(...), user: dict = Depends(get_current_user)):
    """Disable a communication channel.
    
    Web channel cannot be disabled.
    """
    channel = (channel or "").strip().lower()
    
    if channel == "web":
        raise HTTPException(status_code=400, detail="Cannot disable web channel")
    
    await db.users.update_one(
        {"_id": user.get("_id")},
        {
            "$pull": {"enabled_channels": channel},
            "$set": {"updated_at": datetime.now(timezone.utc)},
        },
    )
    
    return {
        "status": "disabled",
        "channel": channel,
        "message": f"❌ {channel.title()} channel disabled.",
    }


@router.get("/companion/sessions")
async def companion_sessions(user: dict = Depends(get_current_user)):
    """Get all companion sessions for this user across all channels.
    
    Sessions are unified—each channel accesses the same conversation history.
    """
    user_id = str(user["_id"])
    
    sessions = await db.companion_sessions.find({
        "user_id": user_id
    }).sort("updated_at", -1).to_list(None)
    
    for session in sessions:
        session["_id"] = str(session["_id"])
        session["turn_count"] = session.get("turn_count", 0)
        session["channels"] = session.get("channels", ["web"])
    
    return {
        "sessions": _json_safe(sessions),
        "total": len(sessions),
        "note": "All channels share conversation history within each session.",
    }


@router.get("/companion/session-history")
async def companion_session_history(session_id: str = Query(...), limit: int = 50, user: dict = Depends(get_current_user)):
    """Get full conversation history for a session across all channels.
    
    Returns all turns (query + response pairs) in this session.
    """
    user_id = str(user["_id"])
    
    # Verify user owns this session
    session = await db.companion_sessions.find_one({
        "session_id": session_id,
        "user_id": user_id,
    })
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all turns
    turns = await db.companion_turns.find({
        "session_id": session_id,
        "user_id": user_id,
    }).sort("created_at", 1).to_list(min(500, max(1, limit)))
    
    return {
        "session_id": session_id,
        "user_id": user_id,
        "channels": session.get("channels", ["web"]),
        "turn_count": len(turns),
        "turns": _json_safe(turns),
        "note": "This conversation was accessed via: " + ", ".join(session.get("channels", ["web"])),
    }


@router.post("/companion/followups/schedule")
async def companion_schedule_followup(body: FollowupIn, user: dict = Depends(get_current_user)):
    from services.credits import debit_credits

    tier = user.get("tier", "free")
    debit = {"ok": True, "balance": None}
    if should_meter_tier(tier):
        debit = await debit_credits(
            user_id=str(user["_id"]),
            amount=1,
            reason="companion-followup-scheduled",
            meta={"channel": body.channel},
        )
        if not debit.get("ok"):
            raise HTTPException(status_code=402, detail={"error": "insufficient-credits", "needed": 1, "balance": debit.get("balance", 0)})

    due = datetime.now(timezone.utc) + timedelta(minutes=max(1, body.minutes_from_now))
    doc = await schedule_followup(
        user=user,
        message=body.message,
        due_at_iso=due.isoformat(),
        channel=body.channel,
        metadata=body.metadata,
    )
    return _json_safe({
        **doc,
        "credits_debited": 1 if should_meter_tier(tier) else 0,
        "credits_balance": debit.get("balance"),
        "metering_active": should_meter_tier(tier),
    })


@router.post("/companion/followups/run-due")
async def companion_run_due(limit: int = 100, internal_key: str = ""):
    # Internal/cron endpoint guard.
    required = os.environ.get("INTERNAL_CRON_KEY")
    if required and internal_key != required:
        raise HTTPException(status_code=403, detail="Forbidden")
    return await run_due_followups(limit=min(1000, max(1, limit)))


# ========== WELCOME MESSAGE ==========


@router.post("/companion/welcome/send")
async def companion_send_welcome(user: dict = Depends(get_current_user)):
    """Send/resend the welcome message to user's phone.
    
    Called when:
    1. User adds phone number after signup
    2. User wants to resend welcome message
    3. Admin resends for testing
    
    Returns:
        {
            "ok": bool,
            "message": str,
            "channel": str,
            "sent_to": str
        }
    """
    phone = user.get("phone", "").strip()
    if not phone:
        raise HTTPException(
            status_code=400,
            detail="Phone number required. Add it in your profile settings first."
        )
    
    user_id = user.get("_id")
    result = await send_welcome_message(user_id, phone)
    
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send welcome message"))
    
    return {
        "ok": True,
        "message": f"✅ Welcome message sent via {result.get('channel', 'messaging')}! Start chatting with Maple.",
        "channel": result.get("channel"),
        "sent_to": result.get("sent_to"),
        "session_id": result.get("session_id"),
    }


@router.get("/companion/welcome/status")
async def companion_welcome_status(user: dict = Depends(get_current_user)):
    """Check welcome message status for user.
    
    Returns:
        {
            "pending": bool,
            "sent": bool,
            "sent_at": str or null,
            "channel": str,
            "can_resend": bool
        }
    """
    pending = user.get("companion_welcome_pending", True)
    sent_at = user.get("companion_welcome_sent_at")
    channel = user.get("companion_welcome_channel", "")
    phone = user.get("phone", "").strip()
    
    return {
        "pending": pending,
        "sent": bool(sent_at),
        "sent_at": sent_at,
        "channel": channel,
        "can_resend": bool(phone),
        "phone": phone if phone else None,
        "note": "If you haven't received the welcome message, check your phone's message filters or spam folder.",
    }
