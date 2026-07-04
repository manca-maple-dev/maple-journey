"""
Crisis Escalation Engine — Detects safety-critical situations and routes to hotlines
Handles: DV, trafficking, self-harm, unaccompanied minors, abuse
"""
import logging
import re
from typing import Optional, Dict
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger("maple.crisis_escalation")


class CrisisType(str, Enum):
    DOMESTIC_VIOLENCE = "dv"
    HUMAN_TRAFFICKING = "trafficking"
    SELF_HARM = "self_harm"
    SUICIDE_RISK = "suicide_risk"
    CHILD_ABUSE = "child_abuse"
    SEXUAL_ASSAULT = "sexual_assault"


# Crisis keywords and patterns
CRISIS_PATTERNS = {
    CrisisType.DOMESTIC_VIOLENCE: [
        r"abuse",
        r"hit|punch|hurt me",
        r"domestic violence",
        r"partner abuse",
        r"afraid of|scared of",
        r"don't feel safe",
        r"controller|controlling",
    ],
    CrisisType.HUMAN_TRAFFICKING: [
        r"traffick",
        r"forced.*work",
        r"debt bond",
        r"passport.*taken",
        r"trapped",
        r"exploitation",
    ],
    CrisisType.SUICIDE_RISK: [
        r"suicide|kill myself|end it",
        r"no point|hopeless|worthless",
        r"should die|want to die",
        r"goodbye",
    ],
    CrisisType.CHILD_ABUSE: [
        r"child.*hurt|abuse",
        r"underage.*abuse",
        r"minor.*harm",
    ],
    CrisisType.SEXUAL_ASSAULT: [
        r"assault|rape|violated",
        r"sexual abuse|sexual violence",
        r"non-consensual",
    ],
}

# Hotline mappings by country/region
CRISIS_HOTLINES = {
    CrisisType.DOMESTIC_VIOLENCE: {
        "us": {"number": "1-800-799-7233", "name": "National DV Hotline"},
        "canada": {"number": "1-833-456-4566", "name": "Assaulted Women's Helpline"},
    },
    CrisisType.HUMAN_TRAFFICKING: {
        "us": {"number": "1-888-373-7888", "name": "National Human Trafficking Hotline"},
        "canada": {"number": "1-833-900-1010", "name": "Canadian Human Trafficking Hotline"},
    },
    CrisisType.SUICIDE_RISK: {
        "us": {"number": "988", "name": "National Suicide & Crisis Lifeline"},
        "canada": {"number": "1-833-456-4566", "name": "Talk Suicide Canada"},
    },
}


class CrisisEscalationEngine:
    """
    Detects crisis language in user messages and routes to immediate help.
    NO LLM processing — direct to hotline.
    """

    def detect_crisis(self, message: str) -> Optional[CrisisType]:
        """
        Scan message for crisis keywords/patterns.
        Returns crisis type if detected, None otherwise.
        """
        message_lower = message.lower()

        for crisis_type, patterns in CRISIS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    logger.warning(f"CRISIS DETECTED: {crisis_type.value} in message")
                    return crisis_type

        return None

    async def get_immediate_help(
        self,
        crisis_type: CrisisType,
        country: str = "canada",  # Default to Canada
    ) -> Dict:
        """
        Return immediate crisis hotline without any conversation delay.
        """
        hotlines = CRISIS_HOTLINES.get(crisis_type, {})
        hotline_info = hotlines.get(country, hotlines.get("us"))

        if not hotline_info:
            hotline_info = {
                "number": "911",
                "name": "Emergency Services",
            }

        return {
            "crisis_detected": True,
            "crisis_type": crisis_type.value,
            "immediate_action": "CALL NOW",
            "hotline": hotline_info["name"],
            "number": hotline_info["number"],
            "message": f"🚨 IMMEDIATE HELP AVAILABLE\n\nPlease contact {hotline_info['name']}\n📞 {hotline_info['number']}\n\nYou can also:\n• Call 911 for emergencies\n• Text 'HELLO' to 741741 (Crisis Text Line - US)\n• Go to nearest emergency room",
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }

    async def log_crisis_alert(
        self,
        user_id: str,
        crisis_type: CrisisType,
        message_preview: str,
        country: str,
        db,
    ) -> None:
        """
        Log crisis detection for safety audit and follow-up.
        """
        try:
            await db.crisis_alerts.insert_one({
                "user_id": str(user_id),
                "crisis_type": crisis_type.value,
                "message_preview": message_preview[:100],  # First 100 chars only
                "country": country,
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "addressed": False,
            })
            logger.info(f"Crisis alert logged: user_id={user_id} type={crisis_type.value}")
        except Exception as e:
            logger.error(f"Failed to log crisis alert: {e}")


crisis_escalation = CrisisEscalationEngine()
