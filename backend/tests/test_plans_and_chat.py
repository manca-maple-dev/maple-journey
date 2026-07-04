"""Iteration 5: plans, checkout session, chat usage, and profile gating contract."""
import os, uuid, pytest, requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if url: return url.rstrip("/")
    with open("/app/frontend/.env") as fh:
        for line in fh:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    raise RuntimeError("no backend url")

BASE = _load_backend_url()
API = f"{BASE}/api"

def uh(t): return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def fresh_user():
    email = f"TEST_plan_{uuid.uuid4().hex[:8]}@test.com"
    r = requests.post(f"{API}/auth/register", json={"name": "Plan Tester", "email": email, "password": "StrongPass1!"})
    assert r.status_code == 200, r.text
    return {"email": email, "token": r.json()["token"], "user": r.json()["user"]}


# ---------- Plans catalogue ----------
class TestPlans:
    def test_list_plans_public(self):
        r = requests.get(f"{API}/plans")
        assert r.status_code == 200
        plans = r.json()
        assert isinstance(plans, list) and len(plans) == 3
        by_id = {p["id"]: p for p in plans}
        assert set(by_id) == {"free", "plus", "family"}
        assert by_id["free"]["price"] == 0.0
        assert by_id["plus"]["price"] == 2.99
        assert by_id["family"]["price"] == 4.99
        for p in plans:
            assert "features" in p and isinstance(p["features"], list)


# ---------- Checkout session ----------
class TestCheckoutSession:
    def test_checkout_requires_auth(self):
        r = requests.post(f"{API}/checkout/session", json={"plan_id": "plus", "origin_url": BASE})
        assert r.status_code in (401, 403)

    def test_checkout_free_returns_400(self, fresh_user):
        r = requests.post(f"{API}/checkout/session", headers=uh(fresh_user["token"]),
                          json={"plan_id": "free", "origin_url": BASE})
        assert r.status_code == 400

    def test_checkout_invalid_plan_returns_400(self, fresh_user):
        r = requests.post(f"{API}/checkout/session", headers=uh(fresh_user["token"]),
                          json={"plan_id": "enterprise", "origin_url": BASE})
        assert r.status_code == 400

    def test_checkout_plus_returns_stripe_url(self, fresh_user):
        r = requests.post(f"{API}/checkout/session", headers=uh(fresh_user["token"]),
                          json={"plan_id": "plus", "origin_url": BASE})
        assert r.status_code == 200, r.text
        d = r.json()
        assert "url" in d and "session_id" in d
        assert "checkout.stripe.com" in d["url"], f"expected stripe URL, got: {d['url']}"
        assert isinstance(d["session_id"], str) and len(d["session_id"]) > 0

    def test_checkout_family_returns_stripe_url(self, fresh_user):
        r = requests.post(f"{API}/checkout/session", headers=uh(fresh_user["token"]),
                          json={"plan_id": "family", "origin_url": BASE})
        assert r.status_code == 200
        assert "checkout.stripe.com" in r.json()["url"]


# ---------- Assistant usage ----------
class TestAssistantUsage:
    def test_usage_shape_free_tier(self, fresh_user):
        r = requests.get(f"{API}/assistant/usage", headers=uh(fresh_user["token"]))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["tier"] == "free"
        assert d["unlimited"] is False
        assert d["limit"] == 8
        assert isinstance(d["used"], int)
        assert d["remaining"] == max(0, 8 - d["used"])

    def test_usage_requires_auth(self):
        r = requests.get(f"{API}/assistant/usage")
        assert r.status_code in (401, 403)

    def test_chat_increments_usage(self, fresh_user):
        before = requests.get(f"{API}/assistant/usage", headers=uh(fresh_user["token"])).json()["used"]
        r = requests.post(f"{API}/assistant/chat", headers=uh(fresh_user["token"]),
                          json={"message": "In one short sentence, what is a SIN?"}, stream=True, timeout=90)
        assert r.status_code == 200
        text = ""
        for c in r.iter_content(chunk_size=None, decode_unicode=True):
            if c: text += c
        assert len(text) > 3
        after = requests.get(f"{API}/assistant/usage", headers=uh(fresh_user["token"])).json()["used"]
        assert after == before + 1, f"used should increment by 1: before={before}, after={after}"


# ---------- Profile gating: profile_completed flips true on PUT /profile ----------
class TestProfileCompletionFlag:
    def test_profile_completed_false_after_register(self):
        email = f"TEST_gate_{uuid.uuid4().hex[:8]}@test.com"
        r = requests.post(f"{API}/auth/register", json={"name": "G", "email": email, "password": "StrongPass1!"})
        assert r.status_code == 200
        tok = r.json()["token"]
        me = requests.get(f"{API}/auth/me", headers=uh(tok)).json()
        assert me.get("profile_completed") in (False, None)

    def test_profile_completed_true_after_put(self):
        email = f"TEST_gate2_{uuid.uuid4().hex[:8]}@test.com"
        r = requests.post(f"{API}/auth/register", json={"name": "G", "email": email, "password": "StrongPass1!"})
        tok = r.json()["token"]
        p = requests.put(f"{API}/profile", headers=uh(tok), json={
            "preferred_name": "Pat", "arrival_status": "planning",
            "immigration_category": "student", "consent_data_personalization": True
        })
        assert p.status_code == 200 and p.json()["completed"] is True
        me = requests.get(f"{API}/auth/me", headers=uh(tok)).json()
        assert me["profile_completed"] is True
