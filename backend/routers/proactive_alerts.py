"""
Proactive Alerts API Endpoints
Endpoints for retrieving, dismissing, and managing deadline alerts
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from core.security import get_current_user
from services.proactive_triggers import proactive_scheduler
from services.deadline_engine import AlertSeverity
from core.db import db
import logging

logger = logging.getLogger("maple.alerts_api")
router = APIRouter(prefix="/assistant/proactive-alerts", tags=["proactive"])


@router.get("/")
async def get_proactive_alerts(user: dict = Depends(get_current_user)):
    """
    Get all proactive alerts for the current user.
    Returns both critical/urgent and informational alerts.
    """
    try:
        deadlines_doc = await db.user_deadlines.find_one({"user_id": str(user["_id"])})
        
        if not deadlines_doc:
            return {"alerts": []}

        triggers = deadlines_doc.get("triggers", [])
        
        # Sort by severity and days_until
        alerts = []
        for trigger in triggers:
            if trigger.get("dismissed_at"):
                continue  # Skip dismissed
            
            from services.deadline_engine import DeadlineType
            from datetime import datetime
            
            try:
                due_date = datetime.fromisoformat(trigger["due_date"])
                now = datetime.now(datetime.now().astimezone().tzinfo or datetime.now().tzinfo)
                days_until = (due_date - now).days
                
                # Determine severity
                if days_until <= 7:
                    severity = AlertSeverity.CRITICAL.value
                elif days_until <= 30:
                    severity = AlertSeverity.URGENT.value
                elif days_until <= 90:
                    severity = AlertSeverity.ATTENTION.value
                else:
                    severity = AlertSeverity.INFO.value
                
                alerts.append({
                    "id": trigger.get("deadline_type"),
                    "type": trigger.get("deadline_type"),
                    "severity": severity,
                    "description": trigger.get("description"),
                    "due_date": trigger.get("due_date"),
                    "days_until": max(0, days_until),
                    "context": trigger.get("context", {}),
                    "surfaced_in_chat": trigger.get("surfaced_in_chat", False),
                })
            except Exception as e:
                logger.warning(f"Error processing trigger: {e}")

        # Sort by severity (critical first) then days_until
        severity_order = {"critical": 0, "urgent": 1, "attention": 2, "info": 3}
        alerts.sort(key=lambda a: (severity_order.get(a["severity"], 4), a["days_until"]))
        
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.post("/{alert_type}/dismiss")
async def dismiss_alert(alert_type: str, user: dict = Depends(get_current_user)):
    """
    Dismiss a specific alert for the user.
    """
    try:
        await db.user_deadlines.update_one(
            {"user_id": str(user["_id"])},
            {
                "$set": {
                    "triggers.$[elem].dismissed_at": datetime.now(timezone.utc).isoformat(),
                }
            },
            array_filters=[{"elem.deadline_type": alert_type}],
        )
        return {"status": "dismissed"}
    except Exception as e:
        logger.error(f"Failed to dismiss alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to dismiss alert")


@router.get("/next")
async def get_next_alert(user: dict = Depends(get_current_user)):
    """
    Get the next urgent alert to surface in chat.
    """
    try:
        if not proactive_scheduler:
            return {"alert": None}

        alert_message = await proactive_scheduler.get_next_alert_for_user(str(user["_id"]))
        return {"alert": alert_message}
    except Exception as e:
        logger.error(f"Failed to get next alert: {e}")
        return {"alert": None}
