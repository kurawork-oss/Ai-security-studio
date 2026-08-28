"""OpenAI (Chat Completions API) provider adapter.

Also usable for OpenAI-compatible endpoints (DeepSeek / Grok / local) by
pointing ``api_base`` at the compatible server. The prompt is always already
anonymized by the Analyze use case.
"""

from __future__ import annotations

import httpx

from ...core.errors import ProviderError
from ...domain.value_objects import LlmRequest, LlmResponse, ProviderCapabilities, TokenUsage


class OpenAIAdapter:
    provider_type = "openai"

    def __init__(
        self,
        api_base: str,
        default_model: str,
        *,
        provider_type: str = "openai",
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.provider_type = provider_type
        self._api_base = api_base.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout
        self._transport = transport

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(streaming=True, default_model=self._default_model or None)

    async def complete(self, req: LlmRequest, *, api_key: str | None) -> LlmResponse:
        if not api_key:
            raise ProviderError(f"Missing API key for {self.provider_type} provider")
        model = req.model or self._default_model
        if not model:
            raise ProviderError(f"No model configured for {self.provider_type} provider")

        messages = []
        if req.system:
            messages.append({"role": "system", "content": req.system})
        messages.append({"role": "user", "content": req.prompt})
        payload: dict = {"model": model, "messages": messages}
        if req.max_tokens is not None:
            payload["max_tokens"] = req.max_tokens
        if req.temperature is not None:
            payload["temperature"] = req.temperature

        headers = {"Authorization": f"Bearer {api_key}", "content-type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                resp = await client.post(
                    f"{self._api_base}/v1/chat/completions", headers=headers, json=payload
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.provider_type} request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise ProviderError(
                f"{self.provider_type} returned an error", details={"status": resp.status_code}
            )
        return self._parse(resp.json(), model)

    @staticmethod
    def _parse(data: dict, model: str) -> LlmResponse:
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Unexpected OpenAI response shape") from exc
        usage = data.get("usage", {})
        return LlmResponse(
            text=text or "",
            model=data.get("model", model),
            usage=TokenUsage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            ),
        )
