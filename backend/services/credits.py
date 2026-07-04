"""Intelligent Credits System for Maple Chat.

Replaces the blunt daily-message-counter with a nuanced credit economy:
- Per-user wallet with daily auto-regeneration
- Query complexity classifier (1–5 credits based on message depth)
- Atomic debit with insufficient-funds gate
- Full ledger for auditability and upsell analytics
- Tier credit grants (signup/upgrade/daily refill)
- Smart upsell moments: surface upgrade nudge at low-balance
"""

import re
from datetime import datetime, timezone, date
from uuid import uuid4

from pymongo import ReturnDocument

from core.db import db

# ---------------------------------------------------------------------------
# Tier credit economy
# ---------------------------------------------------------------------------
TIER_STARTER_CREDITS = {
    "free": 10,
    "plus": 100,
    "family": 275,
}

# Daily regeneration for metered tiers (credits added per day at first message)
TIER_DAILY_CREDITS = {
    "free": 10,      # 10 credits/day — enough for ~5–10 standard questions
    "plus": 150,     # 150/day — effectively unlimited for normal use
    "family": 300,
}

ACTION_CREDIT_COSTS = {
    "message": 1,
    "quick_task": 1,
    "followup": 1,
    "research_task": 3,
    "workflow": 5,
}

# Complexity tiers for chat messages
CHAT_COMPLEXITY_COSTS = {
    "simple": 1,      # Greetings, yes/no, status checks
    "standard": 2,    # Single-topic immigration question
    "research": 3,    # Multi-step, comparisons, timelines
    "deep": 5,        # Full case analysis, CRS calc, document review
}

# Only free tier is metered — paid tiers bypass credit checks
METERED_TIERS = {"free"}

# Regex patterns to classify query complexity (checked in order)
_SIMPLE_PATTERNS = re.compile(
    r"^(hi|hello|hey|thanks|thank you|ok|okay|yes|no|sure|got it|understood|great|\?+)$",
    re.IGNORECASE,
)
_DEEP_PATTERNS = re.compile(
    r"(calculate|full analysis|step.by.step|all documents|complete checklist|case review|"
    r"crs score|points breakdown|compare.*pathway|which.*better|should i|strategy|"
    r"appeal|inadmissib|misrepresent|refused|criminal|medical|sponsor|divorce|custody)",
    re.IGNORECASE,
)
_RESEARCH_PATTERNS = re.compile(
    r"(how long|processing time|timeline|deadline|expire|renewal|extension|eligible|"
    r"requirement|pathway|program|provincial|pnp|express entry|pgwp|lmia|bowp|"
    r"explain|difference between|what is|what are|can i|am i|do i need)",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def action_cost(action_type: str) -> int:
    return max(1, ACTION_CREDIT_COSTS.get((action_type or "").strip().lower(), 1))


def should_meter_tier(tier: str) -> bool:
    return (tier or "free") in METERED_TIERS


# ---------------------------------------------------------------------------
# Intelligent query complexity classifier
# ---------------------------------------------------------------------------
def classify_query(message: str) -> tuple[str, int]:
    """Classify a chat message and return (complexity_label, credit_cost).

    Levels:
      simple   (1 credit)  — greetings, one-word answers, confirmations
      standard (2 credits) — single-topic immigration question
      research (3 credits) — multi-step, eligibility check, timeline
      deep     (5 credits) — full case analysis, strategy, CRS calculation
    """
    text = (message or "").strip()
    if not text:
        return "simple", 1

    # Very short or greeting
    if len(text) < 20 or _SIMPLE_PATTERNS.match(text):
        return "simple", CHAT_COMPLEXITY_COSTS["simple"]

    # Deep analysis indicators
    if _DEEP_PATTERNS.search(text):
        return "deep", CHAT_COMPLEXITY_COSTS["deep"]

    # Research / multi-step
    if _RESEARCH_PATTERNS.search(text) or len(text) > 120:
        return "research", CHAT_COMPLEXITY_COSTS["research"]

    return "standard", CHAT_COMPLEXITY_COSTS["standard"]


async def ensure_wallet(user_id: str, tier: str = "free") -> dict:
    starter = TIER_STARTER_CREDITS.get(tier, TIER_STARTER_CREDITS["free"])
    existing = await db.credit_wallets.find_one({"user_id": user_id})
    if existing:
        return existing
    today = date.today().isoformat()
    doc = {
        "id": str(uuid4()),
        "user_id": user_id,
        "balance": starter,
        "lifetime_earned": starter,
        "lifetime_spent": 0,
        "tier": tier,
        "last_daily_refill": today,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.credit_wallets.insert_one(doc)
    await db.credit_ledger.insert_one(
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "kind": "grant",
            "amount": starter,
            "reason": "signup-starter",
            "meta": {"tier": tier},
            "created_at": _now_iso(),
        }
    )
    return doc


async def auto_refill_daily(user_id: str, tier: str) -> int:
    """Top up free-tier wallet once per calendar day. Returns credits granted (0 if already done today)."""
    if not should_meter_tier(tier):
        return 0

    today = date.today().isoformat()
    daily_amount = TIER_DAILY_CREDITS.get(tier, TIER_DAILY_CREDITS["free"])

    # Atomic: only update if last_daily_refill != today
    updated = await db.credit_wallets.find_one_and_update(
        {"user_id": user_id, "last_daily_refill": {"$ne": today}},
        {
            "$inc": {"balance": daily_amount, "lifetime_earned": daily_amount},
            "$set": {"last_daily_refill": today, "updated_at": _now_iso()},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        return 0  # Already refilled today

    await db.credit_ledger.insert_one(
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "kind": "grant",
            "amount": daily_amount,
            "reason": "daily-refill",
            "meta": {"tier": tier, "date": today},
            "created_at": _now_iso(),
        }
    )
    return daily_amount


def upsell_nudge(balance: int, cost: int, tier: str) -> str | None:
    """Return an upgrade nudge string when balance is critically low, or None."""
    if not should_meter_tier(tier):
        return None
    remaining_after = balance - cost
    if remaining_after <= 0:
        return (
            "\n\n---\n🍁 **You've used all your daily Maple credits.** "
            "Upgrade to **Plus** for 150 credits/day, unlimited deep research, and priority answers. "
            "Tap **Upgrade** in your dashboard."
        )
    if remaining_after <= 2:
        return (
            f"\n\n---\n🍁 You have **{remaining_after} credit{'s' if remaining_after != 1 else ''}** remaining today. "
            "Upgrade to **Plus** for 150 credits/day and unlimited deep analysis."
        )
    return None


async def wallet_summary(user_id: str, tier: str = "free") -> dict:
    w = await ensure_wallet(user_id, tier=tier)
    refilled = await auto_refill_daily(user_id, tier)
    if refilled:
        w = await db.credit_wallets.find_one({"user_id": user_id})
    return {
        "balance": int(w.get("balance", 0)),
        "tier": w.get("tier", tier),
        "lifetime_earned": int(w.get("lifetime_earned", 0)),
        "lifetime_spent": int(w.get("lifetime_spent", 0)),
        "daily_limit": TIER_DAILY_CREDITS.get(tier),
        "last_daily_refill": w.get("last_daily_refill"),
        "refilled_today": refilled,
    }


async def debit_credits(user_id: str, amount: int, reason: str, meta: dict | None = None) -> dict:
    amount = max(1, int(amount))
    updated = await db.credit_wallets.find_one_and_update(
        {"user_id": user_id, "balance": {"$gte": amount}},
        {
            "$inc": {"balance": -amount, "lifetime_spent": amount},
            "$set": {"updated_at": _now_iso()},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        current = await db.credit_wallets.find_one({"user_id": user_id}) or {}
        return {
            "ok": False,
            "balance": int(current.get("balance", 0)),
            "needed": amount,
            "reason": "insufficient-credits",
        }

    await db.credit_ledger.insert_one(
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "kind": "debit",
            "amount": amount,
            "reason": reason,
            "meta": meta or {},
            "created_at": _now_iso(),
        }
    )
    return {"ok": True, "balance": int(updated.get("balance", 0)), "debited": amount}


async def grant_credits(user_id: str, amount: int, reason: str, meta: dict | None = None) -> dict:
    amount = max(1, int(amount))
    updated = await db.credit_wallets.find_one_and_update(
        {"user_id": user_id},
        {
            "$inc": {"balance": amount, "lifetime_earned": amount},
            "$set": {"updated_at": _now_iso()},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        await ensure_wallet(user_id)
        return await grant_credits(user_id, amount, reason, meta)

    await db.credit_ledger.insert_one(
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "kind": "grant",
            "amount": amount,
            "reason": reason,
            "meta": meta or {},
            "created_at": _now_iso(),
        }
    )
    return {"ok": True, "balance": int(updated.get("balance", 0)), "granted": amount}


async def grant_tier_pack(user_id: str, tier: str) -> dict:
    pack = TIER_STARTER_CREDITS.get(tier, 0)
    if pack <= 0:
        return {"ok": True, "balance": 0, "granted": 0}
    return await grant_credits(user_id, pack, reason="tier-pack-grant", meta={"tier": tier})


async def ensure_indexes() -> None:
    await db.credit_wallets.create_index("user_id", unique=True)
    await db.credit_ledger.create_index("user_id")
    await db.credit_ledger.create_index([("created_at", -1)])
