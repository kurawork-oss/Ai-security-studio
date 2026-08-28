"""Extract use case — turn uploaded content into text via an extractor plugin."""

from __future__ import annotations

from ..core.errors import ValidationError


class ExtractTextUseCase:
    def __init__(self, registry) -> None:
        self._registry = registry

    def execute(self, content: bytes, content_type: str) -> str:
        plugin = self._registry.extractor_for(content_type)
        if plugin is None:
            available = [
                ct for m in self._registry.manifests() if m.available for ct in m.content_types
            ]
            raise ValidationError(
                f"No available extractor for content type '{content_type}'",
                details={"supportedContentTypes": available},
            )
        return plugin.extract(content, content_type)
