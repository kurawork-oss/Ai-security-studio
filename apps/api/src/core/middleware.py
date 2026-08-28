"""Cross-cutting HTTP middleware and exception handlers.

- Assigns a ``requestId`` to every request (``X-Request-Id``) and binds it to
  the structlog context.
- Records latency and emits a single structured access log per request
  (metadata only — never the body).
- Maps :class:`AppError` and unexpected exceptions to the unified error
  envelope.
"""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .errors import AppError, ValidationError
from .logging import get_logger

log = get_logger("secureai.http")


def new_request_id() -> str:
    return "req_" + uuid.uuid4().hex


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-Id") or new_request_id()
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            log.info(
                "request",
                method=request.method,
                path=request.url.path,
                latency_ms=elapsed_ms,
            )
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-Id"] = request_id
        return response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        if exc.status_code >= 500:
            log.error("app_error", code=exc.code, message=exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict(request_id))

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        err = ValidationError("Request validation failed", details={"errors": exc.errors()})
        return JSONResponse(status_code=err.status_code, content=err.to_dict(request_id))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        log.error("unhandled_exception", error=str(exc), exc_info=True)
        err = AppError("Internal server error")
        return JSONResponse(status_code=err.status_code, content=err.to_dict(request_id))
