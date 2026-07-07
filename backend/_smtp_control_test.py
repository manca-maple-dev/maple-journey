import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone

SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587
TO_EMAIL = "asamoahelvis550@gmail.com"
USER = "smtp@maplejourney.ca"
PASS = "0554455098aA"

run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
msg = EmailMessage()
msg["From"] = USER
msg["To"] = TO_EMAIL
msg["Subject"] = f"Control SMTP test | {run_id}"
msg.set_content(f"Control test from {USER} at {datetime.now(timezone.utc).isoformat()}")

try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(USER, PASS)
        s.send_message(msg)
    print("CONTROL_OK")
except Exception as e:
    print(f"CONTROL_FAIL|{type(e).__name__}: {e}")
