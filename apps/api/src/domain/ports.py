"""Ports (interfaces) — the boundaries the application depends on.

Infrastructure provides implementations; the application layer depends only on
these Protocols. This keeps the PII engine, providers and persistence swappable
(Dependency Inversion).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from .entities import ApiKey, LogEntry, Project, ProjectRuntime, ProtectRule, Provider
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


# ── Control plane (management) repositories ──


class MembershipRepository(Protocol):
    async def org_ids_for_user(self, user_id: str) -> list[str]: ...
    async def default_org_for_user(self, user_id: str) -> str | None: ...


class ProjectRepository(Protocol):
    async def create(
        self, org_id: str, name: str, slug: str, description: str | None = None
    ) -> Project: ...
    async def list_by_orgs(self, org_ids: list[str]) -> list[Project]: ...
    async def get(self, project_id: str) -> Project | None: ...


class ProviderRepository(Protocol):
    async def create(
        self,
        project_id: str,
        provider_type: str,
        display_name: str,
        default_model: str | None,
        base_url: str | None,
    ) -> Provider: ...
    async def list_by_project(self, project_id: str) -> list[Provider]: ...
    async def get(self, provider_id: str) -> Provider | None: ...
    async def add_key(self, provider_id: str, encrypted_key: bytes, key_hint: str) -> None: ...


class ApiKeyAdminRepository(Protocol):
    async def create(
        self,
        project_id: str,
        key_type: str,
        name: str,
        key_prefix: str,
        key_hash: str,
        rotated_from_id: str | None = None,
    ) -> ApiKey: ...
    async def list_by_project(self, project_id: str) -> list[ApiKey]: ...
    async def get(self, key_id: str) -> ApiKey | None: ...
    async def revoke(self, key_id: str) -> None: ...


class ProtectRuleRepository(Protocol):
    async def create_defaults(self, project_id: str) -> None: ...
    async def list_by_project(self, project_id: str) -> list[ProtectRule]: ...
    async def upsert_many(self, project_id: str, rules: list[ProtectRule]) -> None: ...


class LogRepository(Protocol):
    async def write(
        self,
        *,
        project_id: str,
        endpoint: str,
        request_id: str | None,
        status_code: int,
        latency_ms: int,
        input_chars: int,
        entity_counts: dict[str, int],
        api_key_id: str | None = None,
        provider_id: str | None = None,
        token_usage: dict | None = None,
        error_code: str | None = None,
    ) -> None: ...
    async def list_by_project(self, project_id: str, limit: int = 50) -> list[LogEntry]: ...
