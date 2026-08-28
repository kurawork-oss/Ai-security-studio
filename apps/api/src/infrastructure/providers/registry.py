"""Provider registry — resolves a provider_type to its adapter (Strategy).

Adding a new LLM provider means implementing ``ProviderAdapter`` and calling
``register()`` — no existing code changes (Open/Closed Principle).
"""

from __future__ import annotations

from ...core.errors import ProviderNotSupported
from ...domain.ports import ProviderAdapter


class ProviderRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, ProviderAdapter] = {}

    def register(self, adapter: ProviderAdapter) -> None:
        self._adapters[adapter.provider_type] = adapter

    def get(self, provider_type: str) -> ProviderAdapter:
        try:
            return self._adapters[provider_type]
        except KeyError:
            raise ProviderNotSupported(
                f"Provider '{provider_type}' is not supported",
                details={"supported": sorted(self._adapters)},
            ) from None

    def supported(self) -> list[str]:
        return sorted(self._adapters)
