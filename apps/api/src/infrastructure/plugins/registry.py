"""Plugin registry — discovery + lookup of registered plugins."""

from __future__ import annotations

from ...domain.plugins import ExtractorPlugin, PluginManifest


class PluginRegistry:
    def __init__(self) -> None:
        self._extractors: list[ExtractorPlugin] = []
        self._manifests: list[PluginManifest] = []

    def register_extractor(self, plugin: ExtractorPlugin) -> None:
        self._extractors.append(plugin)
        self._manifests.append(plugin.manifest)

    def register_manifest(self, manifest: PluginManifest) -> None:
        """Declare a plugin that ships as a stub (e.g. PDF/OCR/MCP/RAG)."""
        self._manifests.append(manifest)

    def extractor_for(self, content_type: str) -> ExtractorPlugin | None:
        return next((e for e in self._extractors if e.supports(content_type)), None)

    def manifests(self) -> list[PluginManifest]:
        return list(self._manifests)
