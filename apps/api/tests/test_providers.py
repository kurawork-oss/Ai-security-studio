"""Unit tests for LLM provider adapters (mocked transport — no live API)."""

from __future__ import annotations

import json

import httpx
import pytest

from src.core.errors import ProviderError, ProviderNotSupported
from src.domain.value_objects import LlmRequest
from src.infrastructure.providers.claude import ClaudeAdapter
from src.infrastructure.providers.echo import EchoAdapter
from src.infrastructure.providers.openai import OpenAIAdapter
from src.infrastructure.providers.registry import ProviderRegistry


def _claude_handler(request: httpx.Request) -> httpx.Response:
    assert request.headers["x-api-key"] == "k"
    assert request.headers["anthropic-version"]
    body = json.loads(request.content)
    assert body["messages"][0]["content"] == "<PERSON_1>"  # only masked text is sent
    return httpx.Response(
        200,
        json={
            "model": "claude-test",
            "content": [{"type": "text", "text": "こんにちは"}],
            "usage": {"input_tokens": 3, "output_tokens": 2},
        },
    )


async def test_claude_complete():
    adapter = ClaudeAdapter(
        "https://api.anthropic.com", "claude-test", transport=httpx.MockTransport(_claude_handler)
    )
    resp = await adapter.complete(LlmRequest(prompt="<PERSON_1>"), api_key="k")
    assert resp.text == "こんにちは"
    assert resp.usage.input_tokens == 3 and resp.usage.output_tokens == 2


def _openai_handler(request: httpx.Request) -> httpx.Response:
    assert request.headers["authorization"] == "Bearer k"
    body = json.loads(request.content)
    assert body["messages"][-1]["content"] == "<EMAIL_ADDRESS_1>"
    return httpx.Response(
        200,
        json={
            "model": "gpt-test",
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 4},
        },
    )


async def test_openai_complete():
    adapter = OpenAIAdapter(
        "https://api.openai.com", "gpt-test", transport=httpx.MockTransport(_openai_handler)
    )
    resp = await adapter.complete(LlmRequest(prompt="<EMAIL_ADDRESS_1>"), api_key="k")
    assert resp.text == "ok"
    assert resp.usage.input_tokens == 5 and resp.usage.output_tokens == 4


async def test_missing_key_raises():
    with pytest.raises(ProviderError):
        await ClaudeAdapter("https://x", "m").complete(LlmRequest(prompt="x"), api_key=None)


async def test_missing_model_raises():
    adapter = OpenAIAdapter("https://x", "", transport=httpx.MockTransport(_openai_handler))
    with pytest.raises(ProviderError):
        await adapter.complete(LlmRequest(prompt="x"), api_key="k")


def test_openai_adapter_supports_compatible_types():
    # DeepSeek / Grok / local reuse the OpenAI-compatible adapter.
    assert OpenAIAdapter("https://x", "m", provider_type="deepseek").provider_type == "deepseek"


def test_registry_lookup_and_unknown():
    registry = ProviderRegistry()
    registry.register(EchoAdapter())
    registry.register(ClaudeAdapter("https://x", "m"))
    registry.register(OpenAIAdapter("https://x", "m"))
    assert registry.get("claude").provider_type == "claude"
    assert set(registry.supported()) >= {"echo", "claude", "openai"}
    with pytest.raises(ProviderNotSupported):
        registry.get("nonexistent")


def test_health_lists_all_providers(client):
    providers = client.get("/v1/health").json()["supportedProviders"]
    assert {"echo", "gemini", "claude", "openai"} <= set(providers)
