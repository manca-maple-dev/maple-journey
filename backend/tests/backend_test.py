"""MapleJourney backend API tests — post-refactor (Iteration 7).

Contract:
  - Feature flags: EXACTLY [questionnaire, timeline, documents, jobs, benefits, legal]
  - Removed endpoints: /applications*, /community/*, /messages* -> 404
  - Admin stats: total_users, total_documents, total_chats (no total_applications/total_posts)
"""
import os
import uuid
import pytest
import requests

def _load_backend_url():
    # Prefer OS env; else read frontend/.env so pytest works standalone.
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if url:
        return url.rstrip("/")
    env_path = "/app/frontend/.env"
    if os.path.exists(env_path):
        with open(env_path) as fh:
            for line in fh:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not configured")

BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@maplejourney.ca"
ADMIN_PASSWORD = "MapleAdmin!2026"

TEST_EMAIL = f"TEST_user_{uuid.uuid4().hex[:8]}@test.com"
TEST_PASSWORD = "StrongPass1!"
TEST_NAME = "TEST User"

EXPECTED_FEATURE_KEYS = {"questionnaire", "timeline", "documents", "jobs", "benefits", "legal"}
REMOVED_KEYS = {"applications", "ai_assistant", "messages", "community"}


@pytest.fixture(scope="session")
def session_state():
    return {}


@pytest.fixture(scope="session")
def user_token(session_state):
    r = requests.post(f"{API}/auth/register", json={
        "name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD, "country_of_origin": "India"
    })
    assert r.status_code == 200, r.text
    data = r.json()
    session_state["user_id"] = data["user"]["id"]
    return data["token"]


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["user"]["role"] == "admin"
    return d["token"]


def uh(t): return {"Authorization": f"Bearer {t}"}


# ---------- Auth ----------
class TestAuth:
    def test_root(self):
        r = requests.get(f"{API}/")
        assert r.status_code == 200 and r.json().get("status") == "ok"

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": "nobody@x.com", "password": "wrong"})
        assert r.status_code == 401

    def test_admin_login_returns_token_and_role(self, admin_token):
        assert isinstance(admin_token, str) and len(admin_token) > 20

    def test_register_duplicate(self, user_token):
        r = requests.post(f"{API}/auth/register", json={"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD})
        assert r.status_code == 400

    def test_me(self, user_token):
        r = requests.get(f"{API}/auth/me", headers=uh(user_token))
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == TEST_EMAIL.lower()
        assert d["role"] == "user"
        assert isinstance(d["features"], dict)

    def test_me_no_token(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code in (401, 403)


# ---------- Feature flag contract ----------
class TestFeaturesContract:
    def test_features_exact_keys(self, user_token):
        r = requests.get(f"{API}/features", headers=uh(user_token))
        assert r.status_code == 200
        d = r.json()
        assert set(d.keys()) == EXPECTED_FEATURE_KEYS, f"features mismatch: {set(d.keys())}"
        for k, v in d.items():
            assert isinstance(v, bool)
        for removed in REMOVED_KEYS:
            assert removed not in d


# ---------- Removed endpoints MUST be gone ----------
class TestRemovedEndpoints:
    def test_applications_404(self, user_token):
        r = requests.get(f"{API}/applications", headers=uh(user_token))
        assert r.status_code == 404, f"expected 404, got {r.status_code}"

    def test_community_posts_404(self, user_token):
        r = requests.get(f"{API}/community/posts", headers=uh(user_token))
        assert r.status_code == 404

    def test_messages_404(self, user_token):
        r = requests.get(f"{API}/messages", headers=uh(user_token))
        assert r.status_code == 404

    def test_post_applications_404(self, user_token):
        r = requests.post(f"{API}/applications", headers=uh(user_token), json={"title": "x"})
        assert r.status_code == 404

    def test_post_community_404(self, user_token):
        r = requests.post(f"{API}/community/posts", headers=uh(user_token), json={"content": "x"})
        assert r.status_code == 404

    def test_post_messages_404(self, user_token):
        r = requests.post(f"{API}/messages", headers=uh(user_token), json={"content": "x"})
        assert r.status_code == 404


# ---------- Maple Wingman ----------
class TestMapleWingman:
    def test_briefing(self, user_token):
        r = requests.get(f"{API}/wings/briefing", headers=uh(user_token), timeout=45)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("greeting", "suggestions", "stats"):
            assert k in d
        assert isinstance(d["greeting"], str) and len(d["greeting"]) > 0
        assert isinstance(d["suggestions"], list)

    def test_settings_update(self, user_token):
        r = requests.put(f"{API}/wings/settings", headers=uh(user_token), json={"tone": "concise", "autonomy": "auto"})
        assert r.status_code == 200
        d = r.json()
        assert d["tone"] == "concise" and d["autonomy"] == "auto"


# ---------- Questionnaire ----------
class TestQuestionnaire:
    def test_get_empty(self, user_token):
        r = requests.get(f"{API}/questionnaire", headers=uh(user_token))
        assert r.status_code == 200
        assert "answers" in r.json() and "score" in r.json()

    def test_post_computes_and_persists(self, user_token):
        payload = {"age": 28, "education": "bachelor", "language": "advanced",
                   "experience_years": 3, "canadian_experience": False, "job_offer": False,
                   "provincial_nomination": False, "marital_status": "single"}
        r = requests.post(f"{API}/questionnaire", headers=uh(user_token), json=payload)
        assert r.status_code == 200
        d = r.json()
        assert d["score"] == 375
        r2 = requests.get(f"{API}/questionnaire", headers=uh(user_token))
        assert r2.json()["score"] == 375


# ---------- Timeline / Documents / Jobs / Benefits / Legal ----------
class TestTimeline:
    def test_add_and_list(self, user_token):
        r = requests.post(f"{API}/timeline", headers=uh(user_token), json={"title": "TEST_M", "status": "upcoming"})
        assert r.status_code == 200
        mid = r.json()["id"]
        r2 = requests.get(f"{API}/timeline", headers=uh(user_token))
        assert any(m["id"] == mid for m in r2.json())
        r3 = requests.put(f"{API}/timeline/{mid}", headers=uh(user_token), json={"title": "TEST_M2", "status": "active"})
        assert r3.status_code == 200


class TestDocuments:
    def test_crud(self, user_token):
        r = requests.post(f"{API}/documents", headers=uh(user_token), json={"name": "TEST_Passport", "status": "pending"})
        assert r.status_code == 200
        did = r.json()["id"]
        r2 = requests.get(f"{API}/documents", headers=uh(user_token))
        assert any(x["id"] == did for x in r2.json())
        r3 = requests.put(f"{API}/documents/{did}", headers=uh(user_token), json={"name": "TEST_Passport2", "status": "verified"})
        assert r3.status_code == 200 and r3.json()["status"] == "verified"
        r4 = requests.delete(f"{API}/documents/{did}", headers=uh(user_token))
        assert r4.status_code == 200


class TestJobs:
    def test_list_and_toggle_save(self, user_token):
        r = requests.get(f"{API}/jobs", headers=uh(user_token))
        assert r.status_code == 200
        jobs = r.json()
        assert len(jobs) > 0
        assert "saved" in jobs[0]
        jid = jobs[0]["id"]
        r2 = requests.post(f"{API}/jobs/{jid}/save", headers=uh(user_token))
        assert r2.json()["saved"] is True
        r3 = requests.post(f"{API}/jobs/{jid}/save", headers=uh(user_token))
        assert r3.json()["saved"] is False


class TestBenefits:
    def test_list(self, user_token):
        r = requests.get(f"{API}/benefits", headers=uh(user_token))
        assert r.status_code == 200 and len(r.json()) > 0


class TestLegal:
    def test_list(self, user_token):
        r = requests.get(f"{API}/legal-resources", headers=uh(user_token))
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 8
        assert "_id" not in items[0]


# ---------- Maple Wingman Chat (streaming) ----------
class TestAssistantChat:
    def test_stream_and_history(self, user_token):
        r = requests.post(f"{API}/assistant/chat", headers=uh(user_token),
                          json={"message": "In one short sentence, what is Express Entry?"}, stream=True, timeout=90)
        assert r.status_code == 200
        assert "X-Session-Id" in r.headers
        sid = r.headers["X-Session-Id"]
        text = ""
        for c in r.iter_content(chunk_size=None, decode_unicode=True):
            if c:
                text += c
        assert len(text) > 5, f"empty stream: {text!r}"
        # history
        r2 = requests.get(f"{API}/assistant/history", headers=uh(user_token), params={"session_id": sid})
        assert r2.status_code == 200
        hist = r2.json()
        assert len(hist) >= 2
        roles = [h["role"] for h in hist]
        assert "user" in roles and "assistant" in roles


# ---------- Admin ----------
class TestAdmin:
    def test_stats_contract(self, admin_token):
        r = requests.get(f"{API}/admin/stats", headers=uh(admin_token))
        assert r.status_code == 200
        d = r.json()
        for k in ("total_users", "total_documents", "total_chats"):
            assert k in d
        for removed in ("total_applications", "total_posts"):
            assert removed not in d, f"{removed} should have been removed"
        assert set(d["global_features"].keys()) == EXPECTED_FEATURE_KEYS

    def test_users_list(self, admin_token):
        r = requests.get(f"{API}/admin/users", headers=uh(admin_token))
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_users_forbidden_for_user(self, user_token):
        r = requests.get(f"{API}/admin/users", headers=uh(user_token))
        assert r.status_code == 403

    def test_admin_features_get_and_put(self, admin_token):
        r = requests.get(f"{API}/admin/features", headers=uh(admin_token))
        assert r.status_code == 200
        assert set(r.json().keys()) == EXPECTED_FEATURE_KEYS
        r2 = requests.put(f"{API}/admin/features", headers=uh(admin_token), json={"features": {"jobs": False}})
        assert r2.status_code == 200 and r2.json()["jobs"] is False
        r3 = requests.put(f"{API}/admin/features", headers=uh(admin_token), json={"features": {"jobs": True}})
        assert r3.json()["jobs"] is True

    def test_user_feature_toggle(self, admin_token, user_token, session_state):
        uid = session_state["user_id"]
        r = requests.put(f"{API}/admin/users/{uid}/features", headers=uh(admin_token), json={"features": {"legal": False}})
        assert r.status_code == 200 and r.json()["features"]["legal"] is False
        r2 = requests.get(f"{API}/features", headers=uh(user_token))
        assert r2.json()["legal"] is False
        r3 = requests.put(f"{API}/admin/users/{uid}/features", headers=uh(admin_token), json={"features": {"legal": True}})
        assert r3.json()["features"]["legal"] is True

    def test_content_crud(self, admin_token):
        r = requests.put(f"{API}/admin/content", headers=uh(admin_token), json={"hero_title": "TEST Hero"})
        assert r.status_code == 200
        r2 = requests.get(f"{API}/content")
        assert r2.json().get("hero_title") == "TEST Hero"

    def test_resource_add_delete(self, admin_token):
        r = requests.post(f"{API}/admin/resources", headers=uh(admin_token), json={"title": "TEST_r", "category": "T", "description": "d"})
        assert r.status_code == 200
        rid = r.json()["id"]
        assert requests.delete(f"{API}/admin/resources/{rid}", headers=uh(admin_token)).status_code == 200

    def test_benefit_add_delete(self, admin_token):
        r = requests.post(f"{API}/admin/benefits", headers=uh(admin_token), json={"title": "TEST_b", "category": "T", "description": "d"})
        bid = r.json()["id"]
        assert requests.delete(f"{API}/admin/benefits/{bid}", headers=uh(admin_token)).status_code == 200

    def test_legal_add_delete(self, admin_token):
        r = requests.post(f"{API}/admin/legal-resources", headers=uh(admin_token), json={
            "name": "TEST_LA", "type": "Refugee", "province": "Ontario", "cost": "Free", "description": "d"
        })
        assert r.status_code == 200
        lid = r.json()["id"]
        assert requests.delete(f"{API}/admin/legal-resources/{lid}", headers=uh(admin_token)).status_code == 200

    def test_announcement_add_delete(self, admin_token):
        r = requests.post(f"{API}/admin/announcements", headers=uh(admin_token), json={"title": "TEST_ann", "body": "b", "tone": "info"})
        assert r.status_code == 200
        aid = r.json()["id"]
        assert requests.delete(f"{API}/admin/announcements/{aid}", headers=uh(admin_token)).status_code == 200


# ---------- Twilio contract (endpoints exist + validate) ----------
class TestTwilioContracts:
    def test_send_otp_short_number(self, user_token):
        r = requests.post(f"{API}/phone/send-otp", headers=uh(user_token), json={"phone": "12"})
        assert r.status_code == 400

    def test_verify_otp_bogus_never_200(self, user_token):
        r = requests.post(f"{API}/phone/verify-otp", headers=uh(user_token), json={"phone": "+14155551234", "code": "000000"})
        assert r.status_code != 200
        assert r.status_code in (400, 502)

    def test_whatsapp_test_without_verified_phone(self, user_token):
        r = requests.post(f"{API}/whatsapp/test", headers=uh(user_token))
        assert r.status_code == 400


# ---------- Signup + Onboarding profile contract (Iteration 4) ----------
class TestSignupAndProfileContract:
    def test_signup_minimal_payload(self):
        """Sign up form now sends ONLY {name,email,password}."""
        email = f"TEST_signup_{uuid.uuid4().hex[:8]}@test.com"
        r = requests.post(f"{API}/auth/register", json={
            "name": "QA Tester", "email": email, "password": "StrongPass1!"
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert "token" in d and isinstance(d["token"], str) and len(d["token"]) > 20
        assert d["user"]["email"] == email.lower()
        assert d["user"]["name"] == "QA Tester"
        assert d["user"]["role"] == "user"

    def test_signup_duplicate_email_returns_400(self):
        email = f"TEST_dup_{uuid.uuid4().hex[:8]}@test.com"
        r1 = requests.post(f"{API}/auth/register", json={"name": "A", "email": email, "password": "StrongPass1!"})
        assert r1.status_code == 200
        r2 = requests.post(f"{API}/auth/register", json={"name": "A", "email": email, "password": "StrongPass1!"})
        assert r2.status_code == 400

    def test_login_after_signup(self):
        email = f"TEST_login_{uuid.uuid4().hex[:8]}@test.com"
        r = requests.post(f"{API}/auth/register", json={"name": "L", "email": email, "password": "StrongPass1!"})
        assert r.status_code == 200
        r2 = requests.post(f"{API}/auth/login", json={"email": email, "password": "StrongPass1!"})
        assert r2.status_code == 200
        assert r2.json()["user"]["email"] == email.lower()

    def test_profile_get_and_put_persists_onboarding(self):
        email = f"TEST_prof_{uuid.uuid4().hex[:8]}@test.com"
        r = requests.post(f"{API}/auth/register", json={"name": "P", "email": email, "password": "StrongPass1!"})
        token = r.json()["token"]

        g0 = requests.get(f"{API}/profile", headers=uh(token))
        assert g0.status_code == 200
        assert g0.json()["completed"] is False

        payload = {
            "preferred_name": "Pat",
            "arrival_status": "planning",
            "immigration_category": "express_entry",
            "languages_spoken": ["English", "French"],
            "consent_data_personalization": True,
            "has_sin": False,
        }
        p = requests.put(f"{API}/profile", headers=uh(token), json=payload)
        assert p.status_code == 200, p.text
        assert p.json()["completed"] is True
        assert p.json()["profile"]["preferred_name"] == "Pat"
        assert p.json()["profile"]["languages_spoken"] == ["English", "French"]

        g = requests.get(f"{API}/profile", headers=uh(token))
        assert g.status_code == 200
        assert g.json()["completed"] is True
        assert g.json()["profile"]["immigration_category"] == "express_entry"

        me = requests.get(f"{API}/auth/me", headers=uh(token))
        assert me.status_code == 200
        assert me.json().get("profile_completed") is True

    def test_profile_requires_auth(self):
        r = requests.put(f"{API}/profile", json={"preferred_name": "X"})
        assert r.status_code in (401, 403)
