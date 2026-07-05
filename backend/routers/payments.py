"""Stripe checkout for paid tiers (Plus / Family). Prices are defined
server-side only; the client never sends an amount. Payment state is tracked
in the payment_transactions collection and reconciled via polling + webhook."""
import os
import logging
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from fastapi import APIRouter, Depends, Request, HTTPException

from core.db import db
from core.config import PLAN_CATALOG, PLAN_PRICES
from core.security import get_current_user
from models import CheckoutIn
from services.email_service import send_email_safe
from services.credits import grant_tier_pack, ensure_wallet

logger = logging.getLogger("maplejourney.payments")
router = APIRouter(tags=["payments"])

TIER_DAYS = 30  # one checkout grants ~1 month of access (MVP, no recurring).


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _frontend_base_url(fallback_origin: str = "") -> str:
    configured = (
        os.environ.get("PUBLIC_APP_URL")
        or os.environ.get("FRONTEND_APP_URL")
        or os.environ.get("APP_BASE_URL")
        or fallback_origin
    )
    configured = (configured or "").strip().rstrip("/")
    if not configured:
        raise HTTPException(status_code=503, detail="Frontend app URL is not configured")
    return configured


def _checkout(webhook_url: str):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    api_key = os.environ.get("STRIPE_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")
    return StripeCheckout(api_key=api_key, webhook_url=webhook_url)


async def _grant_tier(session_id: str):
    """Idempotently upgrade the user's tier for a paid session."""
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn or txn.get("granted"):
        return
    expires = (datetime.now(timezone.utc) + timedelta(days=TIER_DAYS)).isoformat()
    await db.users.update_one({"_id": ObjectId(txn["user_id"])}, {"$set": {"tier": txn["plan_id"], "tier_expires_at": expires}})
    await ensure_wallet(txn["user_id"], tier=txn["plan_id"])
    await grant_tier_pack(txn["user_id"], tier=txn["plan_id"])
    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": {"granted": True, "granted_at": _now_iso()}})
    logger.info(
        "stripe tier granted session_id=%s user_id=%s plan_id=%s expires_at=%s",
        session_id,
        txn["user_id"],
        txn["plan_id"],
        expires,
    )
    # Send a branded receipt / upgrade confirmation (never blocks the grant).
    user = await db.users.find_one({"_id": ObjectId(txn["user_id"])})
    if user and user.get("email"):
        plan_name = next((p["name"] for p in PLAN_CATALOG if p["id"] == txn["plan_id"]), str(txn["plan_id"]).title())
        amount = f"${float(txn.get('amount', 0)):.2f} {str(txn.get('currency', 'usd')).upper()}"
        await send_email_safe(user["email"], "payment_confirmation", name=user.get("name", ""),
                              plan_name=plan_name, amount=amount, expires=expires[:10])


@router.get("/plans")
async def list_plans():
    return PLAN_CATALOG


@router.get("/billing/history")
async def billing_history(user: dict = Depends(get_current_user)):
    items = await db.payment_transactions.find({"user_id": str(user["_id"])}).sort("created_at", -1).to_list(50)
    return [
        {"plan_id": i.get("plan_id"), "amount": i.get("amount"), "currency": i.get("currency"),
         "status": i.get("payment_status"), "created_at": i.get("created_at")}
        for i in items
    ]


@router.post("/checkout/session")
async def create_checkout_session(body: CheckoutIn, request: Request, user: dict = Depends(get_current_user)):
    plan_id = body.plan_id
    if plan_id not in PLAN_PRICES or plan_id == "free":
        raise HTTPException(status_code=400, detail="Invalid plan")

    amount = float(PLAN_PRICES[plan_id])  # server-side price only
    api_base = str(request.base_url).rstrip("/")
    app_base = _frontend_base_url(body.origin_url)
    webhook_url = f"{api_base}/api/webhook/stripe"
    success_url = f"{app_base}/app/plans?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{app_base}/app/plans"
    metadata = {"user_id": str(user["_id"]), "plan_id": plan_id, "source": "app_upgrade"}

    from emergentintegrations.payments.stripe.checkout import CheckoutSessionRequest
    checkout = _checkout(webhook_url)
    req = CheckoutSessionRequest(amount=amount, currency="usd", success_url=success_url, cancel_url=cancel_url, metadata=metadata)
    session = await checkout.create_checkout_session(req)

    logger.info(
        "stripe checkout created session_id=%s user_id=%s plan_id=%s amount=%s currency=usd app_base=%s",
        session.session_id,
        str(user["_id"]),
        plan_id,
        amount,
        app_base,
    )

    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "user_id": str(user["_id"]),
        "plan_id": plan_id,
        "amount": amount,
        "currency": "usd",
        "status": "initiated",
        "payment_status": "initiated",
        "granted": False,
        "metadata": metadata,
        "created_at": _now_iso(),
    })
    return {"url": session.url, "session_id": session.session_id}


@router.get("/checkout/status/{session_id}")
async def checkout_status(session_id: str, request: Request, user: dict = Depends(get_current_user)):
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Unknown checkout session")
    if txn.get("user_id") != str(user["_id"]):
        raise HTTPException(status_code=403, detail="This checkout session does not belong to you")

    host = str(request.base_url).rstrip("/")
    checkout = _checkout(f"{host}/api/webhook/stripe")
    status = await checkout.get_checkout_status(session_id)

    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": status.status, "payment_status": status.payment_status, "updated_at": _now_iso()}},
    )
    if status.payment_status == "paid":
        await _grant_tier(session_id)

    logger.info(
        "stripe checkout status session_id=%s user_id=%s status=%s payment_status=%s",
        session_id,
        str(user["_id"]),
        status.status,
        status.payment_status,
    )

    return {"status": status.status, "payment_status": status.payment_status, "plan_id": txn["plan_id"]}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature")
    host = str(request.base_url).rstrip("/")
    try:
        checkout = _checkout(f"{host}/api/webhook/stripe")
        resp = await checkout.handle_webhook(body, sig)
    except Exception:
        logger.exception("stripe webhook error")
        return {"received": True}

    if getattr(resp, "payment_status", None) == "paid" and getattr(resp, "session_id", None):
        await db.payment_transactions.update_one(
            {"session_id": resp.session_id},
            {"$set": {"payment_status": "paid", "status": "complete", "updated_at": _now_iso()}},
        )
        logger.info("stripe webhook paid session_id=%s", resp.session_id)
        await _grant_tier(resp.session_id)
    return {"received": True}
