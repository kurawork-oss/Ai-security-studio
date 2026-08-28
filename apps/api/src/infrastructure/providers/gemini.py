"""Gemini provider adapter (the MVP provider).

Talks to the Google Generative Language API. The prompt passed in is always
already anonymized by the Analyze use case.
"""

from __future__ import annotations

import httpx

from ...core.errors import ProviderError
from ...domain.value_objects import LlmRequest, LlmResponse, ProviderCapabilities, TokenUsage


class GeminiAdapter:
    provider_type = "gemini"

    def __init__(self, api_base: str, default_model: str, *, timeout: float = 30.0) -> None:
        self._api_base = api_base.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            streaming=True, vision=True, default_model=self._default_model
        )

    async def complete(self, req: LlmRequest, *, api_key: str | None) -> LlmResponse:
        if not api_key:
            raise ProviderError("Missing Gemini API key for provider")
        model = req.model or self._default_model
        url = f"{self._api_base}/v1beta/models/{model}:generateContent"
        payload: dict = {"contents": [{"parts": [{"text": req.prompt}]}]}
        if req.system:
            payload["systemInstruction"] = {"parts": [{"text": req.system}]}
        gen_config: dict = {}
        if req.max_tokens is not None:
            gen_config["maxOutputTokens"] = req.max_tokens
        if req.temperature is not None:
            gen_config["temperature"] = req.temperature
        if gen_config:
            payload["generationConfig"] = gen_config

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    url, params={"key": api_key}, json=payload
                )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise ProviderError(
                "Gemini returned an error",
                details={"status": resp.status_code},
            )
        return self._parse(resp.json(), model)

    @staticmethod
    def _parse(data: dict, model: str) -> LlmResponse:
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError) as exc:
            raise ProviderError("Unexpected Gemini response shape") from exc
        usage_meta = data.get("usageMetadata", {})
        usage = TokenUsage(
            input_tokens=usage_meta.get("promptTokenCount", 0),
            output_tokens=usage_meta.get("candidatesTokenCount", 0),
        )
        return LlmResponse(text=text, model=model, usage=usage)
