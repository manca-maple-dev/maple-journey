"""Overview / Today — a localized, grounded morning briefing.
Every item is specific to the user's city and immigration status and carries a
source. Nothing is generated without retrieval. External calls are best-effort
with graceful fallbacks so the page always renders fast."""
import asyncio
import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, date, timedelta

import httpx
from fastapi import APIRouter, Depends

from core.db import db, clean
from core.security import get_current_user

logger = logging.getLogger("maplejourney.overview")
router = APIRouter(tags=["overview"])

IRCC_FEED = "https://api.io.canada.ca/io-server/gc/news/en/v2?dept=departmentofcitizenshipandimmigration&sort=publishedDate&orderBy=desc&format=atom"
ATOM = {"a": "http://www.w3.org/2005/Atom"}

CAT_KEYWORDS = {
    "express_entry": ["express entry", "crs", "invitation", "draw", "skilled worker", "canadian experience"],
    "provincial_nominee": ["provincial nominee", "pnp", "nomination"],
    "student": ["study permit", "student", "pgwp", "designated learning", "graduate"],
    "temp_foreign_worker": ["work permit", "lmia", "temporary foreign worker", "employer"],
    "visitor_work_permit": ["work permit", "visitor", "permit"],
    "spousal_family": ["family", "spousal", "sponsor", "parents and grandparents", "super visa"],
    "refugee_claimant": ["refugee", "asylum", "protected person", "claim"],
    "protected_person": ["refugee", "protected person", "asylum"],
}
PROVINCE_NAMES = {
    "ON": "ontario", "BC": "british columbia", "QC": "quebec", "AB": "alberta", "MB": "manitoba",
    "SK": "saskatchewan", "NS": "nova scotia", "NB": "new brunswick", "NL": "newfoundland",
    "PE": "prince edward island", "NT": "northwest territories", "YT": "yukon", "NU": "nunavut",
}
WMO = {
    0: ("Clear sky", "sun"), 1: ("Mainly clear", "sun"), 2: ("Partly cloudy", "cloud-sun"), 3: ("Overcast", "cloud"),
    45: ("Fog", "cloud-fog"), 48: ("Rime fog", "cloud-fog"), 51: ("Light drizzle", "cloud-drizzle"),
    53: ("Drizzle", "cloud-drizzle"), 55: ("Heavy drizzle", "cloud-drizzle"), 61: ("Light rain", "cloud-rain"),
    63: ("Rain", "cloud-rain"), 65: ("Heavy rain", "cloud-rain"), 66: ("Freezing rain", "cloud-rain"),
    67: ("Freezing rain", "cloud-rain"), 71: ("Light snow", "snowflake"), 73: ("Snow", "snowflake"),
    75: ("Heavy snow", "snowflake"), 77: ("Snow grains", "snowflake"), 80: ("Rain showers", "cloud-rain"),
    81: ("Rain showers", "cloud-rain"), 82: ("Heavy showers", "cloud-rain"), 85: ("Snow showers", "snowflake"),
    86: ("Snow showers", "snowflake"), 95: ("Thunderstorm", "cloud-lightning"), 96: ("Thunderstorm", "cloud-lightning"),
    99: ("Thunderstorm", "cloud-lightning"),
}

_geo_cache: dict[str, tuple] = {}
_news_cache: dict = {"at": 0, "items": []}


def _greeting_time():
    h = datetime.now(timezone.utc).astimezone().hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"


async def _geocode(client, city):
    key = city.lower().strip()
    if key in _geo_cache:
        return _geo_cache[key]
    r = await client.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1, "country": "CA"})
    res = (r.json() or {}).get("results") or []
    if not res:
        return None
    coord = (res[0]["latitude"], res[0]["longitude"])
    _geo_cache[key] = coord
    return coord


async def _weather(client, city):
    if not city:
        return None
    try:
        coord = await _geocode(client, city)
        if not coord:
            return None
        lat, lon = coord
        r = await client.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,precipitation,wind_speed_10m,weather_code", "timezone": "auto",
        })
        cur = (r.json() or {}).get("current") or {}
        cond, icon = WMO.get(int(cur.get("weather_code", -1)), ("—", "cloud"))
        return {
            "city": city,
            "temperature": round(cur.get("temperature_2m")) if cur.get("temperature_2m") is not None else None,
            "precipitation": cur.get("precipitation"),
            "wind": round(cur.get("wind_speed_10m")) if cur.get("wind_speed_10m") is not None else None,
            "condition": cond, "icon": icon,
            "source": "Environment data via Open-Meteo",
        }
    except Exception:
        logger.warning("weather fetch failed for %s", city)
        return None


async def _news(client, category, province):
    now = time.time()
    if now - _news_cache["at"] < 300 and _news_cache["items"]:
        entries = _news_cache["items"]
    else:
        try:
            r = await client.get(IRCC_FEED)
            root = ET.fromstring(r.content)
            entries = []
            for e in root.findall("a:entry", ATOM)[:25]:
                t = e.find("a:title", ATOM)
                l = e.find("a:link", ATOM)
                s = e.find("a:summary", ATOM)
                u = e.find("a:updated", ATOM) or e.find("a:published", ATOM)
                summary = (s.text or "").strip() if s is not None else ""
                entries.append({
                    "title": (t.text or "").strip() if t is not None else "",
                    "link": l.get("href") if l is not None else "",
                    "summary": (summary[:220] + "…") if len(summary) > 220 else summary,
                    "updated": u.text if u is not None else None,
                })
            _news_cache.update(at=now, items=entries)
        except Exception:
            logger.warning("IRCC news fetch failed")
            return []
    kws = CAT_KEYWORDS.get(category, [])
    prov = PROVINCE_NAMES.get((province or "").upper(), "")
    ranked = []
    for i, e in enumerate(entries):
        blob = f"{e['title']} {e['summary']}".lower()
        score = sum(3 for k in kws if k in e["title"].lower()) + sum(1 for k in kws if k in e["summary"].lower())
        if prov and prov in blob:
            score += 2
        ranked.append((score, -i, e))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top = [e for _, _, e in ranked[:5]]
    for e in top:
        e["source"] = "IRCC — Immigration, Refugees and Citizenship Canada"
    return top


def _easter(year):
    a = year % 19; b = year // 100; c = year % 100; d = b // 4; e = b % 4
    f = (b + 8) // 25; g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30
    i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + timedelta(days=offset + 7 * (n - 1))


def _stat_holidays(year):
    easter = _easter(year)
    return [
        (date(year, 1, 1), "New Year's Day", "statutory"),
        (_nth_weekday(year, 2, 0, 3), "Family Day", "statutory"),
        (easter - timedelta(days=2), "Good Friday", "statutory"),
        (_nth_weekday(year, 5, 0, 4) if _nth_weekday(year, 5, 0, 4).day <= 24 else _nth_weekday(year, 5, 0, 3), "Victoria Day", "statutory"),
        (date(year, 7, 1), "Canada Day", "statutory"),
        (_nth_weekday(year, 9, 0, 1), "Labour Day", "statutory"),
        (date(year, 9, 30), "Truth & Reconciliation Day", "statutory"),
        (_nth_weekday(year, 10, 0, 2), "Thanksgiving", "statutory"),
        (date(year, 11, 11), "Remembrance Day", "statutory"),
        (date(year, 12, 25), "Christmas Day", "statutory"),
        (date(year, 12, 26), "Boxing Day", "statutory"),
    ]


RELIGIOUS = {
    "Islam": [(date(2026, 3, 20), "Eid al-Fitr"), (date(2026, 5, 27), "Eid al-Adha")],
    "Hinduism": [(date(2026, 11, 8), "Diwali")],
    "Sikhism": [(date(2026, 4, 14), "Vaisakhi"), (date(2026, 11, 8), "Bandi Chhor / Diwali")],
    "Judaism": [(date(2026, 9, 12), "Rosh Hashanah"), (date(2026, 9, 21), "Yom Kippur")],
}


def _holidays(religion):
    today = date.today()
    pool = _stat_holidays(today.year) + _stat_holidays(today.year + 1)
    for d, name in RELIGIOUS.get(religion or "", []):
        pool.append((d, name, "religious"))
    upcoming = sorted([(d, n, k) for d, n, k in pool if d >= today], key=lambda x: x[0])[:4]
    # Use cross-platform formatting (Windows does not support %-d in strftime).
    return [{"date": d.isoformat(), "name": n, "kind": k, "days": (d - today).days,
             "label": f"{d:%b} {d.day}"} for d, n, k in upcoming]


@router.get("/overview")
async def overview(user: dict = Depends(get_current_user)):
    profile = user.get("profile") or {}
    name = (profile.get("preferred_name") or (user.get("name") or "there").split(" ")[0])
    city = profile.get("current_city") or ""
    category = profile.get("immigration_category")
    province = profile.get("province_of_residence") or profile.get("intended_province")
    completed = bool(user.get("profile_completed"))

    async with httpx.AsyncClient(timeout=6.0, headers={"User-Agent": "MapleJourney/1.0"}) as client:
        weather, news = await asyncio.gather(
            _weather(client, city or "Toronto"),
            _news(client, category, province),
        )

    days_since_arrival = None
    arr = profile.get("arrival_date_canada")
    if arr:
        try:
            d = (date.today() - date.fromisoformat(arr[:10])).days
            if 0 <= d < 365:
                days_since_arrival = d
        except Exception:
            pass

    ads = []
    try:
        ads = [clean(a) for a in await db.ads.find({"active": True}).to_list(2)]
    except Exception:
        ads = []

    greeting_city = city or (weather or {}).get("city") or "Canada"
    return {
        "greeting": f"{_greeting_time()}, {name}. Here's today's briefing for {greeting_city}.",
        "preferred_name": name,
        "city": city,
        "profile_completed": completed,
        "weather": weather,
        "news": news,
        "holidays": _holidays(profile.get("religion")),
        "days_since_arrival": days_since_arrival,
        "ads": ads,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
