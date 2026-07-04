"""Scheduled refresh pipeline for source registry, legal resources, and communities cache."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from services.community_sources import refresh_top_community_cities
from services.source_registry import refresh_legal_sources_and_resources, refresh_source_registry_health

logger = logging.getLogger("maplejourney.update_pipeline")

DEFAULT_COMMUNITY_CITIES = [
    "Toronto",
    "Vancouver",
    "Montreal",
    "Calgary",
    "Ottawa",
    "Winnipeg",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def run_update_cycle(db, community_cities: Optional[list[str]] = None) -> Dict[str, Any]:
    cities = community_cities or DEFAULT_COMMUNITY_CITIES
    cycle = {
        "started_at": _now_iso(),
        "ok": True,
        "errors": [],
        "legal": {},
        "community": {},
    }
    try:
        cycle["legal"] = await refresh_legal_sources_and_resources(db)
    except Exception as exc:
        cycle["ok"] = False
        cycle["errors"].append(f"legal-refresh: {exc}")

    try:
        # Keep government source heartbeat fresh even when legal resource materialization succeeds.
        gov_checked = await refresh_source_registry_health(db, kinds=["government"])
        refreshed = await refresh_top_community_cities(db, cities)
        cycle["community"] = {
            "cities_requested": len(cities),
            "cities_refreshed": refreshed,
            "government_sources_checked": gov_checked,
        }
    except Exception as exc:
        cycle["ok"] = False
        cycle["errors"].append(f"community-refresh: {exc}")

    cycle["finished_at"] = _now_iso()
    await db.update_runs.insert_one(cycle)
    return cycle


async def scheduler_loop(db, interval_minutes: int = 360, stop_event: Optional[asyncio.Event] = None) -> None:
    logger.info("update pipeline scheduler started (interval=%s minutes)", interval_minutes)
    while True:
        if stop_event and stop_event.is_set():
            logger.info("update pipeline scheduler stopping")
            return
        try:
            result = await run_update_cycle(db)
            logger.info("update cycle finished ok=%s errors=%s", result.get("ok"), len(result.get("errors", [])))
        except Exception:
            logger.exception("update cycle failed unexpectedly")
        await asyncio.sleep(max(60, interval_minutes * 60))
