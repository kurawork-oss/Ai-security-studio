from __future__ import annotations

from fastapi import APIRouter, Request

from ...deps import get_container

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health(request: Request) -> dict:
    container = get_container(request)
    return {
        "status": "ok",
        "environment": container.settings.environment,
        "supportedProviders": container.registry.supported(),
    }
