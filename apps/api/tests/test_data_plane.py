"""Integration tests for the Data Plane API (Protect / Analyze / Detect / auth)."""

from __future__ import annotations

from tests.conftest import ANALYZE_KEY, PROTECT_KEY, auth


def test_health(client):
    r = client.get("/v1/health")
    assert r.status_code == 200
    assert "echo" in r.json()["supportedProviders"]


def test_protect_masks_pii(client):
    r = client.post(
        "/v1/protect",
        json={"text": "メールは taro@example.com です", "options": {"returnEntities": True}},
        headers=auth(PROTECT_KEY),
    )
    assert r.status_code == 200
    body = r.json()
    assert "taro@example.com" not in body["maskedText"]
    assert "<EMAIL_ADDRESS_1>" in body["maskedText"]
    assert any(e["entityType"] == "EMAIL_ADDRESS" for e in body["entities"])
    assert body["requestId"].startswith("req_")


def test_protect_requires_key(client):
    r = client.post("/v1/protect", json={"text": "x"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_protect_rejects_analyze_key(client):
    r = client.post("/v1/protect", json={"text": "x"}, headers=auth(ANALYZE_KEY))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_protect_rule_override_disables_type(client):
    r = client.post(
        "/v1/protect",
        json={"text": "taro@example.com", "options": {"rules": {"EMAIL_ADDRESS": False}}},
        headers=auth(PROTECT_KEY),
    )
    assert r.status_code == 200
    assert r.json()["maskedText"] == "taro@example.com"


def test_detect_returns_metadata_only(client):
    r = client.post(
        "/v1/detect",
        json={"text": "taro@example.com 090-1234-5678"},
        headers=auth(PROTECT_KEY),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["entityCounts"].get("EMAIL_ADDRESS") == 1
    # Response must not leak raw values.
    assert "taro@example.com" not in r.text


def test_analyze_only_sends_masked_text(client):
    original = "山田花子さんの email は taro@example.com、電話 090-1234-5678"
    r = client.post("/v1/analyze", json={"text": original}, headers=auth(ANALYZE_KEY))
    assert r.status_code == 200
    body = r.json()
    # Echo provider returns the exact text it received: prove it was masked.
    assert "taro@example.com" not in body["analysis"]
    assert "山田花子" not in body["analysis"]
    assert "090-1234-5678" not in body["analysis"]
    assert "<EMAIL_ADDRESS_1>" in body["analysis"]
    assert body["usage"]["inputTokens"] >= 0


def test_analyze_deanonymize_restores(client):
    r = client.post(
        "/v1/analyze",
        json={"text": "taro@example.com へ連絡", "options": {"deanonymize": True}},
        headers=auth(ANALYZE_KEY),
    )
    assert r.status_code == 200
    # With de-anonymization the original value reappears in the response.
    assert "taro@example.com" in r.json()["analysis"]


def test_analyze_rejects_protect_key(client):
    r = client.post("/v1/analyze", json={"text": "x"}, headers=auth(PROTECT_KEY))
    assert r.status_code == 403
