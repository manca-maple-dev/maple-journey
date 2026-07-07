import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone

SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587
TO_EMAIL = "asamoahelvis550@gmail.com"

accounts = [
    ("smtp01@maplejourney.ca", "Z^908115201658ac"),
    ("smtp02@maplejourney.ca", "W(340153008912ov"),
    ("smtp03@maplejourney.ca", "P^746222124728ul"),
    ("smtp04@maplejourney.ca", "Q!188104398843uh"),
    ("smtp05@maplejourney.ca", "K@322730516353uk"),
]

run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
print(f"RUN_ID={run_id}")

for username, password in accounts:
    subject = f"Maple SMTP live retest | {username} | {run_id}"
    body = (
        "Live SMTP verification from MapleJourney.\n\n"
        f"Sender: {username}\n"
        f"Recipient: {TO_EMAIL}\n"
        f"Run ID: {run_id}\n"
        f"UTC: {datetime.now(timezone.utc).isoformat()}\n"
    )

    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.send_message(msg)
        print(f"OK|{username}|sent")
    except Exception as e:
        print(f"FAIL|{username}|{type(e).__name__}: {e}")
