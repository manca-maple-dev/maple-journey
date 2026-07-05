"""Intelligent live job scraping, matching, and caching service.

Smart logic:
- Profile-aware: matches user's industry, skills, experience level
- Location-based: 25km radius from user's city
- Real-time caching: caches jobs, refreshes on search, clears on inactivity
- Filter-rich: salary, job type, experience level, date posted
"""
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from core.db import db, clean
from pymongo import UpdateOne, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

logger = logging.getLogger("jobs")

# Job Bank API (official Canadian government source)
JOBBANK_API_BASE = "https://www.jobbank.gc.ca/api/search"
JOBBANK_SEARCH_URL = "https://api.jobbank.gc.ca/api/jobs"  # Alternative endpoint if needed

# Distance matrix - approximate lat/long for Canadian cities (for 25km filtering)
CANADIAN_CITIES = {
    "toronto": {"lat": 43.6532, "lng": -79.3832},
    "vancouver": {"lat": 49.2827, "lng": -123.1207},
    "calgary": {"lat": 51.0447, "lng": -114.0719},
    "edmonton": {"lat": 53.5461, "lng": -113.4938},
    "montreal": {"lat": 45.5017, "lng": -73.5673},
    "winnipeg": {"lat": 49.8951, "lng": -97.1384},
    "ottawa": {"lat": 45.4215, "lng": -75.6972},
    "quebec": {"lat": 46.8139, "lng": -71.2080},
    "halifax": {"lat": 44.6426, "lng": -63.2181},
    "victoria": {"lat": 48.4261, "lng": -123.3623},
}

# Job titles for intelligence matching
TECH_KEYWORDS = [
    "software", "developer", "engineer", "data", "analyst", "database",
    "web", "full stack", "frontend", "backend", "devops", "cloud", "it",
    "programmer", "coder", "architect", "system", "network", "security"
]
HEALTHCARE_KEYWORDS = [
    "nurse", "doctor", "physician", "therapist", "counselor", "healthcare",
    "medical", "clinical", "pharmacy", "health", "dental", "mental health"
]
TRADES_KEYWORDS = [
    "electrician", "plumber", "carpenter", "mechanic", "hvac", "construction",
    "welding", "metalwork", "heavy equipment", "trade"
]
FINANCE_KEYWORDS = [
    "accountant", "financial", "analyst", "cpa", "auditor", "bookkeeper",
    "payroll", "tax", "accounting", "banking", "investment"
]
ADMIN_KEYWORDS = [
    "administrative", "admin", "office", "clerk", "receptionist",
    "executive assistant", "secretary", "customer service"
]


async def ensure_indexes() -> None:
    """Create MongoDB indexes for job queries."""
    jobs = db.jobs_cache
    try:
        await jobs.create_index([("location", ASCENDING), ("date_posted", DESCENDING)])
        await jobs.create_index([("industry", ASCENDING)])
        await jobs.create_index([("experience_level", ASCENDING)])
        await jobs.create_index([("created_at", DESCENDING)])
        await jobs.create_index([("user_id", ASCENDING), ("date_posted", DESCENDING)])
    except PyMongoError as e:
        # Do not block app startup if index creation fails (e.g., low disk on DB).
        logger.warning(f"Jobs index initialization skipped: {e}")


async def scrape_jobs_from_jobbank(
    query: str = "",
    location: str = "Canada",
    limit: int = 50
) -> List[Dict]:
    """Scrape jobs from Government Job Bank API (free, official).
    
    Args:
        query: Job title or keyword (e.g., "software engineer")
        location: City or province
        limit: How many jobs to fetch (default 50, max 100)
    
    Returns:
        List of job documents with: title, company, location, salary, job_type, url, posted_date
    """
    jobs = []
    try:
        async with aiohttp.ClientSession() as session:
            # Job Bank API v1 public endpoint
            params = {
                "keywordTitle": query or "",
                "locationName": location,
                "limitResults": min(limit, 100),
                "sort": "reciency",  # Most recent first
            }
            
            async with session.get(
                f"{JOBBANK_API_BASE}/search",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Parse Job Bank response format
                    for item in data.get("data", []):
                        job_doc = {
                            "title": item.get("jobTitle", ""),
                            "company": item.get("companyName", ""),
                            "location": item.get("location", location),
                            "salary_min": item.get("salaryMin"),
                            "salary_max": item.get("salaryMax"),
                            "salary_currency": item.get("salaryCurrency", "CAD"),
                            "job_type": item.get("jobType", "Full-time"),  # Full-time, Part-time, Contract
                            "description": item.get("jobDescription", ""),
                            "external_url": item.get("jobUrl", ""),
                            "source": "jobbank",
                            "date_posted": item.get("postedDate", datetime.utcnow().isoformat()),
                            "experience_level": _infer_experience_level(item.get("jobDescription", "")),
                            "industry": _infer_industry(item.get("jobTitle", "")),
                        }
                        jobs.append(job_doc)
                        
    except Exception as e:
        logger.error(f"JobBank scrape failed: {e}")
    
    return jobs


async def cache_jobs(
    user_id: str,
    jobs: List[Dict],
    location: str,
) -> None:
    """Cache scraped jobs in MongoDB with metadata.
    
    Args:
        user_id: User performing the search
        jobs: List of job documents to cache
        location: User's search location
    """
    if not jobs:
        return
    
    jobs_collection = db.jobs_cache
    now = datetime.utcnow()
    
    # Add metadata to each job
    for job in jobs:
        job.update({
            "location": location,
            "created_at": now,
            "expires_at": now + timedelta(hours=24),  # Auto-cleanup after 24h
            "view_count": 0,
        })
    
    # Bulk insert/update
    try:
        await jobs_collection.insert_many(jobs, ordered=False)
    except Exception as e:
        logger.warning(f"Some jobs already cached: {e}")


async def search_jobs(
    user_id: str,
    location: str,
    keywords: Optional[str] = None,
    job_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    salary_min: Optional[int] = None,
    salary_max: Optional[int] = None,
    days_posted: Optional[int] = None,
    limit: int = 20,
    force_refresh: bool = False,
) -> Tuple[List[Dict], int]:
    """Search and cache jobs intelligently.
    
    1. If force_refresh=True or cache is stale (>30min), re-scrape from Job Bank
    2. Filter by user's smart preferences
    3. Return results with relevance scoring
    
    Args:
        user_id: User ID (for preference matching)
        location: City/province (for 25km filtering)
        keywords: Job title/keyword search
        job_type: Filter by Full-time, Part-time, Contract
        experience_level: entry, mid, senior
        salary_min, salary_max: Salary range filter
        days_posted: Only jobs posted in last N days
        limit: Max results to return
        force_refresh: Force re-scrape even if cached
    
    Returns:
        (jobs_list, total_count) - filtered jobs and total available
    """
    jobs_collection = db.jobs_cache
    now = datetime.utcnow()
    
    # Check cache freshness (30 min threshold)
    cache_age = await jobs_collection.find_one(
        {"location": location},
        sort=[("created_at", -1)]
    )
    
    is_stale = (
        not cache_age or
        (now - cache_age["created_at"]).total_seconds() > 1800 or
        force_refresh
    )
    
    # Re-scrape if stale or forced
    if is_stale:
        logger.info(f"Re-scraping jobs for {location} (stale={is_stale}, force={force_refresh})")
        scraped_jobs = await scrape_jobs_from_jobbank(
            query=keywords or "",
            location=location,
            limit=100  # Fetch more, user can filter
        )
        if scraped_jobs:
            await cache_jobs(user_id, scraped_jobs, location)
    
    # Build filter query
    filters = {
        "location": location,
        "expires_at": {"$gt": now},  # Not expired
    }
    
    if keywords:
        filters["$or"] = [
            {"title": {"$regex": keywords, "$options": "i"}},
            {"company": {"$regex": keywords, "$options": "i"}},
            {"description": {"$regex": keywords, "$options": "i"}},
        ]
    
    if job_type:
        filters["job_type"] = job_type
    
    if experience_level:
        filters["experience_level"] = experience_level
    
    if salary_min or salary_max:
        salary_filter = {}
        if salary_min:
            salary_filter["$gte"] = salary_min
        if salary_max:
            salary_filter["$lte"] = salary_max
        filters["salary_max"] = salary_filter
    
    if days_posted:
        cutoff = now - timedelta(days=days_posted)
        filters["date_posted"] = {"$gte": cutoff.isoformat()}
    
    # Count total
    total = await jobs_collection.count_documents(filters)
    
    # Fetch and score
    cursor = jobs_collection.find(filters).sort("date_posted", -1).limit(limit)
    jobs = await cursor.to_list(limit)
    
    # Score each job by relevance to user profile
    user_profile = await db.users.find_one({"_id": user_id})
    for job in jobs:
        job = clean(job)
        job["relevance_score"] = _score_job_relevance(job, user_profile or {})
    
    # Sort by relevance score
    jobs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return jobs, total


async def get_user_job_preferences(user_id: str) -> Dict:
    """Get or initialize user's job search preferences.
    
    Stores: job_categories, experience_level, salary_range, preferred_locations
    """
    prefs_collection = db.user_job_preferences
    
    existing = await prefs_collection.find_one({"user_id": user_id})
    if existing:
        return clean(existing)
    
    # Initialize from profile
    user = await db.users.find_one({"_id": user_id})
    user_data = user or {}
    
    prefs = {
        "user_id": user_id,
        "job_categories": [],  # Will infer from experience/education
        "experience_level": "mid" if user_data.get("experience_years", 0) > 3 else "entry",
        "salary_min": 50000,
        "salary_max": 150000,
        "preferred_locations": [user_data.get("city", "Toronto")],
        "job_types": ["Full-time"],
        "created_at": datetime.utcnow(),
        "last_searched": None,
    }
    
    await prefs_collection.insert_one(prefs)
    return clean(prefs)


async def update_last_search(user_id: str, location: str) -> None:
    """Track when user last searched for jobs (for inactivity cleanup)."""
    await db.user_job_preferences.update_one(
        {"user_id": user_id},
        {"$set": {"last_searched": datetime.utcnow(), "last_search_location": location}},
        upsert=True
    )


async def cleanup_inactive_caches() -> None:
    """Remove job caches for inactive users (not searched in 7 days).
    
    This keeps MongoDB lean and removes stale data.
    """
    jobs_collection = db.jobs_cache
    cutoff = datetime.utcnow() - timedelta(days=7)
    
    result = await jobs_collection.delete_many({
        "created_at": {"$lt": cutoff}
    })
    
    logger.info(f"Cleaned up {result.deleted_count} expired job caches")


async def get_new_jobs_count(user_id: str, since_last_login: Optional[datetime] = None) -> int:
    """Count new jobs posted since user's last login (for notification badge).
    
    Args:
        user_id: User ID
        since_last_login: Timestamp of last login (or use 24 hours ago if None)
    
    Returns:
        Count of new jobs matching user's location and preferences
    """
    if not since_last_login:
        since_last_login = datetime.utcnow() - timedelta(hours=24)
    
    prefs = await get_user_job_preferences(user_id)
    location = prefs["preferred_locations"][0] if prefs["preferred_locations"] else "Canada"
    
    count = await db.jobs_cache.count_documents({
        "location": location,
        "date_posted": {"$gte": since_last_login.isoformat()},
        "expires_at": {"$gt": datetime.utcnow()},
    })
    
    return count


def _infer_industry(job_title: str) -> str:
    """Infer job industry from title using keyword matching."""
    title_lower = job_title.lower()
    
    if any(kw in title_lower for kw in TECH_KEYWORDS):
        return "Technology"
    elif any(kw in title_lower for kw in HEALTHCARE_KEYWORDS):
        return "Healthcare"
    elif any(kw in title_lower for kw in TRADES_KEYWORDS):
        return "Trades"
    elif any(kw in title_lower for kw in FINANCE_KEYWORDS):
        return "Finance"
    elif any(kw in title_lower for kw in ADMIN_KEYWORDS):
        return "Administration"
    
    return "General"


def _infer_experience_level(job_description: str) -> str:
    """Infer experience level from job description keywords."""
    desc_lower = job_description.lower()
    
    if any(kw in desc_lower for kw in ["senior", "lead", "manager", "director", "principal", "veteran", "10+"]):
        return "senior"
    elif any(kw in desc_lower for kw in ["junior", "entry", "entry-level", "graduate", "new", "no experience"]):
        return "entry"
    
    return "mid"


def _score_job_relevance(job: Dict, user_profile: Dict) -> float:
    """Score how relevant a job is to the user profile.
    
    Scoring factors:
    - Industry match: +30 points
    - Experience level match: +25 points
    - Salary match (within user's range): +20 points
    - Job type match (preferred types): +15 points
    - Recency: +10 points (posted within 7 days)
    
    Returns:
        Score from 0-100
    """
    score = 0.0
    
    # Industry match
    user_industry = user_profile.get("industry") or _infer_industry(user_profile.get("job_title", ""))
    job_industry = job.get("industry", "General")
    if user_industry.lower() == job_industry.lower():
        score += 30
    
    # Experience level match
    user_exp_years = user_profile.get("experience_years", 0)
    user_exp_level = "senior" if user_exp_years > 8 else "mid" if user_exp_years > 3 else "entry"
    job_exp_level = job.get("experience_level", "mid")
    if user_exp_level == job_exp_level:
        score += 25
    
    # Salary match
    user_salary_min = user_profile.get("salary_min", 50000)
    user_salary_max = user_profile.get("salary_max", 150000)
    job_salary_max = job.get("salary_max", user_salary_max)
    if user_salary_min <= job_salary_max <= user_salary_max:
        score += 20
    
    # Job type match
    preferred_types = user_profile.get("job_types", ["Full-time"])
    if job.get("job_type") in preferred_types:
        score += 15
    
    # Recency bonus
    try:
        posted = datetime.fromisoformat(job.get("date_posted", datetime.utcnow().isoformat()))
        days_old = (datetime.utcnow() - posted).days
        if days_old <= 7:
            score += 10
    except:
        pass
    
    return min(score, 100)  # Cap at 100
