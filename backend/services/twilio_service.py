"""Twilio helpers: phone OTP (Verify) and Maple Wingman on WhatsApp."""
import os
import asyncio


TWILIO_REQUIRED_VARS = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN")


def twilio_config_status() -> dict:
    required = (
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_VERIFY_SERVICE_SID",
        "TWILIO_WHATSAPP_FROM",
        "TWILIO_PHONE_NUMBER",
    )
    missing = [name for name in required if not os.environ.get(name)]
    return {
        "configured": not missing,
        "missing": missing,
        "verify_enabled": not any(name in missing for name in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_VERIFY_SERVICE_SID")),
        "whatsapp_enabled": not any(name in missing for name in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM")),
        "sms_enabled": not any(name in missing for name in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER")),
    }


def _require_twilio_env(*names: str) -> None:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Twilio is not configured. Missing: {', '.join(missing)}")


def twilio_client():
    _require_twilio_env(*TWILIO_REQUIRED_VARS)
    from twilio.rest import Client
    return Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])


def normalize_phone(p: str) -> str:
    p = (p or "").strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if p and not p.startswith("+"):
        p = "+" + p
    return p


def send_otp(phone: str):
    _require_twilio_env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_VERIFY_SERVICE_SID")
    twilio_client().verify.v2.services(os.environ["TWILIO_VERIFY_SERVICE_SID"]).verifications.create(to=phone, channel="sms")


def check_otp(phone: str, code: str):
    _require_twilio_env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_VERIFY_SERVICE_SID")
    return twilio_client().verify.v2.services(os.environ["TWILIO_VERIFY_SERVICE_SID"]).verification_checks.create(to=phone, code=code)


async def send_whatsapp(to_phone: str, text: str):
    _require_twilio_env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM")
    return await asyncio.to_thread(
        twilio_client().messages.create,
        from_=os.environ["TWILIO_WHATSAPP_FROM"],
        to=f"whatsapp:{normalize_phone(to_phone)}",
        body=text,
    )


async def send_imessage(to_phone: str, text: str):
    """Send via SMS (appears as iMessage on iPhone, SMS on Android).
    
    Note: True Apple Business Chat requires enterprise setup.
    This implementation uses SMS as the transport, which:
    - Delivers as iMessage on iPhone (via iCloud)
    - Delivers as SMS on Android
    """
    return await asyncio.to_thread(
        twilio_client().messages.create,
        from_=os.environ["TWILIO_PHONE_NUMBER"],
        to=normalize_phone(to_phone),
        body=text,
    )


async def send_message_by_channel(to_phone: str, text: str, channel: str = "whatsapp"):
    """Route message to appropriate channel.
    
    Args:
        to_phone: Phone number (with or without +)
        text: Message body
        channel: 'whatsapp', 'imessage', or 'sms'
    """
    channel = (channel or "sms").lower()
    if channel == "whatsapp":
        return await send_whatsapp(normalize_phone(to_phone), text)
    elif channel == "imessage":
        return await send_imessage(normalize_phone(to_phone), text)
    else:  # SMS fallback
        _require_twilio_env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER")
        return await asyncio.to_thread(
            twilio_client().messages.create,
            from_=os.environ["TWILIO_PHONE_NUMBER"],
            to=normalize_phone(to_phone),
            body=text,
        )
