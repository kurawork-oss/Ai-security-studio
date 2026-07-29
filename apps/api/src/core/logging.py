"""Structured logging (structlog).

Logs are JSON in production and human-friendly in development. Log events MUST
NOT contain raw text or raw PII — only metadata (request_id, endpoint, counts).
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str = "info", *, json: bool = True) -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)

    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    processors.append(
        structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "secureai") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
