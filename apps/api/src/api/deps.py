"""Dependency injection: composition root, request-scoped Unit of Work, auth.

The container is built once at startup. Persistence is Postgres when
``SECUREAI_DATABASE_URL`` is set, otherwise the in-memory dev seed. A Unit of
Work is created per request and shared by the auth dependency and the router.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, replace

from fastapi import Depends, Header, Request

from ..application.analyze import AnalyzeTextUseCase
from ..application.detect import DetectUseCase
from ..application.protect import ProtectTextUseCase
from ..core.auth import AuthUser, JwtVerifier
from ..core.config import Settings
from ..core.errors import Forbidden, NotFound, Unauthenticated, ValidationError
from ..core.security import hash_api_key
from ..domain.entities import ApiKey, ProjectRuntime, ProtectRule
from ..domain.services import Anonymizer
from ..domain.value_objects import KeyType
from ..infrastructure.crypto.keyprovider import build_cipher
from ..infrastructure.db.session import create_engine, create_sessionmaker
from ..infrastructure.db.uow import InMemoryUnitOfWork, PgUnitOfWork
from ..infrastructure.pii.regex_detector import RegexPiiDetector
from ..infrastructure.providers.echo import EchoAdapter
from ..infrastructure.providers.gemini import GeminiAdapter
from ..infrastructure.providers.registry import ProviderRegistry
from ..infrastructure.repositories.memory import build_dev_seed


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cipher = build_cipher(settings.kms_provider, settings.encryption_kek)
        self.jwt = JwtVerifier(settings)

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
        self.analyze_uc = AnalyzeTextUseCase(self.protect_uc, registry, self.cipher)

        self.sessionmaker = None
        self._engine = None
        self._seed = None
        if settings.use_postgres:
            self._engine = create_engine(settings.database_url)  # type: ignore[arg-type]
            self.sessionmaker = create_sessionmaker(self._engine)
        else:
            self._seed = build_dev_seed(
                cipher=self.cipher,
                protect_key=settings.dev_protect_key,
                analyze_key=settings.dev_analyze_key,
                provider_type=settings.dev_provider_type,
                gemini_key=settings.dev_gemini_key,
                gemini_model=settings.gemini_default_model,
            )

    async def aclose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()


def get_container(request: Request) -> Container:
    return request.app.state.container


async def get_uow(request: Request) -> AsyncIterator[object]:
    """Request-scoped Unit of Work (cached by FastAPI within a request)."""
    container = get_container(request)
    if container.sessionmaker is None:
        api_key_repo, runtime_repo = container._seed  # type: ignore[misc]
        yield InMemoryUnitOfWork(api_key_repo, runtime_repo)
        return
    async with container.sessionmaker() as session:
        uow = PgUnitOfWork(session)
        try:
            yield uow
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Data plane auth (API key) ──
@dataclass(frozen=True)
class AuthContext:
    key: ApiKey
    runtime: ProjectRuntime


def _extract_bearer(authorization: str | None, x_api_key: str | None) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    if x_api_key:
        return x_api_key.strip()
    raise Unauthenticated("Missing API key")


def require_key(expected: KeyType):
    async def dependency(
        uow=Depends(get_uow),
        authorization: str | None = Header(default=None),
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> AuthContext:
        raw = _extract_bearer(authorization, x_api_key)
        key = await uow.api_keys.get_by_hash(hash_api_key(raw))
        if key is None or not key.is_active:
            raise Unauthenticated("Invalid or revoked API key")
        if key.key_type != expected:
            raise Forbidden(
                f"This endpoint requires a '{expected.value}' key",
                details={"provided": key.key_type.value, "required": expected.value},
            )
        runtime = await uow.runtime.get(key.project_id)
        if runtime is None:
            raise NotFound("Project runtime not found")
        return AuthContext(key=key, runtime=runtime)

    return dependency


# ── Control plane auth (Supabase JWT) ──
async def require_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise Unauthenticated("Missing bearer token")
    token = authorization[7:].strip()
    return get_container(request).jwt.verify(token)


def guard_text_size(text: str, settings: Settings) -> None:
    if len(text.encode("utf-8")) > settings.api_text_max_bytes:
        raise ValidationError(
            "Input text exceeds the maximum allowed size",
            details={"maxBytes": settings.api_text_max_bytes},
        )


def effective_rules(
    runtime: ProjectRuntime, overrides: dict[str, bool] | None
) -> list[ProtectRule]:
    rules = {r.entity_type: r for r in runtime.rules}
    if overrides:
        for entity_type, enabled in overrides.items():
            if entity_type in rules:
                rules[entity_type] = replace(rules[entity_type], enabled=enabled)
            else:
                rules[entity_type] = ProtectRule(entity_type=entity_type, enabled=enabled)
    return list(rules.values())
