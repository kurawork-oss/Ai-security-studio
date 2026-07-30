"""Analyze use case — Pattern B.

Order of operations enforces fail-closed: PII is anonymized FIRST, and only the
masked text is ever sent to the provider. If anonymization raises, the provider
is never called.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from ..core.errors import ProviderError, ValidationError
from ..domain.entities import ProjectRuntime
from ..domain.services import deanonymize
from ..domain.value_objects import LlmRequest, ProtectionResult, TokenUsage
from ..infrastructure.crypto.keyprovider import AesGcmCipher
from ..infrastructure.providers.registry import ProviderRegistry
from .protect import ProtectTextUseCase


@dataclass(frozen=True)
class AnalyzeOutcome:
    analysis: str
    usage: TokenUsage
    protection: ProtectionResult
    provider_type: str
    model: str


class AnalyzeTextUseCase:
    def __init__(
        self,
        protect_uc: ProtectTextUseCase,
        registry: ProviderRegistry,
        cipher: AesGcmCipher,
    ) -> None:
        self._protect = protect_uc
        self._registry = registry
        self._cipher = cipher

    async def execute(
        self,
        text: str,
        runtime: ProjectRuntime,
        *,
        provider_id: str | None = None,
        model: str | None = None,
        deanonymize_response: bool = False,
    ) -> AnalyzeOutcome:
        # 1) Anonymize first (raises AnonymizationFailed -> provider never called).
        protection = self._protect.execute(text, runtime.enabled_rules())

        # 2) Resolve provider + decrypt its key.
        provider = runtime.provider(provider_id)
        if provider is None:
            raise ValidationError("No active provider configured for this project")
        adapter = self._registry.get(provider.provider_type)

        api_key: str | None = None
        if provider.encrypted_key:
            try:
                api_key = self._cipher.decrypt(provider.encrypted_key)
            except Exception as exc:
                raise ProviderError("Failed to access provider credential") from exc

        # 3) Only the masked text leaves our system.
        req = LlmRequest(prompt=protection.masked_text, model=model or provider.default_model)
        response = await adapter.complete(req, api_key=api_key)

        # 4) Optionally restore original values in the response (in-memory only).
        analysis = response.text
        if deanonymize_response:
            analysis = deanonymize(analysis, protection.mapping)

        return AnalyzeOutcome(
            analysis=analysis,
            usage=response.usage,
            protection=protection,
            provider_type=provider.provider_type,
            model=response.model,
        )

    async def stream(
        self,
        text: str,
        runtime: ProjectRuntime,
        *,
        provider_id: str | None = None,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream the analysis. Anonymization runs eagerly here so that a
        failure raises BEFORE any bytes are streamed (fail-closed)."""
        protection = self._protect.execute(text, runtime.enabled_rules())

        provider = runtime.provider(provider_id)
        if provider is None:
            raise ValidationError("No active provider configured for this project")
        adapter = self._registry.get(provider.provider_type)

        api_key: str | None = None
        if provider.encrypted_key:
            try:
                api_key = self._cipher.decrypt(provider.encrypted_key)
            except Exception as exc:
                raise ProviderError("Failed to access provider credential") from exc

        req = LlmRequest(prompt=protection.masked_text, model=model or provider.default_model)
        stream_fn = getattr(adapter, "stream", None)

        async def gen() -> AsyncIterator[str]:
            if stream_fn is not None:
                async for chunk in stream_fn(req, api_key=api_key):
                    yield chunk
            else:  # provider has no streaming: emit the full completion once
                response = await adapter.complete(req, api_key=api_key)
                yield response.text

        return gen()
