"""
Paystack Payment Router - Live payment integration
Supports one-time payments and recurring subscriptions
"""
import os
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Body, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr

from core.db import db
from core.security import get_current_user
from services.paystack import (
    initialize_payment,
    verify_payment,
    create_subscription_plan,
    subscribe_customer,
    get_customer,
    PaystackException,
    verify_paystack_request
)
from services.email_service import send_email_safe

logger = logging.getLogger("paystack_router")
router = APIRouter(prefix="/paystack", tags=["paystack"])


# --- Models ---
class PaystackCheckoutIn(BaseModel):
    plan_id: str
    origin_url: Optional[str] = ""


class PaystackSubscribeIn(BaseModel):
    plan_code: str
    authorization_code: str
    email: str


class PaystackWebhookIn(BaseModel):
    event: str
    data: dict


# --- One-Time Payment (checkout) ---
@router.post("/checkout/initialize")
async def paystack_checkout_initialize(
    body: PaystackCheckoutIn,
    user: dict = Depends(get_current_user)
):
    """
    Initialize Paystack payment for one-time purchase.
    
    Returns:
        {
            "authorization_url": "https://checkout.paystack.com/...",
            "access_code": "...",
            "reference": "..."
        }
    """
    plan_id = body.plan_id
    
    # Get plan details
    plan = await db.plans.find_one({"id": plan_id})
    if not plan:
        return {"error": "Plan not found"}
    
    # Amount in kobo (NGN currency base unit: 1 Naira = 100 kobo)
    amount_cents = int(plan.get("price_cents", 0))
    if amount_cents <= 0:
        return {"error": "Invalid plan price"}
    
    user_id = str(user["_id"])
    reference = f"maple_{user_id}_{plan_id}_{int(datetime.utcnow().timestamp())}"
    
    try:
        response = await initialize_payment(
            email=user.get("email", ""),
            amount_cents=amount_cents,
            reference=reference,
            metadata={
                "user_id": user_id,
                "plan_id": plan_id,
                "plan_name": plan.get("name"),
                "origin_url": body.origin_url or ""
            },
            channels=["card", "bank", "ussd", "mobile_money"]  # Accept multiple payment methods
        )
        
        if response.get("status"):
            # Store pending transaction
            await db.transactions.insert_one({
                "reference": reference,
                "user_id": user_id,
                "plan_id": plan_id,
                "amount_cents": amount_cents,
                "status": "pending",
                "provider": "paystack",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            logger.info(f"Paystack payment initialized: {reference}")
            return {
                "authorization_url": response["data"]["authorization_url"],
                "access_code": response["data"]["access_code"],
                "reference": reference
            }
        else:
            logger.error(f"Paystack init failed: {response}")
            return {"error": response.get("message", "Payment initialization failed")}
    
    except PaystackException as e:
        logger.error(f"Paystack error: {e}")
        return {"error": str(e)}


@router.get("/verify/{reference}")
async def paystack_verify_payment(
    reference: str,
    user: dict = Depends(get_current_user)
):
    """Verify Paystack payment after callback"""
    try:
        response = await verify_payment(reference)
        
        if response.get("status"):
            payment_data = response.get("data", {})
            payment_status = payment_data.get("status")
            
            # Update transaction
            update_result = await db.transactions.update_one(
                {"reference": reference},
                {
                    "$set": {
                        "status": payment_status,
                        "paystack_data": payment_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if payment_status == "success":
                # Get plan details
                tx = await db.transactions.find_one({"reference": reference})
                plan_id = tx.get("plan_id")
                
                # Upgrade user plan
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {
                            "current_plan": plan_id,
                            "plan_upgraded_at": datetime.utcnow(),
                            "provider": "paystack"
                        }
                    }
                )
                
                logger.info(f"Payment successful: {reference} -> {plan_id}")
                
                # Send confirmation email
                background_tasks = BackgroundTasks()
                background_tasks.add_task(
                    send_email_safe,
                    user.get("email"),
                    "payment_confirmation",
                    name=user.get("name", ""),
                    plan_name=(await db.plans.find_one({"id": plan_id})).get("name", "")
                )
                
                return {"status": "success", "message": "Payment verified and plan upgraded"}
            
            elif payment_status == "failed":
                logger.warning(f"Payment failed: {reference}")
                return {"status": "failed", "message": "Payment was not successful"}
            
            else:
                return {"status": payment_status, "message": f"Payment status: {payment_status}"}
        else:
            logger.error(f"Paystack verify failed: {response}")
            return {"error": response.get("message", "Verification failed")}
    
    except PaystackException as e:
        logger.error(f"Paystack error: {e}")
        return {"error": str(e)}


# --- Recurring Subscription ---
@router.post("/subscription/create-plan")
async def create_paystack_plan(
    plan_data: dict = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    Create subscription plan on Paystack.
    Admin only.
    """
    if not user.get("is_admin"):
        return {"error": "Admin access required"}
    
    try:
        response = await create_subscription_plan(
            name=plan_data["name"],
            description=plan_data.get("description", ""),
            amount_cents=int(plan_data["amount_cents"]),
            interval=plan_data.get("interval", "monthly")
        )
        
        if response.get("status"):
            return {"plan_code": response["data"]["plan_code"]}
        else:
            return {"error": response.get("message")}
    
    except PaystackException as e:
        logger.error(f"Paystack error: {e}")
        return {"error": str(e)}


@router.post("/subscription/subscribe")
async def paystack_subscribe(
    body: PaystackSubscribeIn,
    user: dict = Depends(get_current_user)
):
    """
    Subscribe user to recurring plan.
    """
    try:
        response = await subscribe_customer(
            email=body.email,
            plan_code=body.plan_code,
            authorization_code=body.authorization_code,
            customer_code=str(user["_id"])
        )
        
        if response.get("status"):
            subscription_data = response["data"]
            
            # Store subscription
            await db.subscriptions.insert_one({
                "user_id": user["_id"],
                "subscription_code": subscription_data.get("subscription_code"),
                "plan_code": body.plan_code,
                "provider": "paystack",
                "status": subscription_data.get("status"),
                "authorization_code": body.authorization_code,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
            logger.info(f"Subscription created: {subscription_data.get('subscription_code')}")
            return {"status": "success", "subscription_code": subscription_data.get("subscription_code")}
        else:
            logger.error(f"Paystack subscription failed: {response}")
            return {"error": response.get("message")}
    
    except PaystackException as e:
        logger.error(f"Paystack error: {e}")
        return {"error": str(e)}


# --- Webhook Handler ---
@router.post("/webhook")
async def paystack_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Paystack webhook events (charge.success, charge.failed, etc.)
    
    Verify signature header: "x-paystack-signature"
    """
    try:
        # Get signature
        signature = request.headers.get("x-paystack-signature")
        if not signature:
            logger.warning("Paystack webhook: missing signature")
            return {"status": "error"}
        
        # Get body
        body = await request.body()
        
        # Verify signature
        is_valid = await verify_paystack_request(signature, body.decode())
        if not is_valid:
            logger.warning("Paystack webhook: invalid signature")
            return {"status": "error"}
        
        # Parse event
        import json
        event_data = json.loads(body)
        event_type = event_data.get("event")
        data = event_data.get("data", {})
        
        logger.info(f"Paystack webhook: {event_type}")
        
        if event_type == "charge.success":
            reference = data.get("reference")
            
            # Update transaction
            await db.transactions.update_one(
                {"reference": reference},
                {"$set": {"status": "success", "updated_at": datetime.utcnow()}}
            )
            
            logger.info(f"Payment success: {reference}")
        
        elif event_type == "charge.failed":
            reference = data.get("reference")
            
            # Update transaction
            await db.transactions.update_one(
                {"reference": reference},
                {"$set": {"status": "failed", "updated_at": datetime.utcnow()}}
            )
            
            logger.info(f"Payment failed: {reference}")
        
        elif event_type == "subscription.create":
            subscription_code = data.get("subscription_code")
            logger.info(f"Subscription created: {subscription_code}")
        
        elif event_type == "subscription.disable":
            subscription_code = data.get("subscription_code")
            
            # Update subscription
            await db.subscriptions.update_one(
                {"subscription_code": subscription_code},
                {"$set": {"status": "disabled", "updated_at": datetime.utcnow()}}
            )
            
            logger.info(f"Subscription disabled: {subscription_code}")
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"Paystack webhook error: {e}")
        return {"status": "error", "message": str(e)}


# --- Customer Info ---
@router.get("/customer/{email}")
async def get_paystack_customer(
    email: str,
    user: dict = Depends(get_current_user)
):
    """Get Paystack customer details"""
    if user.get("email") != email and not user.get("is_admin"):
        return {"error": "Unauthorized"}
    
    try:
        response = await get_customer(email)
        if response.get("status"):
            return response.get("data", {})
        else:
            return {"error": response.get("message")}
    
    except PaystackException as e:
        logger.error(f"Paystack error: {e}")
        return {"error": str(e)}
