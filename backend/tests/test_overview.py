"""Tests for GET /api/overview — the morning briefing endpoint."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://bug-squash-preview-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

NEWCOMER_EMAIL = "newcomer_demo@test.com"
NEWCOMER_PASS = "Test1234!"
ADMIN_EMAIL = "admin@maplejourney.ca"
ADMIN_PASS = "MapleAdmin!2026"


@pytest.fixture(scope="module")
def newcomer_token():
    r = requests.post(f"{API}/auth/login", json={"email": NEWCOMER_EMAIL, "password": NEWCOMER_PASS}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _ensure_newcomer_profile(newcomer_token):
    """Ensure newcomer_demo has a completed profile with city=Toronto + arrival 2026-04-01."""
    profile = {
        "preferred_name": "Aanya",
        "current_city": "Toronto",
        "province_of_residence": "ON",
        "immigration_category": "express_entry",
        "arrival_date_canada": "2026-04-01",
        "religion": "Hinduism",
    }
    r = requests.put(f"{API}/profile", json=profile, headers={"Authorization": f"Bearer {newcomer_token}"}, timeout=15)
    assert r.status_code in (200, 201), r.text


def test_overview_requires_auth():
    r = requests.get(f"{API}/overview", timeout=15)
    assert r.status_code in (401, 403)


def test_overview_schema_and_content(newcomer_token):
    _ensure_newcomer_profile(newcomer_token)
    r = requests.get(f"{API}/overview", headers={"Authorization": f"Bearer {newcomer_token}"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    # Top-level keys
    for k in ["greeting", "preferred_name", "city", "profile_completed", "weather", "news", "holidays", "days_since_arrival", "ads", "generated_at"]:
        assert k in d, f"missing key {k}"
    assert d["profile_completed"] is True
    assert d["city"] == "Toronto"
    assert d["preferred_name"] == "Aanya"
    # Greeting format
    assert d["greeting"].startswith(("Good morning", "Good afternoon", "Good evening"))
    assert "Aanya" in d["greeting"]
    assert "Toronto" in d["greeting"]

    # Weather (best-effort; can be None on failure — but under normal ops should populate)
    if d["weather"] is not None:
        w = d["weather"]
        for k in ["temperature", "condition", "wind", "city", "source"]:
            assert k in w, f"weather missing {k}"
        assert w["city"] == "Toronto"

    # News list (best-effort; each cited to canada.ca)
    assert isinstance(d["news"], list)
    assert len(d["news"]) <= 5
    for item in d["news"]:
        assert "title" in item and "link" in item and "summary" in item and "source" in item
        assert item["source"].startswith("IRCC")
        # link should be a canada.ca URL when present
        if item["link"]:
            assert "canada.ca" in item["link"], f"news link not canada.ca: {item['link']}"

    # Holidays
    assert isinstance(d["holidays"], list)
    for h in d["holidays"]:
        for k in ["name", "label", "days", "kind"]:
            assert k in h, f"holiday missing {k}"
        assert h["kind"] in ("statutory", "religious")
        assert isinstance(h["days"], int) and h["days"] >= 0

    # days_since_arrival — arrival 2026-04-01, today is Jan 2026 → future date → should be None
    # (endpoint only sets 0..365 window)
    assert d["days_since_arrival"] is None or (0 <= d["days_since_arrival"] < 365)


def test_overview_admin_defaults_to_toronto(admin_token):
    """Admin has no city — weather should default to Toronto (per endpoint code)."""
    r = requests.get(f"{API}/overview", headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    # Admin has no profile.current_city; greeting_city falls back to weather city or 'Canada'
    if d["weather"] is not None:
        assert d["weather"]["city"] == "Toronto"
