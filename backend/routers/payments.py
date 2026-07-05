"""Stripe checkout for paid tiers (Plus / Family). Prices are defined
server-side only; the client never sends an amount. Payment state is tracked
in the payment_transactions collection and reconciled via polling + webhook."""
import os
import logging
import json
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from fastapi import APIRouter, Depends, Request, HTTPException
import stripe

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
    api_key = os.environ.get("STRIPE_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Stripe is not configured")
    stripe.api_key = api_key
    return {"webhook_url": webhook_url}


def _webhook_secret() -> str:
    return os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()


def _session_to_status(session) -> dict:
    return {
        "session_id": session.get("id"),
        "status": session.get("status"),
        "payment_status": session.get("payment_status"),
        "url": session.get("url"),
    }


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
    success_url = f"{app_base}/app/plans/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{app_base}/app/plans"
    metadata = {"user_id": str(user["_id"]), "plan_id": plan_id, "source": "app_upgrade"}

    checkout = _checkout(webhook_url)
    unit_amount = int(round(amount * 100))
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            line_items=[{
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": unit_amount,
                    "product_data": {
                        "name": next((p["name"] for p in PLAN_CATALOG if p["id"] == plan_id), plan_id.title()),
                        "description": f"MapleJourney {plan_id.title()} plan",
                    },
                },
            }],
        )
    except stripe.error.StripeError as exc:
        logger.exception("stripe checkout create failed user_id=%s plan_id=%s", str(user["_id"]), plan_id)
        raise HTTPException(status_code=502, detail=f"Stripe checkout failed: {exc.user_message or str(exc)}") from exc

    logger.info(
        "stripe checkout created session_id=%s user_id=%s plan_id=%s amount=%s currency=usd app_base=%s",
        session.get("id"),
        str(user["_id"]),
        plan_id,
        amount,
        app_base,
    )

    await db.payment_transactions.insert_one({
        "session_id": session.get("id"),
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
    return {"url": session.get("url"), "session_id": session.get("id")}


@router.get("/checkout/status/{session_id}")
async def checkout_status(session_id: str, request: Request, user: dict = Depends(get_current_user)):
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Unknown checkout session")
    if txn.get("user_id") != str(user["_id"]):
        raise HTTPException(status_code=403, detail="This checkout session does not belong to you")

    host = str(request.base_url).rstrip("/")
    _checkout(f"{host}/api/webhook/stripe")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        status = _session_to_status(session)
    except stripe.error.StripeError as exc:
        logger.exception("stripe checkout status failed session_id=%s user_id=%s", session_id, str(user["_id"]))
        raise HTTPException(status_code=502, detail=f"Stripe status lookup failed: {exc.user_message or str(exc)}") from exc

    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": status["status"], "payment_status": status["payment_status"], "updated_at": _now_iso()}},
    )
    if status["payment_status"] == "paid":
        await _grant_tier(session_id)

    logger.info(
        "stripe checkout status session_id=%s user_id=%s status=%s payment_status=%s",
        session_id,
        str(user["_id"]),
        status["status"],
        status["payment_status"],
    )

    return {"status": status["status"], "payment_status": status["payment_status"], "plan_id": txn["plan_id"]}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature")
    try:
        _checkout(str(request.base_url).rstrip("/"))
        webhook_secret = _webhook_secret()
        if webhook_secret and sig:
            event = stripe.Webhook.construct_event(body, sig, webhook_secret)
        else:
            event = json.loads(body.decode("utf-8"))
    except Exception:
        logger.exception("stripe webhook error")
        return {"received": True}

    event_type = event.get("type")
    data_object = ((event.get("data") or {}).get("object") or {})
    session_id = data_object.get("id")
    payment_status = data_object.get("payment_status")

    if event_type == "checkout.session.completed" and payment_status == "paid" and session_id:
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid", "status": "complete", "updated_at": _now_iso()}},
        )
        logger.info("stripe webhook paid session_id=%s", session_id)
        await _grant_tier(session_id)
    return {"received": True}
