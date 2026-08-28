from __future__ import annotations

from fastapi import APIRouter

from .routers import (
    analyze,
    batch,
    detect,
    extract,
    health,
    management,
    plugins,
    protect,
    stream,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(protect.router)
api_router.include_router(analyze.router)
api_router.include_router(stream.router)
api_router.include_router(batch.router)
api_router.include_router(detect.router)
api_router.include_router(extract.router)
api_router.include_router(plugins.router)
api_router.include_router(management.router)
