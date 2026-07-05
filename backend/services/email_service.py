"""SMTP email delivery for MapleJourney.

Uses aiosmtplib for async, non-blocking sending. `send_email_safe` never raises
so a delivery failure can never break an API request — every attempt is logged
to the `email_log` collection. Endpoints schedule sends via FastAPI
BackgroundTasks so the user never waits on SMTP.
"""
import os
import logging
from datetime import datetime, timezone
from email.message import EmailMessage

try:
    import aiosmtplib
    HAS_AIOSMTPLIB = True
except ImportError:
    HAS_AIOSMTPLIB = False

from core.db import db
from services import email_templates as tpl

log = logging.getLogger("maplejourney.email")


class EmailConfigError(RuntimeError):
    pass


def _env_bool(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() == "true"


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise EmailConfigError(f"Missing required SMTP env var: {name}")
    return value


def _cfg():
    return {
        "host": _required_env("SMTP_HOST"),
        "port": int(os.environ.get("SMTP_PORT", "465").strip()),
        "user": _required_env("SMTP_USERNAME"),
        "password": _required_env("SMTP_PASSWORD"),
        "use_tls": _env_bool("SMTP_USE_TLS", "true"),
        "start_tls": _env_bool("SMTP_STARTTLS", "false"),
        "from_email": _required_env("SMTP_FROM_EMAIL"),
        "from_name": os.environ.get("SMTP_FROM_NAME", "MapleJourney"),
        "reply_to": os.environ.get("SMTP_REPLY_TO", "").strip() or _required_env("SMTP_FROM_EMAIL"),
        "timeout": int(os.environ.get("SMTP_TIMEOUT", "20")),
    }


async def _send_raw(to_email: str, subject: str, html: str, text: str):
    if not HAS_AIOSMTPLIB:
        log.warning("aiosmtplib not installed; skipping email send to %s: %s", to_email, subject)
        return
    c = _cfg()
    log.info(
        "email smtp config host=%s port=%s use_tls=%s start_tls=%s from_email=%s reply_to=%s",
        c["host"],
        c["port"],
        c["use_tls"],
        c["start_tls"],
        c["from_email"],
        c["reply_to"],
    )
    msg = EmailMessage()
    msg["From"] = f"{c['from_name']} <{c['from_email']}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = c["reply_to"]
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    await aiosmtplib.send(
        msg,
        hostname=c["host"],
        port=c["port"],
        username=c["user"],
        password=c["password"],
        use_tls=c["use_tls"],
        start_tls=c["start_tls"],
        timeout=c["timeout"],
    )


async def send_email_safe(to_email: str, template: str, **ctx) -> bool:
    """Render + deliver a branded email. Never raises; logs the outcome."""
    try:
        subject, html, text = tpl.render(template, **ctx)
    except Exception:
        log.exception("email template render failed: %s", template)
        return False

    entry = {
        "to": to_email,
        "template": template,
        "subject": subject,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ok = False
    try:
        await _send_raw(to_email, subject, html, text)
        entry["status"] = "sent"
        ok = True
        log.info(
            "email sent template=%s to=%s subject=%s",
            template,
            to_email,
            subject,
        )
    except Exception as e:
        log.warning(
            "email failed template=%s to=%s subject=%s error=%s",
            template,
            to_email,
            subject,
            str(e),
        )
        entry["status"] = "failed"
        entry["error"] = str(e)
    try:
        await db.email_log.insert_one(entry)
    except Exception:
        log.exception(
            "email log persistence failed template=%s to=%s status=%s",
            template,
            to_email,
            entry.get("status", "unknown"),
        )
    return ok
