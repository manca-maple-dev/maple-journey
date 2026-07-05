"""
Telegram Data Collection Router
RESTful API endpoints for Telegram integration and data management
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any

from core.db import db
from core.security import get_current_user
from services.telegram_collector import TelegramDataCollector

logger = logging.getLogger("maplejourney.telegram.router")
router = APIRouter(prefix="/telegram", tags=["telegram"])

# Get collector instance
telegram_collector = TelegramDataCollector(
    db=db,
    bot_token="",  # Will be set from environment
)


# ============================================================================
# MODELS
# ============================================================================

class CollectedDataResponse(BaseModel):
    """Response model for collected data"""
    id: str = Field(..., alias="_id")
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    collected_data: Dict[str, Any]
    form_type: str
    collected_at: datetime
    status: str

    class Config:
        populate_by_name = True


class CollectionStatsResponse(BaseModel):
    """Statistics about data collection"""
    total_records: int
    completed: int
    today: int
    by_form_type: Dict[str, int]
    collected_at: datetime


class DataExportRequest(BaseModel):
    """Request for data export"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    form_type: Optional[str] = None
    limit: int = Field(1000, ge=1, le=10000)


class TelegramWebhookPayload(BaseModel):
    """Telegram webhook payload"""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None


class CollectionMetricsResponse(BaseModel):
    """Real-time collection metrics"""
    active_sessions: int
    completed_today: int
    avg_completion_time_seconds: float
    forms_by_type: Dict[str, int]
    top_fields: Dict[str, int]
    hourly_breakdown: Dict[str, int]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/status", response_model=CollectionStatsResponse)
async def get_collection_status(user = Depends(get_current_user)):
    """Get real-time data collection statistics"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    stats = await telegram_collector.get_collection_stats()
    return CollectionStatsResponse(**stats)


@router.get("/data/{user_id}", response_model=CollectedDataResponse)
async def get_user_data(
    user_id: int,
    current_user = Depends(get_current_user),
):
    """Get collected data for a specific user"""
    # Users can only view their own data, admins can view any
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    is_admin = current_user.get("is_admin", False)
    if not is_admin and current_user.get("telegram_user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    data = await telegram_collector.collected_data.find_one(
        {"user_id": user_id},
        sort=[("collected_at", -1)],
    )

    if not data:
        raise HTTPException(status_code=404, detail="No data found for user")

    data["id"] = str(data.pop("_id"))
    return CollectedDataResponse(**data)


@router.get("/latest", response_model=List[CollectedDataResponse])
async def get_latest_collections(
    limit: int = 50,
    user = Depends(get_current_user),
):
    """Get latest collected data entries"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    data = await telegram_collector.collected_data.find(
        {"status": "completed"},
        sort=[("collected_at", -1)],
    ).to_list(limit)

    return [
        CollectedDataResponse(**{**d, "id": str(d.pop("_id"))})
        for d in data
    ]


@router.get("/latest/public")
async def get_latest_collections_public(
    limit: int = 10,
):
    """Get latest collected data entries (Public - no auth required)"""
    data = await telegram_collector.collected_data.find(
        {"status": "completed"},
        sort=[("collected_at", -1)],
    ).to_list(limit)

    return [
        {**d, "_id": str(d["_id"]), "collected_at": d.get("collected_at", "").isoformat() if d.get("collected_at") else ""}
        for d in data
    ]


@router.post("/export")
async def export_data(
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
):
    """Export collected data (CSV format)"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Fetch data based on filters
    query = {"status": "completed"}
    if request.form_type:
        query["form_type"] = request.form_type
    if request.start_date or request.end_date:
        query["collected_at"] = {}
        if request.start_date:
            query["collected_at"]["$gte"] = request.start_date
        if request.end_date:
            query["collected_at"]["$lte"] = request.end_date

    data = await telegram_collector.collected_data.find(query).to_list(request.limit)

    # Generate CSV
    import csv
    import io

    output = io.StringIO()
    if data:
        fieldnames = ["user_id", "username", "collected_at", "form_type"] + list(
            data[0].get("collected_data", {}).keys()
        )
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for record in data:
            row = {
                "user_id": record["user_id"],
                "username": record.get("username", ""),
                "collected_at": record["collected_at"].isoformat(),
                "form_type": record["form_type"],
            }
            row.update(record.get("collected_data", {}))
            writer.writerow(row)

    csv_content = output.getvalue()
    return {
        "total_records": len(data),
        "csv_url": f"/api/telegram/export/download?start={request.start_date}&end={request.end_date}",
        "preview": csv_content[:500] + ("..." if len(csv_content) > 500 else ""),
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/metrics", response_model=CollectionMetricsResponse)
async def get_collection_metrics(user = Depends(get_current_user)):
    """Get real-time collection metrics and insights"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Active sessions (last 24 hours)
    day_ago = datetime.utcnow() - timedelta(days=1)
    active_sessions = await telegram_collector.user_sessions.count_documents(
        {"started_at": {"$gte": day_ago}, "status": "in_progress"}
    )

    # Completed today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today = await telegram_collector.collected_data.count_documents(
        {"collected_at": {"$gte": today_start}, "status": "completed"}
    )

    # Average completion time
    completed = await telegram_collector.collected_data.find(
        {"status": "completed"}
    ).to_list(100)

    avg_time = 0
    if completed:
        total_time = sum(
            (d.get("collected_at", datetime.utcnow()) - d.get("started_at", datetime.utcnow())).total_seconds()
            for d in completed
        )
        avg_time = total_time / len(completed)

    # Forms by type
    forms_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": "$form_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    forms_data = await telegram_collector.collected_data.aggregate(forms_pipeline).to_list(None)
    forms_by_type = {f["_id"]: f["count"] for f in forms_data}

    # Top fields
    fields_pipeline = [
        {"$match": {"status": "completed"}},
        {"$project": {"fields": {"$objectToArray": "$collected_data"}}},
        {"$unwind": "$fields"},
        {"$group": {"_id": "$fields.k", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    fields_data = await telegram_collector.collected_data.aggregate(fields_pipeline).to_list(None)
    top_fields = {f["_id"]: f["count"] for f in fields_data}

    # Hourly breakdown for today
    hourly_pipeline = [
        {"$match": {"collected_at": {"$gte": today_start}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%H:00",
                        "date": "$collected_at",
                    }
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    hourly_data = await telegram_collector.collected_data.aggregate(hourly_pipeline).to_list(None)
    hourly_breakdown = {h["_id"]: h["count"] for h in hourly_data}

    return CollectionMetricsResponse(
        active_sessions=active_sessions,
        completed_today=completed_today,
        avg_completion_time_seconds=avg_time,
        forms_by_type=forms_by_type,
        top_fields=top_fields,
        hourly_breakdown=hourly_breakdown,
    )


@router.post("/webhook")
async def telegram_webhook(payload: TelegramWebhookPayload):
    """Receive updates from Telegram webhook"""
    # This is handled by the telegram-python-bot library
    # Just acknowledge receipt
    logger.info(f"Webhook update received: {payload.update_id}")
    return {"ok": True}


@router.get("/dashboard")
async def get_dashboard_data(user = Depends(get_current_user)):
    """Get comprehensive dashboard data"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    stats = await telegram_collector.get_collection_stats()
    metrics = await get_collection_metrics(user)

    return {
        "statistics": stats,
        "metrics": metrics,
        "dashboard_generated_at": datetime.utcnow().isoformat(),
    }


@router.post("/data/{user_id}/verify")
async def verify_collected_data(
    user_id: int,
    user = Depends(get_current_user),
):
    """Mark collected data as verified"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await telegram_collector.collected_data.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "verified": True,
                "verified_at": datetime.utcnow(),
                "verified_by": user.get("user_id"),
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Data not found")

    return {
        "message": "Data verified successfully",
        "user_id": user_id,
        "verified_at": datetime.utcnow().isoformat(),
    }


@router.get("/users/{user_id}/history")
async def get_user_collection_history(
    user_id: int,
    limit: int = 10,
    user = Depends(get_current_user),
):
    """Get collection history for a specific user"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    history = await telegram_collector.collected_data.find(
        {"user_id": user_id}
    ).sort("collected_at", -1).to_list(limit)

    return {
        "user_id": user_id,
        "total_collections": len(history),
        "collections": [
            {
                "id": str(h.pop("_id")),
                "form_type": h.get("form_type"),
                "collected_at": h.get("collected_at"),
                "status": h.get("status"),
                "verified": h.get("verified", False),
            }
            for h in history
        ],
    }


@router.delete("/data/{record_id}")
async def delete_collected_data(
    record_id: str,
    user = Depends(get_current_user),
):
    """Delete a collected data record (admin only)"""
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    from bson import ObjectId

    result = await telegram_collector.collected_data.delete_one(
        {"_id": ObjectId(record_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Record not found")

    return {
        "message": "Record deleted successfully",
        "record_id": record_id,
        "deleted_at": datetime.utcnow().isoformat(),
    }
