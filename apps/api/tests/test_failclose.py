"""Fail-closed guarantee: if anonymization fails, the LLM is never called."""

from __future__ import annotations

import pytest

from src.application.analyze import AnalyzeTextUseCase
from src.application.protect import ProtectTextUseCase
from src.core.errors import AnonymizationFailed
from src.domain.entities import Project, ProjectRuntime, Provider
from src.domain.services import Anonymizer
from src.domain.value_objects import LlmRequest, LlmResponse, ProviderCapabilities, TokenUsage
from src.infrastructure.crypto.keyprovider import build_cipher
from src.infrastructure.providers.registry import ProviderRegistry
from src.infrastructure.repositories.memory import default_rules


class FaultyDetector:
    name = "faulty"

    def detect(self, text, rules):
        raise RuntimeError("boom")


class SpyAdapter:
    provider_type = "spy"

    def __init__(self) -> None:
        self.called = False

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities()

    async def complete(self, req: LlmRequest, *, api_key: str | None) -> LlmResponse:
        self.called = True
        return LlmResponse(text="should not happen", model="spy", usage=TokenUsage())


@pytest.mark.asyncio
async def test_analyze_is_fail_closed():
    spy = SpyAdapter()
    registry = ProviderRegistry()
    registry.register(spy)

    protect_uc = ProtectTextUseCase(FaultyDetector(), Anonymizer())
    analyze_uc = AnalyzeTextUseCase(protect_uc, registry, build_cipher("env", "x" * 32))

    runtime = ProjectRuntime(
        project=Project(id="p", name="n"),
        rules=default_rules(),
        providers=[Provider(id="pr", project_id="p", provider_type="spy")],
    )

    with pytest.raises(AnonymizationFailed):
        await analyze_uc.execute("sensitive taro@example.com", runtime)

    assert spy.called is False, "provider must not be called when anonymization fails"


def test_protect_wraps_errors_as_anonymization_failed():
    protect_uc = ProtectTextUseCase(FaultyDetector(), Anonymizer())
    with pytest.raises(AnonymizationFailed):
        protect_uc.execute("x", default_rules())
