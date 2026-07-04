"""Source registry and freshness tracking for legal/government resources."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

import httpx


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SOURCE_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "ircc-main",
        "name": "IRCC",
        "kind": "government",
        "province": "National",
        "url": "https://www.canada.ca/en/immigration-refugees-citizenship.html",
        "expose_in_legal_resources": True,
        "resource_type": "Immigration",
        "cost": "Free",
        "description": "Official immigration, permits, PR, citizenship and policy guidance.",
        "contact": "1-888-242-2100",
    },
    {
        "id": "justice-irpa",
        "name": "Justice Laws (IRPA)",
        "kind": "government",
        "province": "National",
        "url": "https://laws-lois.justice.gc.ca/eng/acts/i-2.5/",
        "expose_in_legal_resources": True,
        "resource_type": "General",
        "cost": "Free",
        "description": "Authoritative Immigration and Refugee Protection Act text.",
        "contact": "",
    },
    {
        "id": "irb-main",
        "name": "Immigration and Refugee Board",
        "kind": "government",
        "province": "National",
        "url": "https://irb.gc.ca/en/",
        "expose_in_legal_resources": True,
        "resource_type": "Refugee",
        "cost": "Free",
        "description": "Refugee and immigration tribunal process and hearing guidance.",
        "contact": "",
    },
    {
        "id": "lao",
        "name": "Legal Aid Ontario",
        "kind": "legal-aid",
        "province": "Ontario",
        "url": "https://www.legalaid.on.ca/services/immigration-and-refugee-law/",
        "expose_in_legal_resources": True,
        "resource_type": "Refugee",
        "cost": "Free",
        "description": "Immigration and refugee legal help for eligible low-income clients.",
        "contact": "1-800-668-8258",
    },
    {
        "id": "labc",
        "name": "Legal Aid BC",
        "kind": "legal-aid",
        "province": "British Columbia",
        "url": "https://legalaid.bc.ca/",
        "expose_in_legal_resources": True,
        "resource_type": "Refugee",
        "cost": "Free",
        "description": "Refugee and immigration legal representation in BC.",
        "contact": "1-866-577-2525",
    },
    {
        "id": "laa",
        "name": "Legal Aid Alberta",
        "kind": "legal-aid",
        "province": "Alberta",
        "url": "https://www.legalaid.ab.ca/",
        "expose_in_legal_resources": True,
        "resource_type": "Immigration",
        "cost": "Free",
        "description": "Legal aid support for immigration and refugee matters in Alberta.",
        "contact": "1-866-845-3425",
    },
    {
        "id": "csj-qc",
        "name": "Commission des services juridiques",
        "kind": "legal-aid",
        "province": "Quebec",
        "url": "https://www.csj.qc.ca/",
        "expose_in_legal_resources": True,
        "resource_type": "Refugee",
        "cost": "Free",
        "description": "Quebec legal aid for immigration and refugee support.",
        "contact": "",
    },
    {
        "id": "probono-on",
        "name": "Pro Bono Ontario",
        "kind": "legal-aid",
        "province": "Ontario",
        "url": "https://www.probonoontario.org/",
        "expose_in_legal_resources": True,
        "resource_type": "General",
        "cost": "Free",
        "description": "Free brief legal advice clinics and hotline support.",
        "contact": "1-855-255-7256",
    },
]


def _freshness_label(last_success_at: Optional[str]) -> str:
    if not last_success_at:
        return "Needs refresh"
    try:
        ts = datetime.fromisoformat(last_success_at)
    except Exception:
        return "Needs refresh"
    age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
    if age_hours <= 24:
        return "Updated in last 24h"
    if age_hours <= 24 * 7:
        return "Updated this week"
    return "Older than 7 days"


async def ensure_source_registry(db) -> None:
    for source in SOURCE_REGISTRY:
        base = {
            **source,
            "enabled": True,
            "last_checked_at": None,
            "last_success_at": None,
            "status_code": None,
            "reachable": None,
            "last_error": "",
            "updated_at": _utc_now_iso(),
        }
        await db.source_registry.update_one(
            {"id": source["id"]},
            {
                "$setOnInsert": {"created_at": _utc_now_iso()},
                "$set": base,
            },
            upsert=True,
        )


async def _probe_source(url: str, timeout: float = 8.0) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status_code": None,
        "reachable": False,
        "last_error": "",
        "last_checked_at": _utc_now_iso(),
        "last_success_at": None,
        "etag": None,
        "last_modified": None,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.head(url)
            if response.status_code >= 400:
                response = await client.get(url)
            result["status_code"] = int(response.status_code)
            result["reachable"] = response.status_code < 400
            if result["reachable"]:
                result["last_success_at"] = _utc_now_iso()
            result["etag"] = response.headers.get("etag")
            result["last_modified"] = response.headers.get("last-modified")
    except Exception as exc:
        result["last_error"] = str(exc)[:300]
    return result


async def refresh_source_registry_health(db, kinds: Optional[Iterable[str]] = None) -> int:
    query: Dict[str, Any] = {"enabled": True}
    if kinds:
        query["kind"] = {"$in": list(kinds)}
    sources = await db.source_registry.find(query).to_list(500)
    updated = 0
    for source in sources:
        health = await _probe_source(source.get("url", ""))
        await db.source_registry.update_one(
            {"id": source["id"]},
            {
                "$set": {
                    "status_code": health["status_code"],
                    "reachable": health["reachable"],
                    "last_error": health["last_error"],
                    "etag": health["etag"],
                    "last_modified": health["last_modified"],
                    "last_checked_at": health["last_checked_at"],
                    "updated_at": _utc_now_iso(),
                    **({"last_success_at": health["last_success_at"]} if health["last_success_at"] else {}),
                }
            },
        )
        updated += 1
    return updated


def _domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


async def materialize_legal_resources_from_registry(db) -> int:
    sources = await db.source_registry.find({"enabled": True, "expose_in_legal_resources": True}).to_list(500)
    count = 0
    for source in sources:
        doc = {
            "id": source["id"],
            "source_id": source["id"],
            "name": source.get("name", ""),
            "type": source.get("resource_type", "General"),
            "province": source.get("province", "National"),
            "cost": source.get("cost", "Free"),
            "description": source.get("description", ""),
            "contact": source.get("contact", ""),
            "url": source.get("url", ""),
            "source_kind": source.get("kind", "legal-aid"),
            "source_domain": _domain(source.get("url", "")),
            "source_last_checked_at": source.get("last_checked_at"),
            "source_last_success_at": source.get("last_success_at"),
            "source_status_code": source.get("status_code"),
            "source_reachable": bool(source.get("reachable")),
            "freshness_label": _freshness_label(source.get("last_success_at")),
            "updated_at": _utc_now_iso(),
        }
        await db.legal_resources.update_one({"id": source["id"]}, {"$set": doc, "$setOnInsert": {"created_at": _utc_now_iso()}}, upsert=True)
        count += 1
    return count


async def refresh_legal_sources_and_resources(db) -> Dict[str, int]:
    await ensure_source_registry(db)
    health_updated = await refresh_source_registry_health(db, kinds=["government", "legal-aid"])
    legal_count = await materialize_legal_resources_from_registry(db)
    return {"sources_checked": health_updated, "legal_resources_upserted": legal_count}


async def source_registry_snapshot(db) -> List[Dict[str, Any]]:
    rows = await db.source_registry.find({}).sort("kind", 1).to_list(500)
    return rows
