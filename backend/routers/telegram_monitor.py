"""
Telegram Monitoring Endpoints
Real-time monitoring and alert management API
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.db import db
from core.security import get_current_user
from services.telegram_monitor import TelegramMonitoringService

logger = logging.getLogger("maplejourney.telegram.monitor.router")
router = APIRouter(prefix="/api/telegram/monitor", tags=["telegram-monitoring"])

# Initialize monitoring service
monitor = TelegramMonitoringService(db)


# ============================================================================
# MODELS
# ============================================================================

class AlertResponse(BaseModel):
    """Response model for alerts"""
    id: str
    type: str
    severity: str
    message: str
    timestamp: datetime
    acknowledged: bool


class DashboardResponse(BaseModel):
    """Dashboard data response"""
    timestamp: datetime
    metrics: dict
    active_alerts: List[AlertResponse]
    status: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/", response_model=DashboardResponse)
async def get_monitoring_dashboard(user = Depends(get_current_user)):
    """Get real-time monitoring dashboard"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    return await monitor.get_dashboard_data()


@router.get("/alerts")
async def get_alerts(
    limit: int = 50,
    severity: str = None,
    acknowledged: bool = None,
    user = Depends(get_current_user),
):
    """Get all alerts with optional filters"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    alerts = await monitor.get_alerts(
        limit=limit,
        severity=severity,
        acknowledged=acknowledged
    )

    return {
        "total": len(alerts),
        "alerts": [
            {
                "id": str(a.pop("_id")),
                **a
            }
            for a in alerts
        ]
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user = Depends(get_current_user),
):
    """Acknowledge/dismiss an alert"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    success = await monitor.acknowledge_alert(alert_id)

    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "message": "Alert acknowledged",
        "alert_id": alert_id,
        "acknowledged_at": datetime.utcnow().isoformat()
    }


@router.get("/trends")
async def get_trend_data(
    days: int = 7,
    user = Depends(get_current_user),
):
    """Get historical trend data"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 90")

    return await monitor.get_trend_data(days=days)


@router.post("/collect-metrics")
async def collect_metrics_now(user = Depends(get_current_user)):
    """Manually trigger metrics collection"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    metrics = await monitor.collect_metrics()

    return {
        "message": "Metrics collected",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "collections_today": metrics.get("collections_today"),
            "active_sessions": metrics.get("active_sessions"),
            "avg_completion_time": metrics.get("avg_completion_time")
        }
    }


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@router.get("/health")
async def monitoring_health():
    """Check monitoring service health"""
    try:
        # Test database connection
        latest = await db["telegram_metrics"].find_one({}, sort=[("timestamp", -1)])
        
        return {
            "status": "healthy",
            "service": "telegram_monitor",
            "database": "connected",
            "last_metrics": latest.get("timestamp").isoformat() if latest else None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "telegram_monitor",
            "error": str(e)
        }
