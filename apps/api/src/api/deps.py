"""Dependency injection: composition root + request-scoped auth.

The container wires concrete infrastructure into the application use cases and
is built once at startup (stored on ``app.state``). Routers depend on ports via
the container, never on concrete classes directly.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from fastapi import Header, Request

from ..application.analyze import AnalyzeTextUseCase
from ..application.detect import DetectUseCase
from ..application.protect import ProtectTextUseCase
from ..core.config import Settings
from ..core.errors import Forbidden, NotFound, Unauthenticated, ValidationError
from ..core.security import hash_api_key
from ..domain.entities import ApiKey, ProjectRuntime, ProtectRule
from ..domain.services import Anonymizer
from ..domain.value_objects import KeyType
from ..infrastructure.crypto.keyprovider import build_cipher
from ..infrastructure.pii.regex_detector import RegexPiiDetector
from ..infrastructure.providers.echo import EchoAdapter
from ..infrastructure.providers.gemini import GeminiAdapter
from ..infrastructure.providers.registry import ProviderRegistry
from ..infrastructure.repositories.memory import (
    InMemoryApiKeyRepository,
    InMemoryProjectRuntimeRepository,
    build_dev_seed,
)


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        cipher = build_cipher(settings.kms_provider, settings.encryption_kek)
        self.cipher = cipher

        detector = RegexPiiDetector()
        anonymizer = Anonymizer()

        registry = ProviderRegistry()
        registry.register(EchoAdapter())
        registry.register(
            GeminiAdapter(settings.gemini_api_base, settings.gemini_default_model)
        )
        self.registry = registry

        self.protect_uc = ProtectTextUseCase(detector, anonymizer)
        self.detect_uc = DetectUseCase(detector)
        self.analyze_uc = AnalyzeTextUseCase(self.protect_uc, registry, cipher)

        if settings.dev_seed:
            self.api_key_repo, self.runtime_repo = build_dev_seed(
                cipher=cipher,
                protect_key=settings.dev_protect_key,
                analyze_key=settings.dev_analyze_key,
                provider_type=settings.dev_provider_type,
                gemini_key=settings.dev_gemini_key,
                gemini_model=settings.gemini_default_model,
            )
        else:
            self.api_key_repo = InMemoryApiKeyRepository()
            self.runtime_repo = InMemoryProjectRuntimeRepository()


def get_container(request: Request) -> Container:
    return request.app.state.container


@dataclass(frozen=True)
class AuthContext:
    key: ApiKey
    runtime: ProjectRuntime


def _extract_key(authorization: str | None, x_api_key: str | None) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    if x_api_key:
        return x_api_key.strip()
    raise Unauthenticated("Missing API key")


def require_key(expected: KeyType):
    """Build a dependency that authenticates a request and enforces key type."""

    async def dependency(
        request: Request,
        authorization: str | None = Header(default=None),
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> AuthContext:
        raw = _extract_key(authorization, x_api_key)
        container = get_container(request)
        key = await container.api_key_repo.get_by_hash(hash_api_key(raw))
        if key is None or not key.is_active:
            raise Unauthenticated("Invalid or revoked API key")
        if key.key_type != expected:
            raise Forbidden(
                f"This endpoint requires a '{expected.value}' key",
                details={"provided": key.key_type.value, "required": expected.value},
            )
        runtime = await container.runtime_repo.get(key.project_id)
        if runtime is None:
            raise NotFound("Project runtime not found")
        return AuthContext(key=key, runtime=runtime)

    return dependency


def guard_text_size(text: str, settings: Settings) -> None:
    if len(text.encode("utf-8")) > settings.api_text_max_bytes:
        raise ValidationError(
            "Input text exceeds the maximum allowed size",
            details={"maxBytes": settings.api_text_max_bytes},
        )


def effective_rules(
    runtime: ProjectRuntime, overrides: dict[str, bool] | None
) -> list[ProtectRule]:
    """Apply per-request rule toggles (Playground) on top of stored rules."""
    rules = {r.entity_type: r for r in runtime.rules}
    if overrides:
        for entity_type, enabled in overrides.items():
            if entity_type in rules:
                rules[entity_type] = replace(rules[entity_type], enabled=enabled)
            else:
                rules[entity_type] = ProtectRule(entity_type=entity_type, enabled=enabled)
    return list(rules.values())
