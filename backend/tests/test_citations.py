from services.rag import enforce_citation_policy


def test_citation_policy_accepts_allowed_domain():
    text = "Use this guide. [Source: https://www.canada.ca/en/immigration-refugees-citizenship.html, published 2026-07-01]"
    out, ok, reason = enforce_citation_policy(text)
    assert ok is True
    assert reason == "ok"
    assert out == text


def test_citation_policy_rejects_missing_citation():
    out, ok, reason = enforce_citation_policy("General advice without sources")
    assert ok is False
    assert reason == "missing-citation"
    assert "canada.ca" in out


def test_citation_policy_rejects_disallowed_domain():
    text = "Bad source. [Source: https://example.com/policy, published 2026-07-01]"
    out, ok, reason = enforce_citation_policy(text)
    assert ok is False
    assert reason == "disallowed-domain"
    assert "laws-lois.justice.gc.ca" in out
