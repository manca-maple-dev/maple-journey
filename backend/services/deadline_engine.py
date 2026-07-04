"""
Deadline Engine — Proactive triggers for visa/passport/PR/tax deadlines.
Runs as background scheduler, evaluates each user's upcoming events.
Surfaces alerts naturally in chat context.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from enum import Enum
import json

logger = logging.getLogger("maple.deadline_engine")


class DeadlineType(str, Enum):
    VISA_EXPIRY = "visa_expiry"
    PASSPORT_EXPIRY = "passport_expiry"
    PR_ELIGIBILITY = "pr_eligibility"
    TAX_FILING = "tax_filing"
    WORK_PERMIT_RENEWAL = "work_permit_renewal"
    HEALTH_INSURANCE = "health_insurance"
    DRIVER_LICENSE = "driver_license"
    POLICY_CHANGE = "policy_change"
    CITIZENSHIP_ELIGIBLE = "citizenship_eligible"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"  # 0-7 days
    URGENT = "urgent"      # 8-30 days
    ATTENTION = "attention"  # 31-90 days
    INFO = "info"           # 90+ days


class DeadlineTrigger:
    """Single deadline event for a user."""

    def __init__(
        self,
        user_id: str,
        deadline_type: DeadlineType,
        due_date: datetime,
        description: str,
        context: Dict = None,
    ):
        self.user_id = user_id
        self.deadline_type = deadline_type
        self.due_date = due_date
        self.description = description
        self.context = context or {}
        self.created_at = datetime.now(timezone.utc)
        self.dismissed_at: Optional[datetime] = None
        self.surfaced_in_chat = False

    def days_until(self) -> int:
        """Days remaining before deadline."""
        delta = self.due_date - datetime.now(timezone.utc)
        return max(0, delta.days)

    def severity(self) -> AlertSeverity:
        """Determine urgency level."""
        days = self.days_until()
        if days <= 7:
            return AlertSeverity.CRITICAL
        elif days <= 30:
            return AlertSeverity.URGENT
        elif days <= 90:
            return AlertSeverity.ATTENTION
        return AlertSeverity.INFO

    def chat_message(self) -> str:
        """Generate natural chat message for this deadline."""
        days = self.days_until()
        severity = self.severity()

        templates = {
            DeadlineType.VISA_EXPIRY: (
                f"🚨 **Your {self.context.get('visa_type', 'visa')} expires in {days} days** ({self.due_date.strftime('%B %d, %Y')}). "
                f"If you're planning to stay, start renewal paperwork NOW. "
                f"After expiry, you'll have 'implied status' while your extension processes, but you can't work. "
                f"Need help with the renewal? I can walk you through the steps."
            ),
            DeadlineType.PASSPORT_EXPIRY: (
                f"📋 Your passport expires in {days} days. This matters because: "
                f"• International travel requires 6+ months validity. "
                f"• Some immigration applications need a valid passport. "
                f"Start consulate renewal now — typical processing: 4-6 weeks."
            ),
            DeadlineType.PR_ELIGIBILITY: (
                f"🎉 **You're now eligible for Canadian Permanent Residency!** "
                f"You've met the physical presence requirement ({self.context.get('years_in_canada', '?')} years). "
                f"Next: Take a language test, file taxes, submit your PR application. "
                f"Want me to break down the exact steps?"
            ),
            DeadlineType.TAX_FILING: (
                f"💰 Tax deadline: {self.due_date.strftime('%B %d, %Y')} ({days} days away). "
                f"As a {self.context.get('status', 'newcomer')}, you must file because: "
                f"• Unlock Canada Child Benefit (CCB). "
                f"• Avoid penalties ($200+ for late filing). "
                f"Free help at VITA sites or call 211."
            ),
            DeadlineType.WORK_PERMIT_RENEWAL: (
                f"⏰ Your work permit expires in {days} days ({self.due_date.strftime('%B %d, %Y')}). "
                f"Start your extension application 180 days before expiry to maintain 'implied status'. "
                f"What's your employment situation? I can help customize your renewal checklist."
            ),
            DeadlineType.CITIZENSHIP_ELIGIBLE: (
                f"🍁 **You're now eligible for citizenship!** "
                f"You've lived in Canada for the required time. "
                f"Next steps: language test, application fee, oath ceremony. "
                f"Processing time: 12-18 months. Ready to start?"
            ),
        }

        return templates.get(
            self.deadline_type,
            f"{self.description} ({days} days remaining)"
        )

    def to_dict(self) -> Dict:
        """Serialize for storage."""
        return {
            "user_id": self.user_id,
            "deadline_type": self.deadline_type.value,
            "due_date": self.due_date.isoformat(),
            "description": self.description,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
            "surfaced_in_chat": self.surfaced_in_chat,
        }


class DeadlineEngine:
    """
    Evaluates user profiles and detects upcoming deadlines.
    Run as background task: every 6 hours, scan all users.
    Store results in `user_deadlines` collection.
    """

    async def evaluate_user(self, user: Dict) -> List[DeadlineTrigger]:
        """Scan user profile for all upcoming deadlines."""
        triggers = []

        # VISA EXPIRY
        if "status" in user and "visa_expiry" in user:
            visa_expiry = user.get("visa_expiry")
            if visa_expiry:
                try:
                    due = datetime.fromisoformat(visa_expiry)
                    trigger = DeadlineTrigger(
                        user_id=str(user["_id"]),
                        deadline_type=DeadlineType.VISA_EXPIRY,
                        due_date=due,
                        description=f"Visa expires: {user.get('status', 'unknown')}",
                        context={"visa_type": user.get("status", "visa")},
                    )
                    if trigger.days_until() <= 365:
                        triggers.append(trigger)
                except Exception as e:
                    logger.warning(f"Failed to parse visa_expiry for user {user['_id']}: {e}")

        # PASSPORT EXPIRY
        if "passport_expiry" in user:
            try:
                due = datetime.fromisoformat(user["passport_expiry"])
                trigger = DeadlineTrigger(
                    user_id=str(user["_id"]),
                    deadline_type=DeadlineType.PASSPORT_EXPIRY,
                    due_date=due,
                    description="Passport expires",
                )
                if trigger.days_until() <= 365:
                    triggers.append(trigger)
            except Exception as e:
                logger.warning(f"Failed to parse passport_expiry for user {user['_id']}: {e}")

        # PR/CITIZENSHIP ELIGIBILITY
        if "created_at" in user:
            try:
                arrival_date = datetime.fromisoformat(user["created_at"])
                years_in_canada = (datetime.now(timezone.utc) - arrival_date).days / 365.25

                # PR eligibility (3 years physical presence)
                if 2.9 <= years_in_canada <= 3.2 and user.get("tier") != "family":
                    pr_eligible_date = arrival_date + timedelta(days=365 * 3)
                    trigger = DeadlineTrigger(
                        user_id=str(user["_id"]),
                        deadline_type=DeadlineType.PR_ELIGIBILITY,
                        due_date=pr_eligible_date,
                        description="Now eligible for PR",
                        context={"years_in_canada": round(years_in_canada, 1)},
                    )
                    triggers.append(trigger)

                # Citizenship eligibility (3 years PR)
                if years_in_canada >= 3.0:
                    trigger = DeadlineTrigger(
                        user_id=str(user["_id"]),
                        deadline_type=DeadlineType.CITIZENSHIP_ELIGIBLE,
                        due_date=datetime.now(timezone.utc),
                        description="Eligible for citizenship",
                    )
                    triggers.append(trigger)
            except Exception as e:
                logger.warning(f"Failed to calculate eligibility for user {user['_id']}: {e}")

        # TAX FILING DEADLINE (April 30 in Canada, May 15 for US)
        if user.get("country") in ["Canada", "US"]:
            deadline_month = 4 if user.get("country") == "Canada" else 5
            deadline_day = 30 if user.get("country") == "Canada" else 15
            today = datetime.now(timezone.utc)
            year = today.year if today.month < deadline_month else today.year + 1
            tax_deadline = datetime(year, deadline_month, deadline_day, tzinfo=timezone.utc)

            trigger = DeadlineTrigger(
                user_id=str(user["_id"]),
                deadline_type=DeadlineType.TAX_FILING,
                due_date=tax_deadline,
                description=f"Tax filing deadline ({user.get('country')})",
                context={"status": user.get("status", "newcomer"), "country": user.get("country")},
            )
            if trigger.days_until() <= 180:  # Alert up to 6 months before
                triggers.append(trigger)

        return triggers

    async def get_urgent_for_user(self, user_id: str, db) -> List[DeadlineTrigger]:
        """Get deadlines marked CRITICAL or URGENT for this user."""
        user = await db.users.find_one({"_id": user_id})
        if not user:
            return []

        all_triggers = await self.evaluate_user(user)
        urgent = [t for t in all_triggers if t.severity() in [AlertSeverity.CRITICAL, AlertSeverity.URGENT]]
        return urgent


deadline_engine = DeadlineEngine()
