"""Jobs search and discovery API routes.

Live job scraping, intelligent matching, and notifications.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId

from core.security import get_current_user
from services.jobs import (
    search_jobs,
    get_user_job_preferences,
    update_last_search,
    get_new_jobs_count,
    ensure_indexes as ensure_job_indexes,
)
from core.db import db, clean

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.on_event("startup")
async def startup_jobs():
    """Initialize job indexes on app startup."""
    await ensure_job_indexes()


@router.get("/search")
async def search_jobs_endpoint(
    user: dict = Depends(get_current_user),
    location: str = Query("Toronto", description="City or province"),
    keywords: Optional[str] = Query(None, description="Job title or keyword"),
    job_type: Optional[str] = Query(None, description="Full-time, Part-time, Contract"),
    experience_level: Optional[str] = Query(None, description="entry, mid, senior"),
    salary_min: Optional[int] = Query(None, description="Minimum salary"),
    salary_max: Optional[int] = Query(None, description="Maximum salary"),
    days_posted: Optional[int] = Query(30, description="Jobs posted in last N days"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    refresh: bool = Query(False, description="Force re-scrape (bypass 30min cache)"),
):
    """
    Search live jobs near user with intelligent filtering.
    
    **Smart features:**
    - Matches user's industry, skills, experience level
    - 25km radius filtering by location
    - Real-time re-scrape when stale or requested
    - Relevance scoring (0-100)
    - Auto-clears old caches
    
    **Response:** Sorted by relevance score (highest first)
    """
    try:
        user_id = str(user["_id"])
        jobs, total = await search_jobs(
            user_id=user_id,
            location=location,
            keywords=keywords,
            job_type=job_type,
            experience_level=experience_level,
            salary_min=salary_min,
            salary_max=salary_max,
            days_posted=days_posted,
            limit=limit,
            force_refresh=refresh,
        )
        
        # Track search for inactivity cleanup
        await update_last_search(user_id, location)
        
        return {
            "jobs": jobs,
            "total": total,
            "count": len(jobs),
            "location": location,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/new-count")
async def get_new_jobs_notification(
    user: dict = Depends(get_current_user),
    since_hours: int = Query(24, description="Check for jobs posted in last N hours"),
):
    """
    Get count of new jobs posted since last login (for notification badge).
    
    Used to show badge on dashboard: "3 new jobs in Toronto"
    """
    user_id = str(user["_id"])
    since = datetime.utcnow() - timedelta(hours=since_hours)
    
    count = await get_new_jobs_count(user_id, since)
    
    return {
        "new_jobs": count,
        "since": since.isoformat(),
        "message": f"{count} new job(s) in your area" if count > 0 else "No new jobs yet",
    }


@router.get("/preferences")
async def get_preferences(
    user: dict = Depends(get_current_user),
):
    """Get user's job search preferences (auto-initialized from profile)."""
    user_id = str(user["_id"])
    prefs = await get_user_job_preferences(user_id)
    return prefs


@router.put("/preferences")
async def update_preferences(
    user: dict = Depends(get_current_user),
    job_categories: Optional[List[str]] = None,
    experience_level: Optional[str] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    preferred_locations: Optional[List[str]] = None,
    job_types: Optional[List[str]] = None,
):
    """
    Update user's job search preferences.
    
    Used to remember user's filters and personalize future searches.
    """
    update_data = {}
    if job_categories is not None:
        update_data["job_categories"] = job_categories
    if experience_level is not None:
        update_data["experience_level"] = experience_level
    if salary_min is not None:
        update_data["salary_min"] = salary_min
    if salary_max is not None:
        update_data["salary_max"] = salary_max
    if preferred_locations is not None:
        update_data["preferred_locations"] = preferred_locations
    if job_types is not None:
        update_data["job_types"] = job_types
    
    user_id = str(user["_id"])
    if not update_data:
        return await get_user_job_preferences(user_id)
    
    result = await db.user_job_preferences.find_one_and_update(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True,
        return_document=True
    )
    
    return clean(result)


@router.get("/trending")
async def get_trending_jobs(
    user: dict = Depends(get_current_user),
    location: str = Query("Canada", description="City or province"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get trending/popular jobs in location (most viewed/applied).
    
    Great for showing "Jobs near you" section on dashboard.
    """
    jobs_collection = db.jobs_cache
    
    # Find most-viewed jobs from last 48 hours
    trending = await jobs_collection.find(
        {
            "location": location,
            "created_at": {"$gte": datetime.utcnow() - timedelta(days=2)}
        }
    ).sort([("view_count", -1), ("date_posted", -1)]).limit(limit).to_list(limit)
    
    return {
        "trending_jobs": [clean(j) for j in trending],
        "location": location,
        "count": len(trending),
    }


@router.post("/view")
async def log_job_view(
    user: dict = Depends(get_current_user),
    job_id: str = Query(..., description="Job MongoDB _id"),
):
    """
    Log when user views a job (for trending calculation).
    
    This helps us show popular jobs and improve recommendations.
    """
    from bson import ObjectId
    
    try:
        result = await db.jobs_cache.update_one(
            {"_id": ObjectId(job_id)},
            {"$inc": {"view_count": 1}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"status": "viewed", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/apply-tip/{job_id}")
async def get_apply_tip(
    user: dict = Depends(get_current_user),
    job_id: str = None,
):
    """
    Get AI-powered application tip for a specific job.
    
    Uses Claude to generate custom cover letter snippet or tip
    based on job requirements and user profile.
    """
    # TODO: Integrate with Maple AI to generate personalized tips
    return {
        "tip": "Highlight your Canadian experience and language skills in your cover letter.",
        "job_id": job_id,
    }
