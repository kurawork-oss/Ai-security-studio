"""Tests for the plugin layer: extractors, extract/file input, batch, stream, webhook."""

from __future__ import annotations

import base64

from src.infrastructure.plugins.extractors import (
    CsvExtractor,
    HtmlExtractor,
    JsonExtractor,
    PlaintextExtractor,
)
from src.infrastructure.plugins.webhook import WebhookPlugin
from tests.conftest import ANALYZE_KEY, PROTECT_KEY, auth


def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


# ── extractor units ──
def test_extractors_produce_text():
    assert "taro@example.com" in PlaintextExtractor().extract(b"taro@example.com", "text/plain")
    csv_text = CsvExtractor().extract(b"name,email\nTanaka,taro@example.com", "text/csv")
    assert "taro@example.com" in csv_text
    json_text = JsonExtractor().extract(b'{"user":{"email":"taro@example.com"},"n":42}', "application/json")
    assert "taro@example.com" in json_text and "42" in json_text
    html_text = HtmlExtractor().extract(
        b"<html><body><p>mail taro@example.com</p><script>ignore()</script></body></html>",
        "text/html",
    )
    assert "taro@example.com" in html_text and "ignore" not in html_text


# ── /v1/plugins listing ──
def test_plugins_listing(client):
    plugins = {p["key"]: p for p in client.get("/v1/plugins").json()}
    assert "plaintext" in plugins and "csv" in plugins and "webhook" in plugins
    assert plugins["pdf"]["available"] is False  # declared stub
    assert plugins["csv"]["available"] is True


# ── /v1/extract (extract -> mask) ──
def test_extract_masks_from_html(client):
    r = client.post(
        "/v1/extract",
        json={"contentType": "text/html", "contentBase64": b64("<p>連絡は taro@example.com</p>")},
        headers=auth(PROTECT_KEY),
    )
    assert r.status_code == 200
    body = r.json()
    assert "taro@example.com" not in body["maskedText"]
    assert "<EMAIL_ADDRESS_1>" in body["maskedText"]


def test_extract_unsupported_type(client):
    r = client.post(
        "/v1/extract",
        json={"contentType": "application/pdf", "contentBase64": b64("x")},
        headers=auth(PROTECT_KEY),
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ── protect with file input ──
def test_protect_accepts_file_input(client):
    r = client.post(
        "/v1/protect",
        json={"contentType": "text/csv", "contentBase64": b64("name,email\nT,taro@example.com")},
        headers=auth(PROTECT_KEY),
    )
    assert r.status_code == 200
    assert "taro@example.com" not in r.json()["maskedText"]


# ── batch analyze ──
def test_batch_analyze(client):
    r = client.post(
        "/v1/batch/analyze",
        json={"texts": ["taro@example.com", "電話 090-1234-5678"]},
        headers=auth(ANALYZE_KEY),
    )
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 2
    assert "taro@example.com" not in results[0]["analysis"]


# ── streaming analyze ──
def test_analyze_stream(client):
    with client.stream(
        "POST", "/v1/analyze/stream", json={"text": "taro@example.com"}, headers=auth(ANALYZE_KEY)
    ) as r:
        assert r.status_code == 200
        body = "".join(chunk for chunk in r.iter_text())
    assert "taro@example.com" not in body
    assert "<EMAIL_ADDRESS_1>" in body


# ── webhook plugin (injected stub, no network) ──
async def test_webhook_plugin_delivers():
    captured: dict = {}

    async def poster(url: str, payload: dict) -> None:
        captured["url"] = url
        captured["payload"] = payload

    plugin = WebhookPlugin(poster)
    await plugin.deliver({"maskedText": "<EMAIL_ADDRESS_1>"}, {"url": "https://example.com/hook"})
    assert captured["url"] == "https://example.com/hook"
    assert captured["payload"]["maskedText"] == "<EMAIL_ADDRESS_1>"
