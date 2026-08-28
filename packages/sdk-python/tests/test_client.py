from __future__ import annotations

import httpx
import pytest

from secureai import SecureAI, SecureAIError


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.headers["authorization"] == "Bearer sk_test"
    path = request.url.path
    if path == "/v1/protect":
        return httpx.Response(
            200,
            json={
                "maskedText": "<EMAIL_ADDRESS_1>",
                "requestId": "req_1",
                "entities": [
                    {"entityType": "EMAIL_ADDRESS", "start": 0, "end": 16, "score": 0.95}
                ],
            },
        )
    if path == "/v1/analyze":
        return httpx.Response(
            200,
            json={"analysis": "ok <PERSON_1>", "requestId": "req_2",
                  "usage": {"inputTokens": 3, "outputTokens": 5}},
        )
    if path == "/v1/detect":
        return httpx.Response(
            200, json={"entities": [], "entityCounts": {"EMAIL_ADDRESS": 1}, "requestId": "req_3"}
        )
    return httpx.Response(404, json={"error": {"code": "NOT_FOUND", "message": "nope"}})


def _client(handler=_handler) -> SecureAI:
    return SecureAI("sk_test", base_url="https://api.test", transport=httpx.MockTransport(handler))


def test_protect_parses_result():
    with _client() as c:
        r = c.protect("taro@example.com", return_entities=True)
    assert r.masked_text == "<EMAIL_ADDRESS_1>"
    assert r.request_id == "req_1"
    assert r.entities[0].entity_type == "EMAIL_ADDRESS"


def test_analyze_parses_usage():
    with _client() as c:
        r = c.analyze("x", deanonymize=True)
    assert r.analysis.startswith("ok")
    assert r.output_tokens == 5


def test_detect_counts():
    with _client() as c:
        assert c.detect("x").entity_counts["EMAIL_ADDRESS"] == 1


def test_error_maps_to_exception():
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"code": "FORBIDDEN", "message": "no", "requestId": "r"}})

    with pytest.raises(SecureAIError) as ei:
        _client(handler).protect("x")
    assert ei.value.code == "FORBIDDEN"
    assert ei.value.status == 403


def test_requires_api_key():
    with pytest.raises(ValueError):
        SecureAI("")
