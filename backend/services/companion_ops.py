"""Companion operations: approval-gated actions and proactive follow-ups.

Implements Wingman-style execution control:
- Propose actions that require explicit user approval
- Approve/reject actions with auditable status transitions
- Schedule proactive follow-ups and run due notifications
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from bson import ObjectId

from core.db import db
from services.twilio_service import send_whatsapp

ACTION_STATUSES = {"pending", "approved", "rejected", "executed", "failed", "cancelled"}
FOLLOWUP_STATUSES = {"scheduled", "sent", "cancelled", "failed"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def propose_action(user: dict, action_type: str, title: str, payload: dict, channel: str = "web") -> dict:
    doc = {
        "id": str(uuid4()),
        "user_id": str(user["_id"]),
        "action_type": action_type,
        "title": title,
        "payload": payload or {},
        "channel": channel,
        "status": "pending",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.companion_actions.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def list_actions(user: dict, status: Optional[str] = None, limit: int = 50) -> list[dict]:
    q = {"user_id": str(user["_id"])}
    if status:
        q["status"] = status
    items = await db.companion_actions.find(q).sort("created_at", -1).to_list(limit)
    for i in items:
        i.pop("_id", None)
    return items


async def decide_action(user: dict, action_id: str, decision: str, note: Optional[str] = None) -> dict:
    if decision not in ("approve", "reject"):
        raise ValueError("decision must be 'approve' or 'reject'")

    action = await db.companion_actions.find_one({"id": action_id, "user_id": str(user["_id"])})
    if not action:
        raise KeyError("action-not-found")
    if action.get("status") != "pending":
        raise ValueError("action-not-pending")

    status = "approved" if decision == "approve" else "rejected"
    update = {
        "status": status,
        "decision_note": note or "",
        "decided_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.companion_actions.update_one({"id": action_id}, {"$set": update})

    if status == "approved":
        # Placeholder executor: mark executed immediately for safe, non-destructive rollout.
        await db.companion_actions.update_one(
            {"id": action_id},
            {"$set": {"status": "executed", "executed_at": _now_iso(), "updated_at": _now_iso()}},
        )
        update["status"] = "executed"

    return {"id": action_id, **update}


async def schedule_followup(
    user: dict,
    message: str,
    due_at_iso: str,
    channel: str = "whatsapp",
    metadata: Optional[dict] = None,
) -> dict:
    doc = {
        "id": str(uuid4()),
        "user_id": str(user["_id"]),
        "channel": channel,
        "message": message,
        "due_at": due_at_iso,
        "status": "scheduled",
        "metadata": metadata or {},
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.companion_followups.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def run_due_followups(limit: int = 100) -> dict:
    now_iso = _now_iso()
    due = await db.companion_followups.find(
        {"status": "scheduled", "due_at": {"$lte": now_iso}}
    ).sort("due_at", 1).to_list(limit)

    sent = 0
    failed = 0
    for item in due:
        try:
            if item.get("channel") == "whatsapp":
                user_doc = None
                try:
                    user_doc = await db.users.find_one({"_id": ObjectId(item.get("user_id"))})
                except Exception:
                    user_doc = None
                phone = (user_doc or {}).get("phone")
                if phone:
                    await send_whatsapp(phone, item.get("message", ""))
            await db.companion_followups.update_one(
                {"id": item.get("id")},
                {"$set": {"status": "sent", "sent_at": _now_iso(), "updated_at": _now_iso()}},
            )
            sent += 1
        except Exception:
            failed += 1
            await db.companion_followups.update_one(
                {"id": item.get("id")},
                {"$set": {"status": "failed", "updated_at": _now_iso()}},
            )

    return {"checked": len(due), "sent": sent, "failed": failed}
