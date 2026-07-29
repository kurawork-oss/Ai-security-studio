"""Ports (interfaces) — the boundaries the application depends on.

Infrastructure provides implementations; the application layer depends only on
these Protocols. This keeps the PII engine, providers and persistence swappable
(Dependency Inversion).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from .entities import ApiKey, ProjectRuntime, ProtectRule
from .value_objects import LlmRequest, LlmResponse, PiiSpan, ProviderCapabilities


@runtime_checkable
class PiiDetector(Protocol):
    """Detects PII spans in text according to the enabled rules.

    Implementations: RegexPiiDetector (default), PresidioPiiDetector (optional).
    """

    name: str

    def detect(self, text: str, rules: Sequence[ProtectRule]) -> list[PiiSpan]: ...


@runtime_checkable
class ProviderAdapter(Protocol):
    """Abstraction over an LLM provider. The prompt is always anonymized."""

    provider_type: str

    def capabilities(self) -> ProviderCapabilities: ...

    async def complete(self, req: LlmRequest, *, api_key: str | None) -> LlmResponse: ...


class ApiKeyRepository(Protocol):
    async def get_by_hash(self, key_hash: str) -> ApiKey | None: ...


class ProjectRuntimeRepository(Protocol):
    async def get(self, project_id: str) -> ProjectRuntime | None: ...
