"""SecureAI Studio API — application entrypoint.

Run (from apps/api): ``uvicorn src.main:app --reload``
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.deps import Container
from .api.v1.router import api_router
from .core.config import get_settings
from .core.logging import configure_logging
from .core.middleware import RequestContextMiddleware, register_exception_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, json=settings.is_production)

    app = FastAPI(
        title="SecureAI Studio API",
        version="0.1.0",
        description="PII protection layer — Protect / Analyze / Detect",
    )
    app.state.container = Container(settings)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    app.include_router(api_router, prefix="/v1")

    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {
            "name": "SecureAI Studio API",
            "tagline": "AI へ送る前に、必ず SecureAI を通す",
            "docs": "/docs",
        }

    return app


app = create_app()
