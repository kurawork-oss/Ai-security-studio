"""Unified error taxonomy and response shape.

Every error returned by the API has the same envelope::

    {"error": {"code": "...", "message": "...", "requestId": "...", "details": {...}}}

Domain/application code raises :class:`AppError` subclasses; the HTTP layer maps
them to this envelope in ``middleware.register_exception_handlers``.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for all expected application errors."""

    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self, request_id: str | None = None) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "requestId": request_id,
                "details": self.details,
            }
        }


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 400


class Unauthenticated(AppError):
    code = "UNAUTHENTICATED"
    status_code = 401


class Forbidden(AppError):
    code = "FORBIDDEN"
    status_code = 403


class NotFound(AppError):
    code = "NOT_FOUND"
    status_code = 404


class RateLimitExceeded(AppError):
    code = "RATE_LIMIT_EXCEEDED"
    status_code = 429


class AnonymizationFailed(AppError):
    """Raised when PII protection could not be completed.

    Critical for Analyze: on this error we MUST NOT forward text to the LLM
    (fail-closed).
    """

    code = "ANONYMIZATION_FAILED"
    status_code = 502


class ProviderError(AppError):
    code = "PROVIDER_ERROR"
    status_code = 502


class ProviderNotSupported(AppError):
    code = "PROVIDER_NOT_SUPPORTED"
    status_code = 400


class DbRequired(AppError):
    """Raised when a management endpoint is hit without Postgres configured."""

    code = "DB_REQUIRED"
    status_code = 501
