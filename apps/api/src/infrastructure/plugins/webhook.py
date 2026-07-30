"""Webhook delivery plugin — POST a (masked) result to a configured URL.

The poster is injectable so it can be unit-tested without real network I/O.
Only anonymized payloads are ever delivered.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import httpx

from ...core.errors import ValidationError
from ...domain.plugins import PluginManifest

Poster = Callable[[str, dict], Awaitable[None]]


async def _httpx_post(url: str, payload: dict) -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(url, json=payload)


class WebhookPlugin:
    manifest = PluginManifest(
        key="webhook",
        category="delivery",
        description="POST a masked result to a configured URL",
    )

    def __init__(self, poster: Poster | None = None) -> None:
        self._poster = poster or _httpx_post

    async def deliver(self, payload: dict, target: dict) -> None:
        url = target.get("url")
        if not url:
            raise ValidationError("Webhook target requires a 'url'")
        await self._poster(url, payload)
