"""Adzuna Job API integration for live Canadian job listings.

Adzuna provides real-time job search across multiple Canadian job boards.
API docs: https://developer.adzuna.com/
"""

import os
import logging
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger("maplejourney.adzuna")

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/ca/search"
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")


async def search_adzuna_jobs(
    location: str = "Toronto",
    keywords: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Search live jobs from Adzuna API.
    
    Args:
        location: Canadian city (Toronto, Vancouver, Montreal, etc.)
        keywords: Job title or keywords to search
        limit: Max results to return
    
    Returns:
        List of job dictionaries with standardized fields
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.warning("Adzuna credentials not configured")
        return []

    try:
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "location": location,
            "results_per_page": min(limit, 50),
            "sort_by": "date",
            "sort_direction": "descending",
        }

        if keywords:
            params["what"] = keywords

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(ADZUNA_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            jobs = []
            for job in data.get("results", []):
                try:
                    standardized = {
                        "_id": job.get("id"),
                        "title": job.get("title", ""),
                        "company": job.get("company", {}).get("display_name", ""),
                        "location": job.get("location", {}).get("display_name", location),
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                        "job_type": job.get("employment_type", "").title() if job.get("employment_type") else "",
                        "external_url": job.get("redirect_url", ""),
                        "description": job.get("description", ""),
                        "posted_at": job.get("created", ""),
                        "source": "adzuna",
                        "relevance_score": 70,
                    }
                    jobs.append(standardized)
                except Exception as e:
                    logger.warning(f"Error processing job: {e}")
                    continue

            logger.info(f"Adzuna: fetched {len(jobs)} jobs for {location}")
            return jobs[:limit]

    except Exception as e:
        logger.error(f"Adzuna API error: {e}")
        return []
