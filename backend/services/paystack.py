"""
Paystack Payment Integration Service
Live payment processing for MapleJourney (African focus)
"""
import os
import logging
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("paystack")

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_API_BASE = "https://api.paystack.co"


class PaystackException(Exception):
    """Paystack integration error"""
    pass


async def verify_paystack_request(signature: str, body: str) -> bool:
    """Verify Paystack webhook signature using SHA512 HMAC"""
    import hmac
    import hashlib
    
    hash_obj = hmac.new(
        PAYSTACK_SECRET_KEY.encode(),
        body.encode(),
        hashlib.sha512
    )
    computed = hash_obj.hexdigest()
    return hmac.compare_digest(computed, signature)


async def initialize_payment(
    email: str,
    amount_cents: int,  # In kobo (1/100 of Naira)
    reference: str,
    plan_id: str = "",
    metadata: Dict[str, Any] = None,
    channels: list = None
) -> Dict[str, Any]:
    """
    Initialize Paystack payment.
    
    Args:
        email: Customer email
        amount_cents: Amount in kobo (NGN currency base unit)
        reference: Unique transaction reference
        plan_id: Subscription plan ID if applicable
        metadata: Additional metadata
        channels: Payment channels to accept (card, bank, ussd, qr, mobile_money)
    
    Returns:
        {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": "https://checkout.paystack.com/...",
                "access_code": "...",
                "reference": "..."
            }
        }
    """
    if not PAYSTACK_SECRET_KEY:
        raise PaystackException("PAYSTACK_SECRET_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "email": email,
        "amount": amount_cents,
        "reference": reference,
    }
    
    if metadata:
        payload["metadata"] = metadata
    
    if channels:
        payload["channels"] = channels
    
    if plan_id:
        payload["plan"] = plan_id
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{PAYSTACK_API_BASE}/transaction/initialize",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Paystack init failed: {resp.status} {text}")
                    raise PaystackException(f"Paystack API error: {resp.status}")
                
                data = await resp.json()
                if not data.get("status"):
                    logger.error(f"Paystack init returned error: {data}")
                    raise PaystackException(data.get("message", "Unknown error"))
                
                return data
    except aiohttp.ClientError as e:
        logger.error(f"Paystack connection error: {e}")
        raise PaystackException(f"Connection error: {e}")


async def verify_payment(reference: str) -> Dict[str, Any]:
    """
    Verify payment status using reference.
    
    Returns:
        {
            "status": True,
            "message": "Verification successful",
            "data": {
                "id": 123456,
                "reference": "...",
                "amount": 50000,
                "status": "success",
                "customer": {
                    "id": 789,
                    "email": "customer@example.com",
                    "customer_code": "CUS_xxx"
                },
                "authorization": {
                    "authorization_code": "AUTH_xxx",
                    "bin": "412345",
                    "last4": "5678",
                    "card_type": "visa"
                },
                "plan": null,
                "created_at": "2026-07-05T10:30:00.000Z"
            }
        }
    """
    if not PAYSTACK_SECRET_KEY:
        raise PaystackException("PAYSTACK_SECRET_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{PAYSTACK_API_BASE}/transaction/verify/{reference}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Paystack verify failed: {resp.status} {text}")
                    raise PaystackException(f"Paystack API error: {resp.status}")
                
                data = await resp.json()
                if not data.get("status"):
                    logger.error(f"Paystack verify returned error: {data}")
                    raise PaystackException(data.get("message", "Unknown error"))
                
                return data
    except aiohttp.ClientError as e:
        logger.error(f"Paystack connection error: {e}")
        raise PaystackException(f"Connection error: {e}")


async def create_subscription_plan(
    name: str,
    description: str,
    amount_cents: int,  # Amount in kobo per billing cycle
    interval: str = "monthly",  # monthly, quarterly, biannually, annually
    invoice_limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create subscription plan on Paystack.
    
    Returns:
        {
            "status": True,
            "message": "Plan created",
            "data": {
                "id": 123,
                "name": "Plus Plan",
                "description": "...",
                "amount": 29900,  # in kobo
                "interval": "monthly",
                "plan_code": "PLN_xxx",
                "created_at": "2026-07-05T10:30:00.000Z"
            }
        }
    """
    if not PAYSTACK_SECRET_KEY:
        raise PaystackException("PAYSTACK_SECRET_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": name,
        "description": description,
        "amount": amount_cents,
        "interval": interval,
    }
    
    if invoice_limit:
        payload["invoice_limit"] = invoice_limit
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{PAYSTACK_API_BASE}/plan",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Paystack plan creation failed: {resp.status} {text}")
                    raise PaystackException(f"Paystack API error: {resp.status}")
                
                data = await resp.json()
                if not data.get("status"):
                    logger.error(f"Paystack plan creation returned error: {data}")
                    raise PaystackException(data.get("message", "Unknown error"))
                
                return data
    except aiohttp.ClientError as e:
        logger.error(f"Paystack connection error: {e}")
        raise PaystackException(f"Connection error: {e}")


async def subscribe_customer(
    email: str,
    plan_code: str,
    authorization_code: str,
    customer_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Subscribe customer to a plan.
    
    Returns:
        {
            "status": True,
            "message": "Subscription created",
            "data": {
                "subscription_code": "SUB_xxx",
                "email": "customer@example.com",
                "plan_code": "PLN_xxx",
                "customer_code": "CUS_xxx",
                "authorization": {...},
                "start": "2026-07-05T10:30:00.000Z",
                "status": "active"
            }
        }
    """
    if not PAYSTACK_SECRET_KEY:
        raise PaystackException("PAYSTACK_SECRET_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "customer": customer_code or email,
        "plan": plan_code,
        "authorization": authorization_code,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{PAYSTACK_API_BASE}/subscription",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Paystack subscription failed: {resp.status} {text}")
                    raise PaystackException(f"Paystack API error: {resp.status}")
                
                data = await resp.json()
                if not data.get("status"):
                    logger.error(f"Paystack subscription returned error: {data}")
                    raise PaystackException(data.get("message", "Unknown error"))
                
                return data
    except aiohttp.ClientError as e:
        logger.error(f"Paystack connection error: {e}")
        raise PaystackException(f"Connection error: {e}")


async def get_customer(
    email_or_code: str
) -> Dict[str, Any]:
    """Get customer details from Paystack"""
    if not PAYSTACK_SECRET_KEY:
        raise PaystackException("PAYSTACK_SECRET_KEY not configured")
    
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{PAYSTACK_API_BASE}/customer/{email_or_code}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    if resp.status == 404:
                        return {"status": False, "message": "Customer not found"}
                    text = await resp.text()
                    logger.error(f"Paystack get customer failed: {resp.status} {text}")
                    raise PaystackException(f"Paystack API error: {resp.status}")
                
                return await resp.json()
    except aiohttp.ClientError as e:
        logger.error(f"Paystack connection error: {e}")
        raise PaystackException(f"Connection error: {e}")
