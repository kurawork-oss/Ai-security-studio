"""Unit tests for the Export module renderers (no DB required)."""

from __future__ import annotations

import pytest

from src.application.export import TARGET_META, ExportContext, render
from src.core.errors import ValidationError


def test_render_protect_prompt():
    ctx = ExportContext(
        pattern="protect",
        language="typescript",
        api_base_url="https://api.example.com",
        enabled_rules=["EMAIL_ADDRESS", "PERSON"],
        key_env_var="SECUREAI_PROTECT_KEY",
    )
    art = render("claude_code", ctx)
    assert art.target_id == "claude_code"
    assert "SECUREAI_PROTECT_KEY" in art.content
    assert "/v1/protect" in art.content
    assert "EMAIL_ADDRESS" in art.content
    # never embed a real key
    assert "sk_protect_" not in art.content


def test_render_analyze_mentions_provider():
    ctx = ExportContext(
        pattern="analyze",
        language="python",
        api_base_url="https://api.example.com",
        enabled_rules=["PERSON"],
        key_env_var="SECUREAI_ANALYZE_KEY",
        provider_type="gemini",
    )
    art = render("cursor", ctx)
    assert "/v1/analyze" in art.content
    assert "gemini" in art.content


def test_all_targets_render():
    ctx = ExportContext("protect", "typescript", "https://api.x", [], "SECUREAI_PROTECT_KEY")
    for t in TARGET_META:
        assert render(t["id"], ctx).content


def test_unknown_target_raises():
    ctx = ExportContext("protect", "typescript", "https://api.x", [], "K")
    with pytest.raises(ValidationError):
        render("nope", ctx)
