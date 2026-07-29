"""In-memory repositories + dev seed.

Lets the data plane (Protect / Analyze / Detect) run and be tested without a
live Supabase. Production swaps these for SQLAlchemy/Postgres-backed repos
implementing the same ports.
"""

from __future__ import annotations

from ...core.security import hash_api_key, key_prefix
from ...domain.entities import ApiKey, Project, ProjectRuntime, ProtectRule, Provider
from ...domain.value_objects import BuiltinEntity, KeyType
from ..crypto.keyprovider import AesGcmCipher


def default_rules() -> list[ProtectRule]:
    """All 12 built-in entity types enabled with MASK (matches seed catalog)."""
    return [ProtectRule(entity_type=e.value, enabled=True) for e in BuiltinEntity]


class InMemoryApiKeyRepository:
    def __init__(self, keys: list[ApiKey] | None = None) -> None:
        self._by_hash: dict[str, ApiKey] = {k.key_hash: k for k in (keys or [])}

    def add(self, key: ApiKey) -> None:
        self._by_hash[key.key_hash] = key

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return self._by_hash.get(key_hash)


class InMemoryProjectRuntimeRepository:
    def __init__(self, runtimes: list[ProjectRuntime] | None = None) -> None:
        self._by_id: dict[str, ProjectRuntime] = {
            r.project.id: r for r in (runtimes or [])
        }

    def add(self, runtime: ProjectRuntime) -> None:
        self._by_id[runtime.project.id] = runtime

    async def get(self, project_id: str) -> ProjectRuntime | None:
        return self._by_id.get(project_id)


def build_dev_seed(
    *,
    cipher: AesGcmCipher,
    protect_key: str,
    analyze_key: str,
    provider_type: str = "echo",
    gemini_key: str = "",
    gemini_model: str = "gemini-1.5-flash",
) -> tuple[InMemoryApiKeyRepository, InMemoryProjectRuntimeRepository]:
    project = Project(id="prj_dev", name="Dev Project", org_id="org_dev")

    encrypted = None
    if provider_type == "gemini" and gemini_key:
        encrypted = cipher.encrypt(gemini_key)
    provider = Provider(
        id="prov_dev",
        project_id=project.id,
        provider_type=provider_type,
        display_name=f"Dev {provider_type}",
        default_model=gemini_model if provider_type == "gemini" else None,
        encrypted_key=encrypted,
    )

    runtime = ProjectRuntime(
        project=project, rules=default_rules(), providers=[provider]
    )

    keys = [
        ApiKey(
            id="key_protect_dev",
            project_id=project.id,
            key_type=KeyType.PROTECT,
            key_prefix=key_prefix(protect_key),
            key_hash=hash_api_key(protect_key),
        ),
        ApiKey(
            id="key_analyze_dev",
            project_id=project.id,
            key_type=KeyType.ANALYZE,
            key_prefix=key_prefix(analyze_key),
            key_hash=hash_api_key(analyze_key),
        ),
    ]
    return InMemoryApiKeyRepository(keys), InMemoryProjectRuntimeRepository([runtime])
