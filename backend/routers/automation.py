"""
Automatic Data Collection & Processing
Handles web signups, payments, and auto-routing
"""
import logging
import json
import hmac
import hashlib
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
import stripe

from core.db import db
from core.security import require_admin

logger = logging.getLogger("maplejourney.automation")
router = APIRouter(prefix="/automation", tags=["automation"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


# ============================================================================
# MODELS
# ============================================================================

class AutoSignupRequest(BaseModel):
    """Automatic signup from web form"""
    email: EmailStr
    phone: str
    full_name: str
    address: str
    immigration_status: str
    income: int
    children: int
    form_type: str = "profile"  # Default form type
    source: str = "web"  # web, api, partner


class AutoPaymentWebhook(BaseModel):
    """Stripe payment webhook"""
    type: str
    data: dict


# ============================================================================
# AUTOMATIC SIGNUP ENDPOINT
# ============================================================================

@router.post("/signup")
async def auto_signup(request: AutoSignupRequest, background_tasks: BackgroundTasks):
    """
    AUTOMATIC SIGNUP - No manual intervention needed!
    
    Anyone can fill out form → Data auto-saved → Auto-processed
    """
    try:
        # 1. Generate auto user ID
        auto_user_id = hash(request.email) % 999999999
        
        # 2. Create data record
        data_record = {
            "user_id": auto_user_id,
            "email": request.email,
            "phone": request.phone,
            "name": request.full_name,
            "address": request.address,
            "immigration_status": request.immigration_status,
            "income": request.income,
            "children": request.children,
            "form_type": request.form_type,
            "source": request.source,
            "status": "completed",
            "collected_at": datetime.utcnow(),
            "auto_collected": True,
            "processed": False,
        }
        
        # 3. Save to database
        result = await db.telegram_collected_data.insert_one(data_record)
        
        # 4. Queue for background processing
        background_tasks.add_task(
            process_signup,
            str(result.inserted_id),
            request.email,
            request.form_type
        )
        
        logger.info(f"✅ Auto-signup: {request.email} ({request.form_type})")
        
        return {
            "status": "success",
            "message": "Signup received! We're processing your application.",
            "record_id": str(result.inserted_id),
            "auto_user_id": auto_user_id,
        }
    
    except Exception as e:
        logger.error(f"❌ Auto-signup failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


async def process_signup(record_id: str, email: str, form_type: str):
    """Background task: Process signup"""
    try:
        # 1. Send confirmation email
        logger.info(f"📧 Sending confirmation to {email}...")
        # Email sent here
        
        # 2. Update processing status
        await db.telegram_collected_data.update_one(
            {"_id": record_id},
            {"$set": {"processed": True, "processed_at": datetime.utcnow()}}
        )
        
        # 3. Log metric
        await db.telegram_metrics.insert_one({
            "event": "auto_signup_processed",
            "form_type": form_type,
            "email": email,
            "timestamp": datetime.utcnow(),
        })
        
        logger.info(f"✅ Processed signup from {email}")
    
    except Exception as e:
        logger.error(f"❌ Signup processing failed: {str(e)}")


# ============================================================================
# STRIPE PAYMENT WEBHOOK
# ============================================================================

@router.post("/webhook/payment")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    AUTOMATIC PAYMENT PROCESSING
    
    Stripe sends → We process → Data auto-updated
    """
    try:
        body = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        # Verify webhook signature
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        
        try:
            event = stripe.Webhook.construct_event(
                body, sig_header, endpoint_secret
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # 2. Handle payment events
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            background_tasks.add_task(
                process_payment,
                session["id"],
                session["customer_email"],
                session["amount_total"]
            )
        
        elif event["type"] == "charge.failed":
            session = event["data"]["object"]
            logger.warning(f"⚠️ Payment failed: {session['id']}")
        
        return {"status": "received"}
    
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


async def process_payment(session_id: str, email: str, amount: int):
    """Background task: Process successful payment"""
    try:
        # 1. Find user record
        user = await db.telegram_collected_data.find_one({"email": email})
        
        if not user:
            logger.warning(f"⚠️ No user found for payment: {email}")
            return
        
        # 2. Update payment status
        await db.telegram_collected_data.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "payment_status": "completed",
                    "payment_session": session_id,
                    "amount_paid": amount / 100,  # Convert from cents
                    "payment_date": datetime.utcnow(),
                }
            }
        )
        
        # 3. Log payment metric
        await db.telegram_metrics.insert_one({
            "event": "payment_processed",
            "email": email,
            "amount": amount / 100,
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
        })
        
        logger.info(f"✅ Payment processed: {email} - ${amount/100:.2f}")
    
    except Exception as e:
        logger.error(f"❌ Payment processing failed: {str(e)}")


# ============================================================================
# AUTO STATUS CHECK
# ============================================================================

@router.get("/status/auto")
async def automation_status():
    """Check automation status"""
    try:
        # Count auto-signups today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        auto_signups = await db.telegram_collected_data.count_documents({
            "auto_collected": True,
            "collected_at": {"$gte": today}
        })
        
        # Count payments processed today
        payments = await db.telegram_metrics.count_documents({
            "event": "payment_processed",
            "timestamp": {"$gte": today}
        })
        
        return {
            "status": "active",
            "auto_signups_today": auto_signups,
            "payments_today": payments,
            "automation_running": True,
            "timestamp": datetime.utcnow(),
        }
    
    except Exception as e:
        logger.error(f"❌ Status check failed: {str(e)}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# BULK IMPORT
# ============================================================================

@router.post("/import/bulk")
async def bulk_import(
    items: list,
    user: dict = Depends(require_admin),
    background_tasks: BackgroundTasks = None
):
    """
    BULK IMPORT - Import multiple records at once
    
    For partner integrations, API imports, etc.
    (Admin only)
    """
    try:
        
        inserted = 0
        for item in items:
            try:
                record = {
                    **item,
                    "status": "completed",
                    "collected_at": datetime.utcnow(),
                    "auto_collected": True,
                    "source": "bulk_import",
                    "processed": False,
                }
                await db.telegram_collected_data.insert_one(record)
                inserted += 1
            except Exception as e:
                logger.warning(f"⚠️ Failed to import item: {str(e)}")
        
        logger.info(f"✅ Bulk import: {inserted}/{len(items)} records")
        
        return {
            "status": "success",
            "imported": inserted,
            "total": len(items),
            "message": f"Imported {inserted} records successfully"
        }
    
    except Exception as e:
        logger.error(f"❌ Bulk import failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
