"""Backend tests for Profile hub features: secure IDs (encrypted), export data,
billing history, and delete account. Also verifies /api/auth/profile route removal
is not needed since frontend uses /api/profile."""
import os
import uuid
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://bug-squash-preview-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def _signup():
    email = f"TEST_profile_{uuid.uuid4().hex[:8]}@test.com"
    r = requests.post(f"{API}/auth/register", json={"name": "Profile Tester", "email": email, "password": "Test1234!"})
    assert r.status_code == 200, r.text
    return r.json()["token"], email


def _auth(tok):
    return {"Authorization": f"Bearer {tok}"}


# --- Secure IDs (encryption round-trip) ---
class TestSecureIds:
    def test_secure_ids_default_empty(self):
        tok, _ = _signup()
        r = requests.get(f"{API}/auth/secure-ids", headers=_auth(tok))
        assert r.status_code == 200
        data = r.json()
        assert data == {"ircc_file_number": "", "ucis_or_foreign_id": ""}

    def test_secure_ids_put_then_get_plaintext(self):
        tok, _ = _signup()
        payload = {"ircc_file_number": "IRCC-12345", "ucis_or_foreign_id": "A9876543"}
        r = requests.put(f"{API}/auth/secure-ids", json=payload, headers=_auth(tok))
        assert r.status_code == 200
        assert r.json() == {"ok": True}

        r2 = requests.get(f"{API}/auth/secure-ids", headers=_auth(tok))
        assert r2.status_code == 200
        assert r2.json() == payload

    def test_secure_ids_stored_encrypted_in_me(self):
        """The plaintext must not leak via /auth/me (serialize_user)."""
        tok, _ = _signup()
        payload = {"ircc_file_number": "SENSITIVE-IRCC-XYZ", "ucis_or_foreign_id": "SENSITIVE-A123"}
        requests.put(f"{API}/auth/secure-ids", json=payload, headers=_auth(tok))
        me = requests.get(f"{API}/auth/me", headers=_auth(tok)).json()
        blob = str(me)
        assert "SENSITIVE-IRCC-XYZ" not in blob
        assert "SENSITIVE-A123" not in blob


# --- Profile PUT (whole-dict replace) ---
class TestProfilePut:
    def test_profile_put_sets_completed_and_persists(self):
        tok, _ = _signup()
        profile = {
            "preferred_name": "Alex",
            "immigration_category": "express_entry",
            "pr_received_date": "2024-01-15",
            "work_permit_expiry": "2026-06-30",
            "current_city": "Toronto",
            "consent_data_personalization": True,
        }
        r = requests.put(f"{API}/profile", json=profile, headers=_auth(tok))
        assert r.status_code == 200
        body = r.json()
        assert body["completed"] is True
        assert body["profile"]["preferred_name"] == "Alex"

        me = requests.get(f"{API}/auth/me", headers=_auth(tok)).json()
        assert me.get("profile_completed") is True
        assert me.get("profile", {}).get("current_city") == "Toronto"


# --- Billing history ---
class TestBilling:
    def test_billing_history_empty_new_user(self):
        tok, _ = _signup()
        r = requests.get(f"{API}/billing/history", headers=_auth(tok))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert r.json() == []

    def test_billing_history_requires_auth(self):
        r = requests.get(f"{API}/billing/history")
        assert r.status_code in (401, 403)


# --- Export data ---
class TestExport:
    def test_export_returns_account_and_questionnaire(self):
        tok, email = _signup()
        r = requests.get(f"{API}/auth/export", headers=_auth(tok))
        assert r.status_code == 200
        data = r.json()
        assert "account" in data
        assert "questionnaire" in data
        assert "exported_at" in data
        assert data["account"]["email"] == email.lower()


# --- Delete account (throwaway) ---
class TestDeleteAccount:
    def test_delete_account_removes_user(self):
        tok, email = _signup()
        # add a profile row so we test cascade too
        requests.put(f"{API}/profile", json={"preferred_name": "X"}, headers=_auth(tok))
        r = requests.delete(f"{API}/auth/account", headers=_auth(tok))
        assert r.status_code == 200
        assert r.json() == {"ok": True}

        # subsequent /auth/me should fail (user gone)
        me = requests.get(f"{API}/auth/me", headers=_auth(tok))
        assert me.status_code in (401, 404)

        # login should also fail
        login = requests.post(f"{API}/auth/login", json={"email": email, "password": "Test1234!"})
        assert login.status_code == 401
