"""Branded, investor-grade HTML email templates for MapleJourney.

Every email shares one professional, table-based layout that renders reliably
across email clients (Gmail, Outlook, Apple Mail). Brand: MapleJourney blue
(#0066FF) + maple red (#E31837) on a clean light canvas.

Each template function returns a (subject, html, text) tuple. `render()` is the
single entry point used by the email service.
"""
import os
from datetime import datetime, timezone

# --- brand tokens -------------------------------------------------------------
BRAND = "#0066FF"
NAVY = "#001B44"
MAPLE = "#E31837"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#e2e8f0"
CANVAS = "#eef2f7"
CARD = "#ffffff"
LOGO_URL = os.environ.get(
    "EMAIL_LOGO_URL",
    "https://static.prod-images.emergentagent.com/jobs/7f869000-5ecc-4ddf-b719-0bb45e5e5b49/images/4490d7e5af308d35af21aa5690c831f1eda6415e1a6edae288dcf9987bb0fefc.png",
)


def _app():
    return {
        "name": "MapleJourney",
        "tagline": "Your journey to Canada, guided every step.",
        "base_url": os.environ.get("APP_BASE_URL", "https://app.maplejourney.ca").rstrip("/"),
        "support": os.environ.get("SUPPORT_EMAIL", os.environ.get("SMTP_REPLY_TO", "support@boomerbetting.com")),
    }


def _first(name: str) -> str:
    return (name or "there").strip().split(" ")[0] or "there"


def _button(label: str, url: str) -> str:
    return (
        f'<table role="presentation" cellspacing="0" cellpadding="0" style="margin:28px 0;">'
        f'<tr><td align="center" bgcolor="{BRAND}" style="border-radius:999px;">'
        f'<a href="{url}" target="_blank" '
        f'style="display:inline-block;padding:14px 30px;font-family:Arial,Helvetica,sans-serif;'
        f'font-size:15px;font-weight:700;color:#ffffff;text-decoration:none;border-radius:999px;">'
        f'{label}</a></td></tr></table>'
    )


def _layout(preheader: str, heading: str, body_html: str) -> str:
    a = _app()
    year = datetime.now(timezone.utc).year
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>{heading}</title></head>
<body style="margin:0;padding:0;background:{CANVAS};-webkit-font-smoothing:antialiased;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;font-size:1px;line-height:1px;color:{CANVAS};">{preheader}</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{CANVAS};padding:36px 12px;">
<tr><td align="center">
<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="width:600px;max-width:100%;">

<!-- brand header -->
<tr><td style="padding:2px 6px 22px 6px;">
  <table role="presentation" cellspacing="0" cellpadding="0"><tr>
    <td valign="middle" style="padding-right:13px;">
      <img src="{LOGO_URL}" width="48" height="48" alt="MapleJourney"
           style="display:block;width:48px;height:48px;border-radius:13px;border:0;outline:none;text-decoration:none;" />
    </td>
    <td valign="middle" style="font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:23px;font-weight:800;color:{NAVY};letter-spacing:-0.4px;">
      Maple<span style="color:{BRAND};">Journey</span>
    </td>
  </tr></table>
</td></tr>

<!-- card -->
<tr><td style="background:{CARD};border:1px solid {LINE};border-top:4px solid {BRAND};border-radius:16px;padding:40px 44px 34px 44px;">
  <h1 style="margin:0 0 18px 0;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:25px;line-height:1.25;font-weight:800;color:{INK};letter-spacing:-0.3px;">{heading}</h1>
  <div style="font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:15px;line-height:1.68;color:#334155;">{body_html}</div>
</td></tr>

<!-- footer -->
<tr><td style="padding:26px 24px 6px 24px;">
  <table role="presentation" cellspacing="0" cellpadding="0" style="margin-bottom:12px;"><tr>
    <td valign="middle" style="padding-right:10px;">
      <img src="{LOGO_URL}" width="28" height="28" alt="" style="display:block;width:28px;height:28px;border-radius:8px;border:0;" />
    </td>
    <td valign="middle" style="font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:15px;font-weight:800;color:{NAVY};letter-spacing:-0.2px;">
      Maple<span style="color:{BRAND};">Journey</span>
    </td>
  </tr></table>
  <p style="margin:0 0 8px 0;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:13px;line-height:1.6;color:{MUTED};">
    {a['tagline']} &nbsp;·&nbsp; Questions? <a href="mailto:{a['support']}" style="color:{BRAND};text-decoration:none;">{a['support']}</a>
  </p>
  <p style="margin:0;font-family:'Segoe UI',Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:#94a3b8;">
    MapleJourney is an independent settlement companion providing cited information and organization —
    not legal advice. For legal representation consult a licensed RCIC or lawyer.<br>
    &copy; {year} MapleJourney. All rights reserved.
  </p>
</td></tr>

</table>
</td></tr>
</table>
</body></html>"""


def _text(lines) -> str:
    a = _app()
    footer = (
        f"\n\n—\n{a['name']} — {a['tagline']}\n"
        f"Questions? {a['support']}\n"
        "MapleJourney provides cited information, not legal advice."
    )
    return "\n".join(lines) + footer


# --- templates ----------------------------------------------------------------
def welcome(name: str = "", **_):
    a = _app()
    first = _first(name)
    heading = f"Welcome to MapleJourney, {first} \U0001F341"
    body = (
        f"<p style='margin:0 0 14px 0;'>You just took the first clear step toward building your life in Canada. "
        f"MapleJourney turns the maze of visas, PR, jobs and benefits into one personalized path — "
        f"with guidance cited from IRCC, CRA &amp; Service Canada.</p>"
        f"<p style='margin:0 0 6px 0;'>Here's what to do next:</p>"
        f"<ul style='margin:0 0 8px 20px;padding:0;color:#334155;'>"
        f"<li style='margin-bottom:6px;'>Finish your quick profile so Maple can tailor everything to you</li>"
        f"<li style='margin-bottom:6px;'>Ask Maple your first immigration question</li>"
        f"<li style='margin-bottom:6px;'>Check your personalized daily briefing</li></ul>"
        + _button("Open MapleJourney", f"{a['base_url']}/app")
        + "<p style='margin:0;color:#64748b;font-size:13px;'>We're glad you're here.</p>"
    )
    text = _text([
        f"Welcome to MapleJourney, {first}!",
        "",
        "You just took the first clear step toward building your life in Canada.",
        "Next: finish your profile, ask Maple a question, and check your daily briefing.",
        f"Open MapleJourney: {a['base_url']}/app",
    ])
    return heading, _layout("Welcome to MapleJourney — your journey starts here.", heading, body), text


def password_reset(name: str = "", reset_url: str = "", **_):
    first = _first(name)
    heading = "Reset your password"
    body = (
        f"<p style='margin:0 0 14px 0;'>Hi {first}, we received a request to reset the password for your "
        f"MapleJourney account. Click the button below to choose a new password. "
        f"This link expires in <strong>60 minutes</strong>.</p>"
        + _button("Reset my password", reset_url)
        + f"<p style='margin:0 0 8px 0;color:#64748b;font-size:13px;'>If the button doesn't work, copy and paste this link:<br>"
          f"<a href='{reset_url}' style='color:{BRAND};word-break:break-all;'>{reset_url}</a></p>"
        + "<p style='margin:14px 0 0 0;color:#64748b;font-size:13px;'>Didn't request this? You can safely ignore this "
          "email — your password won't change.</p>"
    )
    text = _text([
        f"Hi {first},",
        "",
        "Reset your MapleJourney password using the link below (expires in 60 minutes):",
        reset_url,
        "",
        "Didn't request this? You can safely ignore this email.",
    ])
    return heading, _layout("Reset your MapleJourney password.", heading, body), text


def password_changed(name: str = "", **_):
    a = _app()
    first = _first(name)
    heading = "Your password was changed"
    body = (
        f"<p style='margin:0 0 14px 0;'>Hi {first}, this is a confirmation that the password for your "
        f"MapleJourney account was just changed.</p>"
        f"<p style='margin:0 0 14px 0;'>If this was you, no further action is needed.</p>"
        f"<p style='margin:0;color:#64748b;font-size:13px;'>If you did <strong>not</strong> make this change, "
        f"please reset your password immediately and contact us at "
        f"<a href='mailto:{a['support']}' style='color:{BRAND};'>{a['support']}</a>.</p>"
    )
    text = _text([
        f"Hi {first},",
        "",
        "Your MapleJourney password was just changed.",
        "If this wasn't you, reset your password immediately and contact us.",
    ])
    return heading, _layout("Your MapleJourney password was changed.", heading, body), text


def payment_confirmation(name: str = "", plan_name: str = "Plus", amount: str = "", expires: str = "", **_):
    a = _app()
    first = _first(name)
    heading = f"You're on MapleJourney {plan_name} \U0001F389"
    amount_row = f"<tr><td style='padding:6px 0;color:#64748b;'>Amount</td><td align='right' style='padding:6px 0;color:{INK};font-weight:700;'>{amount}</td></tr>" if amount else ""
    expires_row = f"<tr><td style='padding:6px 0;color:#64748b;'>Renews / valid until</td><td align='right' style='padding:6px 0;color:{INK};font-weight:700;'>{expires}</td></tr>" if expires else ""
    body = (
        f"<p style='margin:0 0 16px 0;'>Thank you, {first}! Your upgrade to <strong>{plan_name}</strong> is confirmed. "
        f"You now have unlimited Maple chats, deeper personalized guidance and priority responses.</p>"
        f"<table role='presentation' width='100%' style='border:1px solid {LINE};border-radius:12px;padding:14px 18px;'>"
        f"<tr><td style='padding:6px 0;color:#64748b;'>Plan</td><td align='right' style='padding:6px 0;color:{INK};font-weight:700;'>MapleJourney {plan_name}</td></tr>"
        f"{amount_row}{expires_row}"
        f"</table>"
        + _button("Go to my dashboard", f"{a['base_url']}/app")
        + f"<p style='margin:0;color:#64748b;font-size:13px;'>This email is your receipt. Manage your plan anytime under "
          f"Profile &rarr; Subscription.</p>"
    )
    text = _text([
        f"Thank you, {first}! Your upgrade to MapleJourney {plan_name} is confirmed.",
        f"Amount: {amount}" if amount else "",
        f"Valid until: {expires}" if expires else "",
        f"Dashboard: {a['base_url']}/app",
    ])
    return heading, _layout(f"Your MapleJourney {plan_name} upgrade is confirmed.", heading, body), text


def onboarding_complete(name: str = "", city: str = "", **_):
    a = _app()
    first = _first(name)
    place = f" for {city}" if city else ""
    heading = f"Your MapleJourney is set up, {first}"
    body = (
        f"<p style='margin:0 0 14px 0;'>Your profile is complete — Maple now understands your situation and will "
        f"tailor your briefing, jobs, benefits and deadlines{place}.</p>"
        f"<p style='margin:0 0 6px 0;'>From here you can:</p>"
        f"<ul style='margin:0 0 8px 20px;padding:0;color:#334155;'>"
        f"<li style='margin-bottom:6px;'>Read your grounded daily briefing</li>"
        f"<li style='margin-bottom:6px;'>Track key permit &amp; citizenship deadlines</li>"
        f"<li style='margin-bottom:6px;'>Ask Maple anything about your journey</li></ul>"
        + _button("See my briefing", f"{a['base_url']}/app")
    )
    text = _text([
        f"Your MapleJourney is set up, {first}.",
        "Maple now tailors your briefing, jobs, benefits and deadlines to you.",
        f"See your briefing: {a['base_url']}/app",
    ])
    return heading, _layout("Your MapleJourney profile is complete.", heading, body), text


def account_deleted(name: str = "", **_):
    a = _app()
    first = _first(name)
    heading = "Your account has been deleted"
    body = (
        f"<p style='margin:0 0 14px 0;'>Hi {first}, this confirms that your MapleJourney account and associated "
        f"data have been permanently deleted, as you requested.</p>"
        f"<p style='margin:0 0 14px 0;'>We're sorry to see you go. If you'd ever like to return, you're always "
        f"welcome to create a new account.</p>"
        f"<p style='margin:0;color:#64748b;font-size:13px;'>If you did not request this, contact us right away at "
        f"<a href='mailto:{a['support']}' style='color:{BRAND};'>{a['support']}</a>.</p>"
    )
    text = _text([
        f"Hi {first},",
        "",
        "Your MapleJourney account and data have been permanently deleted, as requested.",
        "If you didn't request this, contact us right away.",
    ])
    return heading, _layout("Your MapleJourney account has been deleted.", heading, body), text


def announcement(name: str = "", title: str = "", body_text: str = "", **_):
    a = _app()
    first = _first(name)
    heading = title or "An update from MapleJourney"
    safe_body = (body_text or "").replace("\n", "<br>")
    body = (
        f"<p style='margin:0 0 14px 0;'>Hi {first},</p>"
        f"<p style='margin:0 0 14px 0;'>{safe_body}</p>"
        + _button("Open MapleJourney", f"{a['base_url']}/app")
    )
    text = _text([f"Hi {first},", "", body_text or "", f"Open MapleJourney: {a['base_url']}/app"])
    return heading, _layout(heading, heading, body), text


def test(name: str = "Team", **_):
    a = _app()
    heading = "MapleJourney email is working \u2705"
    body = (
        f"<p style='margin:0 0 14px 0;'>This is a test email confirming that MapleJourney's SMTP is correctly "
        f"configured and branded emails are sending successfully.</p>"
        f"<p style='margin:0;color:#64748b;font-size:13px;'>Sent from {a['name']} &lt;{os.environ.get('SMTP_FROM_EMAIL','')}&gt;.</p>"
    )
    text = _text(["MapleJourney email is working.", "SMTP is correctly configured."])
    return heading, _layout("MapleJourney SMTP test.", heading, body), text


_TEMPLATES = {
    "welcome": welcome,
    "password_reset": password_reset,
    "password_changed": password_changed,
    "payment_confirmation": payment_confirmation,
    "onboarding_complete": onboarding_complete,
    "account_deleted": account_deleted,
    "announcement": announcement,
    "test": test,
}


def render(template: str, **ctx):
    fn = _TEMPLATES.get(template)
    if not fn:
        raise KeyError(f"Unknown email template: {template}")
    return fn(**ctx)
