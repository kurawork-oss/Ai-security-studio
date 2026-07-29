"""Domain entities — the core business objects (persistence-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .value_objects import AnonymizeAction, KeyType


@dataclass
class Project:
    id: str
    name: str
    org_id: str | None = None


@dataclass
class ProtectRule:
    """Per-project configuration for a single PII entity type.

    Fully data-driven so rules (including custom regex / enterprise types) can
    be added without code changes.
    """

    entity_type: str
    enabled: bool = True
    action: AnonymizeAction = AnonymizeAction.MASK
    placeholder_format: str = "<{type}_{n}>"
    score_threshold: float = 0.4
    regex: str | None = None          # custom recognizer pattern
    replacement: str | None = None    # for AnonymizeAction.REPLACE
    priority: int = 100               # lower wins on overlap

    @staticmethod
    def default_for(entity_type: str) -> "ProtectRule":
        return ProtectRule(entity_type=entity_type)


@dataclass
class Provider:
    id: str
    project_id: str
    provider_type: str
    display_name: str = ""
    default_model: str | None = None
    base_url: str | None = None
    # Encrypted at rest via KeyProvider; decrypted only at request time.
    encrypted_key: bytes | None = None
    is_active: bool = True


@dataclass
class ApiKey:
    """A SecureAI-issued key. The raw key is never stored — only its hash."""

    id: str
    project_id: str
    key_type: KeyType
    key_prefix: str
    key_hash: str
    status: str = "active"
    rotated_from_id: str | None = None

    @property
    def is_active(self) -> bool:
        return self.status == "active"


@dataclass
class ProjectRuntime:
    """Everything the data plane needs to serve one project's requests."""

    project: Project
    rules: list[ProtectRule] = field(default_factory=list)
    providers: list[Provider] = field(default_factory=list)

    def enabled_rules(self) -> list[ProtectRule]:
        return [r for r in self.rules if r.enabled]

    def provider(self, provider_id: str | None) -> Provider | None:
        if provider_id:
            return next((p for p in self.providers if p.id == provider_id), None)
        return next((p for p in self.providers if p.is_active), None)
