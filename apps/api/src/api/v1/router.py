from __future__ import annotations

from fastapi import APIRouter

from .routers import analyze, detect, health, management, protect

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(protect.router)
api_router.include_router(analyze.router)
api_router.include_router(detect.router)
api_router.include_router(management.router)
