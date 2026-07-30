"""Claude (Anthropic Messages API) provider adapter.

The prompt is always already anonymized by the Analyze use case.
"""

from __future__ import annotations

import httpx

from ...core.errors import ProviderError
from ...domain.value_objects import LlmRequest, LlmResponse, ProviderCapabilities, TokenUsage


class ClaudeAdapter:
    provider_type = "claude"

    def __init__(
        self,
        api_base: str,
        default_model: str,
        *,
        api_version: str = "2023-06-01",
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._default_model = default_model
        self._api_version = api_version
        self._timeout = timeout
        self._transport = transport

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(streaming=True, vision=True, default_model=self._default_model or None)

    async def complete(self, req: LlmRequest, *, api_key: str | None) -> LlmResponse:
        if not api_key:
            raise ProviderError("Missing Claude API key for provider")
        model = req.model or self._default_model
        if not model:
            raise ProviderError("No model configured for Claude provider")

        payload: dict = {
            "model": model,
            "max_tokens": req.max_tokens or 1024,
            "messages": [{"role": "user", "content": req.prompt}],
        }
        if req.system:
            payload["system"] = req.system
        if req.temperature is not None:
            payload["temperature"] = req.temperature

        headers = {
            "x-api-key": api_key,
            "anthropic-version": self._api_version,
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                resp = await client.post(f"{self._api_base}/v1/messages", headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise ProviderError(f"Claude request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise ProviderError("Claude returned an error", details={"status": resp.status_code})
        return self._parse(resp.json(), model)

    @staticmethod
    def _parse(data: dict, model: str) -> LlmResponse:
        try:
            blocks = data["content"]
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise ProviderError("Unexpected Claude response shape") from exc
        usage = data.get("usage", {})
        return LlmResponse(
            text=text,
            model=data.get("model", model),
            usage=TokenUsage(
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            ),
        )
