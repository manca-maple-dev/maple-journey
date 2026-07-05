"""
Telegram Data Collection Monitoring Dashboard
Real-time backend service for collecting and publishing metrics
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from enum import Enum

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("maplejourney.telegram.monitor")


class MetricType(Enum):
    """Types of metrics we track"""
    COLLECTIONS_TODAY = "collections_today"
    ACTIVE_SESSIONS = "active_sessions"
    AVG_COMPLETION_TIME = "avg_completion_time"
    FORM_DISTRIBUTION = "form_distribution"
    FIELD_COMPLETION = "field_completion"
    HOURLY_TREND = "hourly_trend"
    ERROR_RATE = "error_rate"
    USER_RETENTION = "user_retention"


class TelegramMonitoringService:
    """
    Real-time monitoring service for Telegram data collection
    Tracks metrics, generates alerts, and provides dashboard data
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collected_data = db["telegram_collected_data"]
        self.user_sessions = db["telegram_user_sessions"]
        self.metrics = db["telegram_metrics"]
        self.alerts = db["telegram_alerts"]

    async def start_monitoring(self, interval_seconds: int = 60):
        """Start real-time monitoring loop"""
        logger.info(f"🔍 Monitoring service started (interval: {interval_seconds}s)")
        
        while True:
            try:
                await self.collect_metrics()
                await self.check_alerts()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Monitoring error: {e}", exc_info=True)
                await asyncio.sleep(5)

    # ========================================================================
    # CORE METRICS COLLECTION
    # ========================================================================

    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect all metrics"""
        timestamp = datetime.utcnow()
        
        metrics = {
            "timestamp": timestamp,
            "collections_today": await self._get_collections_today(),
            "active_sessions": await self._get_active_sessions(),
            "avg_completion_time": await self._get_avg_completion_time(),
            "form_distribution": await self._get_form_distribution(),
            "field_completion": await self._get_field_completion(),
            "hourly_trend": await self._get_hourly_trend(),
            "error_rate": await self._get_error_rate(),
            "user_retention": await self._get_user_retention(),
        }
        
        # Store metrics
        await self.metrics.insert_one(metrics)
        
        # Keep only last 7 days of metrics
        week_ago = timestamp - timedelta(days=7)
        await self.metrics.delete_many({"timestamp": {"$lt": week_ago}})
        
        return metrics

    async def _get_collections_today(self) -> Dict[str, int]:
        """Get number of collections today"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {
                "$match": {
                    "collected_at": {"$gte": today_start},
                    "status": "completed"
                }
            },
            {
                "$group": {
                    "_id": "$form_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = await self.collected_data.aggregate(pipeline).to_list(None)
        return {r["_id"]: r["count"] for r in results}

    async def _get_active_sessions(self) -> int:
        """Get number of active sessions in last 24 hours"""
        day_ago = datetime.utcnow() - timedelta(days=1)
        
        count = await self.user_sessions.count_documents({
            "started_at": {"$gte": day_ago},
            "$or": [
                {"status": "in_progress"},
                {"status": "waiting_input"}
            ]
        })
        
        return count

    async def _get_avg_completion_time(self) -> float:
        """Get average time to complete form (in seconds)"""
        pipeline = [
            {
                "$match": {"status": "completed"}
            },
            {
                "$addFields": {
                    "completion_time": {
                        "$subtract": ["$completed_at", "$started_at"]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "avg_time": {"$avg": "$completion_time"}
                }
            }
        ]
        
        results = await self.user_sessions.aggregate(pipeline).to_list(1)
        return results[0]["avg_time"] / 1000 if results else 0  # Convert to seconds

    async def _get_form_distribution(self) -> Dict[str, int]:
        """Get distribution of form types"""
        pipeline = [
            {
                "$group": {
                    "_id": "$form_type",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        results = await self.collected_data.aggregate(pipeline).to_list(None)
        return {r["_id"]: r["count"] for r in results}

    async def _get_field_completion(self) -> Dict[str, float]:
        """Get completion rate for each field (0-100%)"""
        total = await self.collected_data.count_documents({"status": "completed"})
        
        if total == 0:
            return {}
        
        fields = [
            "email", "phone", "address", "full_name",
            "immigration_status", "annual_income", "dependent_children"
        ]
        
        completion = {}
        for field in fields:
            count = await self.collected_data.count_documents({
                "status": "completed",
                f"collected_data.{field}": {"$exists": True}
            })
            completion[field] = round((count / total) * 100, 2)
        
        return completion

    async def _get_hourly_trend(self) -> Dict[str, int]:
        """Get collections per hour for last 24 hours"""
        day_ago = datetime.utcnow() - timedelta(days=1)
        
        pipeline = [
            {
                "$match": {
                    "collected_at": {"$gte": day_ago},
                    "status": "completed"
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d %H:00",
                            "date": "$collected_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        results = await self.collected_data.aggregate(pipeline).to_list(None)
        return {r["_id"]: r["count"] for r in results}

    async def _get_error_rate(self) -> Dict[str, float]:
        """Get error rate by error type"""
        total_sessions = await self.user_sessions.count_documents({})
        
        error_types = {
            "validation_error": 0,
            "timeout": 0,
            "user_cancelled": 0,
            "other": 0
        }
        
        if total_sessions == 0:
            return {k: 0.0 for k in error_types.keys()}
        
        for error_type in error_types.keys():
            count = await self.user_sessions.count_documents({
                "status": error_type
            })
            error_types[error_type] = round((count / total_sessions) * 100, 2)
        
        return error_types

    async def _get_user_retention(self) -> Dict[str, Any]:
        """Get user retention metrics"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        today_users = await self.collected_data.distinct(
            "user_id",
            {"collected_at": {"$gte": today}}
        )
        
        yesterday_users = await self.collected_data.distinct(
            "user_id",
            {"collected_at": {"$gte": yesterday, "$lt": today}}
        )
        
        week_users = await self.collected_data.distinct(
            "user_id",
            {"collected_at": {"$gte": week_ago}}
        )
        
        month_users = await self.collected_data.distinct(
            "user_id",
            {"collected_at": {"$gte": month_ago}}
        )
        
        return {
            "today_unique": len(today_users),
            "yesterday_unique": len(yesterday_users),
            "week_unique": len(week_users),
            "month_unique": len(month_users),
            "repeat_users": len(set(yesterday_users) & set(today_users)),
        }

    # ========================================================================
    # ALERT SYSTEM
    # ========================================================================

    async def check_alerts(self):
        """Check for alert conditions"""
        metrics = await self.metrics.find_one({}, sort=[("timestamp", -1)])
        
        if not metrics:
            return
        
        # Check alert conditions
        await self._check_low_completion()
        await self._check_high_error_rate()
        await self._check_inactivity()
        await self._check_anomalies(metrics)

    async def _check_low_completion(self):
        """Alert if completion rate drops below threshold"""
        day_ago = datetime.utcnow() - timedelta(days=1)
        
        started = await self.user_sessions.count_documents({
            "started_at": {"$gte": day_ago}
        })
        
        completed = await self.collected_data.count_documents({
            "collected_at": {"$gte": day_ago},
            "status": "completed"
        })
        
        if started > 0:
            completion_rate = (completed / started) * 100
            
            if completion_rate < 50:
                await self._create_alert(
                    alert_type="LOW_COMPLETION_RATE",
                    severity="warning",
                    message=f"Completion rate dropped to {completion_rate:.1f}%",
                    metrics={"completion_rate": completion_rate, "completed": completed}
                )

    async def _check_high_error_rate(self):
        """Alert if error rate exceeds threshold"""
        total = await self.user_sessions.count_documents({})
        
        if total == 0:
            return
        
        errors = await self.user_sessions.count_documents({
            "$or": [
                {"status": "validation_error"},
                {"status": "timeout"},
                {"status": "error"}
            ]
        })
        
        error_rate = (errors / total) * 100
        
        if error_rate > 10:
            await self._create_alert(
                alert_type="HIGH_ERROR_RATE",
                severity="critical",
                message=f"Error rate reached {error_rate:.1f}%",
                metrics={"error_rate": error_rate, "total_errors": errors}
            )

    async def _check_inactivity(self):
        """Alert if no activity for extended period"""
        threshold = datetime.utcnow() - timedelta(hours=2)
        
        recent = await self.collected_data.find_one(
            {},
            sort=[("collected_at", -1)]
        )
        
        if recent and recent["collected_at"] < threshold:
            await self._create_alert(
                alert_type="INACTIVITY",
                severity="info",
                message="No data collected in last 2 hours",
                metrics={"last_collection": recent["collected_at"].isoformat()}
            )

    async def _check_anomalies(self, current_metrics: Dict[str, Any]):
        """Detect anomalies using statistical analysis"""
        # Get previous metrics (last 7 days)
        week_ago = current_metrics["timestamp"] - timedelta(days=7)
        
        historical = await self.metrics.find({
            "timestamp": {"$gte": week_ago}
        }).to_list(None)
        
        if len(historical) < 3:
            return
        
        # Calculate average and std dev
        today_count = current_metrics["collections_today"]
        avg_count = sum(m.get("collections_today", {}).get("profile", 0) for m in historical) / len(historical)
        
        if avg_count > 0 and today_count < (avg_count * 0.5):
            await self._create_alert(
                alert_type="UNUSUAL_DROP",
                severity="warning",
                message=f"Collections dropped 50% below average ({today_count} vs {avg_count:.0f})",
                metrics={"current": today_count, "average": avg_count}
            )

    async def _create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        metrics: Dict[str, Any]
    ):
        """Create an alert"""
        alert = {
            "timestamp": datetime.utcnow(),
            "type": alert_type,
            "severity": severity,
            "message": message,
            "metrics": metrics,
            "acknowledged": False,
        }
        
        # Check if similar alert exists (within last hour)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        existing = await self.alerts.find_one({
            "type": alert_type,
            "timestamp": {"$gte": hour_ago},
            "acknowledged": False
        })
        
        if not existing:
            await self.alerts.insert_one(alert)
            logger.warning(f"🚨 Alert created: {alert_type} - {message}")

    # ========================================================================
    # DATA RETRIEVAL
    # ========================================================================

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        latest_metrics = await self.metrics.find_one({}, sort=[("timestamp", -1)])
        
        active_alerts = await self.alerts.find({
            "acknowledged": False
        }).sort("timestamp", -1).to_list(10)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": latest_metrics or {},
            "active_alerts": active_alerts or [],
            "status": "operational"
        }

    async def get_trend_data(self, days: int = 7) -> Dict[str, Any]:
        """Get historical trend data"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        historical = await self.metrics.find({
            "timestamp": {"$gte": start_date}
        }).sort("timestamp", 1).to_list(None)
        
        return {
            "period_days": days,
            "data_points": len(historical),
            "data": historical
        }

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark alert as acknowledged"""
        from bson import ObjectId
        
        result = await self.alerts.update_one(
            {"_id": ObjectId(alert_id)},
            {"$set": {
                "acknowledged": True,
                "acknowledged_at": datetime.utcnow()
            }}
        )
        
        return result.modified_count > 0

    async def get_alerts(
        self,
        limit: int = 50,
        severity: str = None,
        acknowledged: bool = None
    ) -> List[Dict[str, Any]]:
        """Get alerts with optional filters"""
        query = {}
        
        if severity:
            query["severity"] = severity
        
        if acknowledged is not None:
            query["acknowledged"] = acknowledged
        
        alerts = await self.alerts.find(query).sort(
            "timestamp", -1
        ).to_list(limit)
        
        return alerts
