"""Control-plane (management) use cases.

Orchestrates the management repositories with tenancy checks. Every operation
verifies the acting user has access to the target project's organization.
"""

from __future__ import annotations

import re
import secrets

from ...core.auth import AuthUser
from ...core.errors import Forbidden, NotFound, ValidationError
from ...core.security import generate_api_key
from ...domain.entities import ApiKey, LogEntry, Project, ProtectRule, Provider
from ...domain.value_objects import KeyType
from ...infrastructure.crypto.keyprovider import AesGcmCipher
from ..export import TARGET_META, ExportArtifact, ExportContext, render


def slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"
    return f"{base[:40]}-{secrets.token_hex(3)}"


class ManagementService:
    def __init__(self, uow, cipher: AesGcmCipher) -> None:
        self.uow = uow
        self.cipher = cipher

    async def _project_for(self, user: AuthUser, project_id: str) -> Project:
        org_ids = await self.uow.memberships.org_ids_for_user(user.id)
        project = await self.uow.projects.get(project_id)
        if project is None:
            raise NotFound("Project not found")
        if project.org_id not in org_ids:
            raise Forbidden("You do not have access to this project")
        return project

    # ── Projects ──
    async def create_project(self, user: AuthUser, name: str) -> Project:
        org_id = await self.uow.memberships.default_org_for_user(user.id)
        if not org_id:
            raise ValidationError("User has no organization")
        project = await self.uow.projects.create(org_id, name, slugify(name))
        await self.uow.rules.create_defaults(project.id)
        await self.uow.commit()
        return project

    async def list_projects(self, user: AuthUser) -> list[Project]:
        org_ids = await self.uow.memberships.org_ids_for_user(user.id)
        return await self.uow.projects.list_by_orgs(org_ids)

    async def get_project(self, user: AuthUser, project_id: str) -> Project:
        return await self._project_for(user, project_id)

    # ── Providers ──
    async def create_provider(
        self,
        user: AuthUser,
        project_id: str,
        *,
        provider_type: str,
        display_name: str,
        default_model: str | None,
        base_url: str | None,
        api_key: str | None,
    ) -> Provider:
        await self._project_for(user, project_id)
        provider = await self.uow.providers.create(
            project_id, provider_type, display_name, default_model, base_url
        )
        if api_key:
            await self.uow.providers.add_key(
                provider.id, self.cipher.encrypt(api_key), api_key[-4:]
            )
        await self.uow.commit()
        return provider

    async def list_providers(self, user: AuthUser, project_id: str) -> list[Provider]:
        await self._project_for(user, project_id)
        return await self.uow.providers.list_by_project(project_id)

    # ── API keys (Protect / Analyze, rotatable) ──
    async def issue_api_key(
        self, user: AuthUser, project_id: str, key_type: KeyType, name: str
    ) -> tuple[ApiKey, str]:
        await self._project_for(user, project_id)
        raw, prefix, key_hash = generate_api_key(key_type)
        key = await self.uow.api_key_admin.create(
            project_id, key_type.value, name, prefix, key_hash
        )
        await self.uow.commit()
        return key, raw

    async def list_api_keys(self, user: AuthUser, project_id: str) -> list[ApiKey]:
        await self._project_for(user, project_id)
        return await self.uow.api_key_admin.list_by_project(project_id)

    async def rotate_api_key(self, user: AuthUser, key_id: str) -> tuple[ApiKey, str]:
        key = await self.uow.api_key_admin.get(key_id)
        if key is None:
            raise NotFound("API key not found")
        await self._project_for(user, key.project_id)
        raw, prefix, key_hash = generate_api_key(KeyType(key.key_type))
        new = await self.uow.api_key_admin.create(
            key.project_id, KeyType(key.key_type).value, key.name, prefix, key_hash,
            rotated_from_id=key.id,
        )
        await self.uow.api_key_admin.revoke(key.id)
        await self.uow.commit()
        return new, raw

    async def revoke_api_key(self, user: AuthUser, key_id: str) -> None:
        key = await self.uow.api_key_admin.get(key_id)
        if key is None:
            raise NotFound("API key not found")
        await self._project_for(user, key.project_id)
        await self.uow.api_key_admin.revoke(key.id)
        await self.uow.commit()

    # ── Protect rules ──
    async def list_rules(self, user: AuthUser, project_id: str) -> list[ProtectRule]:
        await self._project_for(user, project_id)
        return await self.uow.rules.list_by_project(project_id)

    async def update_rules(
        self, user: AuthUser, project_id: str, rules: list[ProtectRule]
    ) -> list[ProtectRule]:
        await self._project_for(user, project_id)
        await self.uow.rules.upsert_many(project_id, rules)
        await self.uow.commit()
        return await self.uow.rules.list_by_project(project_id)

    # ── Logs & analytics ──
    async def list_logs(self, user: AuthUser, project_id: str, limit: int = 50) -> list[LogEntry]:
        await self._project_for(user, project_id)
        return await self.uow.logs.list_by_project(project_id, limit)

    async def analytics_summary(self, user: AuthUser, project_id: str) -> dict:
        await self._project_for(user, project_id)
        logs = await self.uow.logs.list_by_project(project_id, limit=1000)
        by_endpoint: dict[str, int] = {}
        entity_counts: dict[str, int] = {}
        protect_count = 0
        for entry in logs:
            by_endpoint[entry.endpoint] = by_endpoint.get(entry.endpoint, 0) + 1
            for code, n in (entry.entity_counts or {}).items():
                entity_counts[code] = entity_counts.get(code, 0) + n
                protect_count += n
        total = len(logs)
        avg_latency = int(sum(e.latency_ms or 0 for e in logs) / total) if total else 0
        return {
            "requests": total,
            "byEndpoint": by_endpoint,
            "protectCount": protect_count,
            "entityCounts": entity_counts,
            "avgLatencyMs": avg_latency,
        }

    # ── Export (AI coding tool prompts) ──
    def export_targets(self) -> list[dict]:
        return TARGET_META

    async def export(
        self,
        user: AuthUser,
        project_id: str,
        *,
        target_id: str,
        language: str,
        pattern: str,
        api_base_url: str,
    ) -> ExportArtifact:
        await self._project_for(user, project_id)
        rules = await self.uow.rules.list_by_project(project_id)
        enabled = [r.entity_type for r in rules if r.enabled]
        provider_type = None
        if pattern == "analyze":
            providers = await self.uow.providers.list_by_project(project_id)
            active = next((p for p in providers if p.is_active), None)
            provider_type = active.provider_type if active else None
        ctx = ExportContext(
            pattern=pattern,
            language=language,
            api_base_url=api_base_url,
            enabled_rules=enabled,
            key_env_var="SECUREAI_PROTECT_KEY" if pattern == "protect" else "SECUREAI_ANALYZE_KEY",
            provider_type=provider_type,
        )
        return render(target_id, ctx)
