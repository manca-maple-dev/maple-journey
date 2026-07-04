"""Live community data fetch + cache using OpenStreetMap (Nominatim + Overpass)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_city(city: str) -> str:
    return (city or "").strip().lower()


CATEGORY_QUERIES: Dict[str, Dict[str, str]] = {
    "worship": {
        "title": "Places of worship",
        "query": 'node["amenity"="place_of_worship"](around:{radius},{lat},{lon});way["amenity"="place_of_worship"](around:{radius},{lat},{lon});relation["amenity"="place_of_worship"](around:{radius},{lat},{lon});',
    },
    "grocery": {
        "title": "Ethnic groceries",
        "query": 'node["shop"="supermarket"](around:{radius},{lat},{lon});node["shop"="convenience"](around:{radius},{lat},{lon});way["shop"="supermarket"](around:{radius},{lat},{lon});',
    },
    "foodbank": {
        "title": "Food banks & meals",
        "query": 'node["social_facility"="food_bank"](around:{radius},{lat},{lon});node["amenity"="social_facility"]["social_facility:for"~"homeless|poor|food"](around:{radius},{lat},{lon});',
    },
    "shelter": {
        "title": "Shelters & housing help",
        "query": 'node["social_facility"="shelter"](around:{radius},{lat},{lon});way["social_facility"="shelter"](around:{radius},{lat},{lon});',
    },
    "settlement": {
        "title": "Settlement agencies",
        "query": 'node["office"="ngo"](around:{radius},{lat},{lon});node["amenity"="community_centre"](around:{radius},{lat},{lon});way["office"="ngo"](around:{radius},{lat},{lon});',
    },
    "health": {
        "title": "Community health centres",
        "query": 'node["amenity"="clinic"](around:{radius},{lat},{lon});node["amenity"="doctors"](around:{radius},{lat},{lon});way["amenity"="clinic"](around:{radius},{lat},{lon});',
    },
}


async def _geocode_city(city: str, timeout: float = 8.0) -> Optional[Tuple[float, float, str]]:
    if not city:
        return None
    params = {
        "q": f"{city}, Canada",
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": "MapleJourney/1.0 (community-refresh)"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)
        resp.raise_for_status()
        payload = resp.json() or []
    if not payload:
        return None
    top = payload[0]
    return float(top["lat"]), float(top["lon"]), str(top.get("display_name", city))


async def _fetch_category(city: str, lat: float, lon: float, key: str, radius: int = 12000, timeout: float = 15.0, limit: int = 10) -> List[Dict[str, Any]]:
    cat = CATEGORY_QUERIES[key]
    overpass_q = (
        "[out:json][timeout:25];("
        + cat["query"].format(radius=radius, lat=lat, lon=lon)
        + ");out center "
        + str(limit)
        + ";"
    )
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post("https://overpass-api.de/api/interpreter", data=overpass_q)
        resp.raise_for_status()
        payload = resp.json() or {}
    items: List[Dict[str, Any]] = []
    for element in payload.get("elements", [])[:limit]:
        tags = element.get("tags") or {}
        e_lat = element.get("lat") or (element.get("center") or {}).get("lat")
        e_lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if e_lat is None or e_lon is None:
            continue
        name = tags.get("name") or f"{cat['title']} location"
        osm_url = f"https://www.openstreetmap.org/?mlat={e_lat}&mlon={e_lon}#map=16/{e_lat}/{e_lon}"
        items.append(
            {
                "id": str(uuid4()),
                "city": city,
                "category": key,
                "category_title": cat["title"],
                "name": name,
                "address": tags.get("addr:full") or tags.get("addr:street") or "",
                "lat": float(e_lat),
                "lon": float(e_lon),
                "url": osm_url,
                "source": "OpenStreetMap",
                "source_url": "https://www.openstreetmap.org/",
                "fetched_at": _now_iso(),
            }
        )
    return items


async def fetch_live_community_resources(city: str, categories: Optional[List[str]] = None) -> Dict[str, Any]:
    normalized_city = city.strip()
    geo = await _geocode_city(normalized_city)
    if not geo:
        return {"city": normalized_city, "items": [], "fetched_at": _now_iso(), "error": "city-not-found"}
    lat, lon, display_name = geo
    category_keys = [c for c in (categories or list(CATEGORY_QUERIES.keys())) if c in CATEGORY_QUERIES]
    all_items: List[Dict[str, Any]] = []
    for key in category_keys:
        try:
            all_items.extend(await _fetch_category(normalized_city, lat, lon, key))
        except Exception:
            # Continue with partial results if one category fails.
            continue
    return {
        "city": normalized_city,
        "display_name": display_name,
        "lat": lat,
        "lon": lon,
        "items": all_items,
        "fetched_at": _now_iso(),
    }


async def cache_community_resources(db, city: str, payload: Dict[str, Any]) -> None:
    await db.community_resources_cache.update_one(
        {"city_key": _norm_city(city)},
        {
            "$set": {
                "city_key": _norm_city(city),
                "city": payload.get("city", city),
                "display_name": payload.get("display_name", city),
                "lat": payload.get("lat"),
                "lon": payload.get("lon"),
                "items": payload.get("items", []),
                "fetched_at": payload.get("fetched_at") or _now_iso(),
                "updated_at": _now_iso(),
            },
            "$setOnInsert": {"created_at": _now_iso()},
        },
        upsert=True,
    )


async def get_cached_community_resources(db, city: str, max_age_minutes: int) -> Optional[Dict[str, Any]]:
    row = await db.community_resources_cache.find_one({"city_key": _norm_city(city)})
    if not row:
        return None
    if max_age_minutes <= 0:
        return None
    fetched_at = row.get("fetched_at")
    if not fetched_at:
        return None
    try:
        fetched_dt = datetime.fromisoformat(str(fetched_at))
    except Exception:
        return None
    if datetime.now(timezone.utc) - fetched_dt > timedelta(minutes=max_age_minutes):
        return None
    return row


async def refresh_top_community_cities(db, cities: List[str]) -> int:
    refreshed = 0
    for city in cities:
        try:
            payload = await fetch_live_community_resources(city)
            await cache_community_resources(db, city, payload)
            refreshed += 1
        except Exception:
            continue
    return refreshed
