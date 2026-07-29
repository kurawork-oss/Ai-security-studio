"""Echo adapter — a dev/test provider that performs no external call.

Useful to exercise the Analyze pipeline end-to-end (and to prove that only
anonymized text reaches the provider) without needing real credentials.
"""

from __future__ import annotations

from ...domain.value_objects import LlmRequest, LlmResponse, ProviderCapabilities, TokenUsage


class EchoAdapter:
    provider_type = "echo"

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(default_model="echo-1")

    async def complete(self, req: LlmRequest, *, api_key: str | None) -> LlmResponse:
        # The prompt is already anonymized by the Analyze use case.
        analysis = f"分析結果(echo): 受信したマスク済みテキストを要約しました → {req.prompt}"
        words = max(1, len(req.prompt.split()))
        return LlmResponse(
            text=analysis,
            model=req.model or "echo-1",
            usage=TokenUsage(input_tokens=words, output_tokens=len(analysis.split())),
        )
