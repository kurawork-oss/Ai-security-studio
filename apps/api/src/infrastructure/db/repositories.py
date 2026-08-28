"""Postgres repository implementations (SQLAlchemy async).

Each repository is bound to a request-scoped AsyncSession. Domain entities are
returned to the application layer; ORM models never leak past this boundary.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities import (
    ApiKey,
    LogEntry,
    Project,
    ProjectRuntime,
    ProtectRule,
    Provider,
)
from ...domain.value_objects import AnonymizeAction, BuiltinEntity, KeyType
from . import models as m


def _uid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


# ── mappers ──
def _to_project(row: m.Project) -> Project:
    return Project(
        id=str(row.id),
        name=row.name,
        org_id=str(row.org_id),
        slug=row.slug,
        description=row.description,
        environment=row.environment,
        status=row.status,
        created_at=row.created_at,
    )


def _to_rule(row: m.ProtectRuleModel) -> ProtectRule:
    cfg = row.config or {}
    return ProtectRule(
        entity_type=row.entity_type,
        enabled=row.enabled,
        action=AnonymizeAction(row.action),
        placeholder_format=row.placeholder_format,
        score_threshold=float(cfg.get("score", 0.4)),
        regex=cfg.get("regex"),
        replacement=cfg.get("replacement"),
        priority=row.priority,
    )


def _to_provider(row: m.ProviderModel, *, include_key: bool = False) -> Provider:
    encrypted = None
    if include_key:
        active = next((k for k in row.keys if k.status == "active"), None)
        encrypted = bytes(active.encrypted_key) if active else None
    return Provider(
        id=str(row.id),
        project_id=str(row.project_id),
        provider_type=row.provider_type,
        display_name=row.display_name,
        default_model=row.default_model,
        base_url=row.base_url,
        encrypted_key=encrypted,
        is_active=row.is_active,
    )


def _to_api_key(row: m.ApiKeyModel) -> ApiKey:
    return ApiKey(
        id=str(row.id),
        project_id=str(row.project_id),
        key_type=KeyType(row.key_type),
        key_prefix=row.key_prefix,
        key_hash=row.key_hash,
        status=row.status,
        rotated_from_id=str(row.rotated_from_id) if row.rotated_from_id else None,
        name=row.name,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
        revoked_at=row.revoked_at,
    )


class PgApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        row = (
            await self._s.execute(select(m.ApiKeyModel).where(m.ApiKeyModel.key_hash == key_hash))
        ).scalar_one_or_none()
        return _to_api_key(row) if row else None


class PgProjectRuntimeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, project_id: str) -> ProjectRuntime | None:
        row = (
            await self._s.execute(select(m.Project).where(m.Project.id == _uid(project_id)))
        ).scalar_one_or_none()
        if row is None:
            return None
        rules = [_to_rule(r) for r in row.rules]
        providers = [_to_provider(p, include_key=True) for p in row.providers if p.is_active]
        return ProjectRuntime(project=_to_project(row), rules=rules, providers=providers)


class PgMembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def org_ids_for_user(self, user_id: str) -> list[str]:
        rows = (
            await self._s.execute(
                select(m.Membership.org_id).where(m.Membership.user_id == _uid(user_id))
            )
        ).scalars().all()
        return [str(o) for o in rows]

    async def default_org_for_user(self, user_id: str) -> str | None:
        row = (
            await self._s.execute(
                select(m.Membership.org_id)
                .where(m.Membership.user_id == _uid(user_id))
                .order_by(m.Membership.created_at.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        return str(row) if row else None


class PgProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self, org_id: str, name: str, slug: str, description: str | None = None
    ) -> Project:
        row = m.Project(org_id=_uid(org_id), name=name, slug=slug, description=description)
        self._s.add(row)
        await self._s.flush()
        return _to_project(row)

    async def list_by_orgs(self, org_ids: list[str]) -> list[Project]:
        if not org_ids:
            return []
        rows = (
            await self._s.execute(
                select(m.Project)
                .where(m.Project.org_id.in_([_uid(o) for o in org_ids]))
                .order_by(m.Project.created_at.desc())
            )
        ).scalars().all()
        return [_to_project(r) for r in rows]

    async def get(self, project_id: str) -> Project | None:
        row = (
            await self._s.execute(select(m.Project).where(m.Project.id == _uid(project_id)))
        ).scalar_one_or_none()
        return _to_project(row) if row else None


class PgProviderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        project_id: str,
        provider_type: str,
        display_name: str,
        default_model: str | None,
        base_url: str | None,
    ) -> Provider:
        row = m.ProviderModel(
            project_id=_uid(project_id),
            provider_type=provider_type,
            display_name=display_name,
            default_model=default_model,
            base_url=base_url,
        )
        self._s.add(row)
        await self._s.flush()
        await self._s.refresh(row, ["keys"])
        return _to_provider(row)

    async def list_by_project(self, project_id: str) -> list[Provider]:
        rows = (
            await self._s.execute(
                select(m.ProviderModel).where(m.ProviderModel.project_id == _uid(project_id))
            )
        ).scalars().all()
        return [_to_provider(r) for r in rows]

    async def get(self, provider_id: str) -> Provider | None:
        row = (
            await self._s.execute(
                select(m.ProviderModel).where(m.ProviderModel.id == _uid(provider_id))
            )
        ).scalar_one_or_none()
        return _to_provider(row) if row else None

    async def add_key(self, provider_id: str, encrypted_key: bytes, key_hint: str) -> None:
        self._s.add(
            m.ProviderKeyModel(
                provider_id=_uid(provider_id), encrypted_key=encrypted_key, key_hint=key_hint
            )
        )
        await self._s.flush()


class PgApiKeyAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        project_id: str,
        key_type: str,
        name: str,
        key_prefix: str,
        key_hash: str,
        rotated_from_id: str | None = None,
    ) -> ApiKey:
        row = m.ApiKeyModel(
            project_id=_uid(project_id),
            key_type=key_type,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            rotated_from_id=_uid(rotated_from_id) if rotated_from_id else None,
        )
        self._s.add(row)
        await self._s.flush()
        return _to_api_key(row)

    async def list_by_project(self, project_id: str) -> list[ApiKey]:
        rows = (
            await self._s.execute(
                select(m.ApiKeyModel)
                .where(m.ApiKeyModel.project_id == _uid(project_id))
                .order_by(m.ApiKeyModel.created_at.desc())
            )
        ).scalars().all()
        return [_to_api_key(r) for r in rows]

    async def get(self, key_id: str) -> ApiKey | None:
        row = (
            await self._s.execute(select(m.ApiKeyModel).where(m.ApiKeyModel.id == _uid(key_id)))
        ).scalar_one_or_none()
        return _to_api_key(row) if row else None

    async def revoke(self, key_id: str) -> None:
        from datetime import datetime, timezone

        row = (
            await self._s.execute(select(m.ApiKeyModel).where(m.ApiKeyModel.id == _uid(key_id)))
        ).scalar_one_or_none()
        if row is not None:
            row.status = "revoked"
            row.revoked_at = datetime.now(timezone.utc)
            await self._s.flush()


class PgProtectRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create_defaults(self, project_id: str) -> None:
        for entity in BuiltinEntity:
            self._s.add(
                m.ProtectRuleModel(project_id=_uid(project_id), entity_type=str(entity))
            )
        await self._s.flush()

    async def list_by_project(self, project_id: str) -> list[ProtectRule]:
        rows = (
            await self._s.execute(
                select(m.ProtectRuleModel).where(
                    m.ProtectRuleModel.project_id == _uid(project_id)
                )
            )
        ).scalars().all()
        return [_to_rule(r) for r in rows]

    async def upsert_many(self, project_id: str, rules: list[ProtectRule]) -> None:
        existing = {
            r.entity_type: r
            for r in (
                await self._s.execute(
                    select(m.ProtectRuleModel).where(
                        m.ProtectRuleModel.project_id == _uid(project_id)
                    )
                )
            ).scalars().all()
        }
        for rule in rules:
            config = {"score": rule.score_threshold}
            if rule.regex:
                config["regex"] = rule.regex
            if rule.replacement:
                config["replacement"] = rule.replacement
            row = existing.get(rule.entity_type)
            if row is None:
                self._s.add(
                    m.ProtectRuleModel(
                        project_id=_uid(project_id),
                        entity_type=rule.entity_type,
                        enabled=rule.enabled,
                        action=str(rule.action),
                        placeholder_format=rule.placeholder_format,
                        config=config,
                        priority=rule.priority,
                    )
                )
            else:
                row.enabled = rule.enabled
                row.action = str(rule.action)
                row.placeholder_format = rule.placeholder_format
                row.config = config
                row.priority = rule.priority
        await self._s.flush()


class PgLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

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
    ) -> None:
        self._s.add(
            m.LogModel(
                project_id=_uid(project_id),
                api_key_id=_uid(api_key_id) if api_key_id else None,
                provider_id=_uid(provider_id) if provider_id else None,
                endpoint=endpoint,
                request_id=request_id,
                status_code=status_code,
                latency_ms=latency_ms,
                input_chars=input_chars,
                entity_counts=entity_counts,
                token_usage=token_usage,
                error_code=error_code,
            )
        )
        await self._s.flush()

    async def list_by_project(self, project_id: str, limit: int = 50) -> list[LogEntry]:
        rows = (
            await self._s.execute(
                select(m.LogModel)
                .where(m.LogModel.project_id == _uid(project_id))
                .order_by(m.LogModel.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [
            LogEntry(
                id=str(r.id),
                endpoint=r.endpoint,
                status_code=r.status_code,
                latency_ms=r.latency_ms,
                input_chars=r.input_chars,
                entity_counts=r.entity_counts or {},
                error_code=r.error_code,
                created_at=r.created_at,
            )
            for r in rows
        ]
