"""Observability endpoints for runtime metrics and launch health gates."""

from datetime import datetime, timezone
import os
import time

from fastapi import APIRouter, HTTPException

from core.db import db

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/health")
async def ops_health():
    """Composite health check used by CI/CD gate and uptime probes."""
    checks = {
        "api": "ok",
        "db": "unknown",
        "messaging": "unknown",
    }

    try:
        await db.command("ping")
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "fail"

    twilio_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"]
    checks["messaging"] = "ok" if all(os.getenv(k) for k in twilio_vars) else "degraded"

    status = "ok" if checks["db"] == "ok" else "degraded"
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/metrics")
async def ops_metrics():
    """Runtime metrics for dashboards and alerting sinks."""
    from server import app

    metrics = getattr(app.state, "runtime_metrics", {})
    started_at = getattr(app.state, "started_at", None)
    uptime_seconds = int(time.time() - started_at) if started_at else 0

    requests_total = int(metrics.get("requests_total", 0))
    errors_total = int(metrics.get("errors_total", 0))
    latency_sum_ms = float(metrics.get("latency_sum_ms", 0.0))

    avg_latency_ms = (latency_sum_ms / requests_total) if requests_total else 0.0
    error_rate = (errors_total / requests_total) if requests_total else 0.0

    webhook_dedup_24h = await db.webhook_message_dedup.count_documents(
        {
            "created_at": {
                "$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            }
        }
    )

    return {
        "uptime_seconds": uptime_seconds,
        "requests_total": requests_total,
        "errors_total": errors_total,
        "error_rate": round(error_rate, 6),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "max_latency_ms": round(float(metrics.get("latency_max_ms", 0.0)), 2),
        "webhook_dedup_markers_today": webhook_dedup_24h,
    }


@router.get("/ready")
async def ops_ready():
    """Readiness gate for deployment rollout checks."""
    try:
        await db.command("ping")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database not ready") from exc

    return {"ready": True}
