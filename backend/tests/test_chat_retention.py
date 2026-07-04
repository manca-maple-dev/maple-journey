"""Tests for Ask Maple tier-based chat retention & usage contract (Iteration 8).

Covers:
- GET /api/assistant/usage returns retention_days=3 for free tier + limit=8.
- GET /api/assistant/history filters out messages outside tier retention window.
- Free tier daily cap of 8 user messages triggers X-Maple-Limit header.
"""
import os
import uuid
from datetime import datetime, timezone, timedelta

import pytest
import requests


def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if url:
        return url.rstrip("/")
    with open("/app/frontend/.env") as fh:
        for line in fh:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    raise RuntimeError("no backend url")


BASE = _load_backend_url()
API = f"{BASE}/api"


def uh(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def fresh_user():
    email = f"TEST_retn_{uuid.uuid4().hex[:8]}@test.com"
    r = requests.post(
        f"{API}/auth/register",
        json={"name": "Retention Tester", "email": email, "password": "StrongPass1!"},
    )
    assert r.status_code == 200, r.text
    return {"email": email, "token": r.json()["token"], "user": r.json()["user"]}


# -------- Usage contract --------
class TestUsageRetentionContract:
    def test_usage_free_tier_shape(self, fresh_user):
        r = requests.get(f"{API}/assistant/usage", headers=uh(fresh_user["token"]))
        assert r.status_code == 200
        d = r.json()
        assert d["tier"] == "free"
        assert d["unlimited"] is False
        assert d["limit"] == 8
        assert d["retention_days"] == 3
        assert d["remaining"] == max(0, 8 - d["used"])


# -------- History retention filter (direct DB seed) --------
class TestHistoryRetentionFilter:
    """Seed messages older than 3 days directly in Mongo; free tier must hide them."""

    def test_free_tier_hides_old_messages(self, fresh_user):
        # Insert messages: one 5 days old (should be hidden), one now (should show).
        import asyncio
        import sys
        sys.path.insert(0, "/app/backend")
        from dotenv import load_dotenv
        load_dotenv("/app/backend/.env")
        from core.db import db  # type: ignore

        uid = str(fresh_user["user"]["id"])
        session_id = str(uuid.uuid4())
        old_ts = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        new_ts = datetime.now(timezone.utc).isoformat()

        async def seed():
            await db.chat_messages.insert_many([
                {"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id,
                 "role": "user", "content": "OLD_MSG_hidden", "created_at": old_ts},
                {"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id,
                 "role": "assistant", "content": "OLD_REPLY_hidden", "created_at": old_ts},
                {"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id,
                 "role": "user", "content": "NEW_MSG_visible", "created_at": new_ts},
            ])

        asyncio.run(seed())

        r = requests.get(
            f"{API}/assistant/history",
            headers=uh(fresh_user["token"]),
            params={"session_id": session_id},
        )
        assert r.status_code == 200, r.text
        items = r.json()
        contents = [i["content"] for i in items]
        assert "NEW_MSG_visible" in contents
        assert "OLD_MSG_hidden" not in contents, f"free-tier retention leak: {contents}"
        assert "OLD_REPLY_hidden" not in contents


# -------- Free tier daily cap enforcement --------
class TestFreeDailyCap:
    """Exhaust the 8-msg cap by seeding user messages in DB, then attempt to send."""

    def test_ninth_message_returns_limit_banner(self):
        import asyncio, sys
        sys.path.insert(0, "/app/backend")
        from dotenv import load_dotenv
        load_dotenv("/app/backend/.env")
        from core.db import db  # type: ignore

        email = f"TEST_cap_{uuid.uuid4().hex[:8]}@test.com"
        r = requests.post(
            f"{API}/auth/register",
            json={"name": "Cap", "email": email, "password": "StrongPass1!"},
        )
        assert r.status_code == 200
        token = r.json()["token"]
        uid = str(r.json()["user"]["id"])
        session_id = str(uuid.uuid4())
        today_iso = datetime.now(timezone.utc).replace(hour=12).isoformat()

        async def seed_cap():
            await db.chat_messages.insert_many([
                {"id": str(uuid.uuid4()), "user_id": uid, "session_id": session_id,
                 "role": "user", "content": f"TEST_seed_{i}", "created_at": today_iso}
                for i in range(8)
            ])
        asyncio.run(seed_cap())

        # Usage should reflect cap reached.
        u = requests.get(f"{API}/assistant/usage", headers=uh(token)).json()
        assert u["used"] >= 8
        assert u["remaining"] == 0

        # Next chat must return limit banner + special header.
        resp = requests.post(
            f"{API}/assistant/chat",
            headers=uh(token),
            json={"message": "should be blocked", "session_id": session_id},
            stream=True,
            timeout=30,
        )
        assert resp.status_code == 200
        assert resp.headers.get("X-Maple-Limit") == "reached", resp.headers
        body = "".join([c for c in resp.iter_content(chunk_size=None, decode_unicode=True) if c])
        assert "free limit" in body.lower() or "8 messages" in body.lower()
