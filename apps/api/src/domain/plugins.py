"""Plugin contracts — the extension points that keep the core closed to change.

Plugins fall into categories (see docs/architecture/14-plugin-architecture.md):
- extractor    : non-text input -> text (fed into the PII engine)
- augmentation : add context around detection/anonymization
- delivery     : how results are transported (webhook / streaming / batch)
- protocol     : expose the core over an external protocol (e.g. MCP)

Concrete plugins live in ``infrastructure/plugins``. Content extracted by an
extractor is ALWAYS passed through anonymization before leaving the system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class PluginManifest:
    key: str
    category: str  # extractor | augmentation | delivery | protocol
    version: str = "0.1.0"
    description: str = ""
    # extractor-only: the content types this plugin can turn into text
    content_types: tuple[str, ...] = field(default_factory=tuple)
    # whether a working implementation ships now, or it is a declared stub
    available: bool = True

    def public_dict(self) -> dict:
        return {
            "key": self.key,
            "category": self.category,
            "version": self.version,
            "description": self.description,
            "contentTypes": list(self.content_types),
            "available": self.available,
        }


@runtime_checkable
class ExtractorPlugin(Protocol):
    manifest: PluginManifest

    def supports(self, content_type: str) -> bool: ...

    def extract(self, content: bytes, content_type: str) -> str: ...


@runtime_checkable
class DeliveryPlugin(Protocol):
    manifest: PluginManifest

    async def deliver(self, payload: dict, target: dict) -> None: ...
