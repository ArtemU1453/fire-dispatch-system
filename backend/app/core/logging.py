"""Logging configuration.

A single ``configure_logging`` entry-point keeps logging setup DRY and in one
place. Supports both human-readable (local dev) and JSON (production) output
selected purely from configuration, so no code needs to change between
environments.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.config import Settings


class JsonFormatter(logging.Formatter):
    """Minimal structured JSON log formatter (no external dependency)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=UTC
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Attach any extra contextual fields.
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_ATTRS and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


# Attributes present on every LogRecord that should not be treated as "extra".
_RESERVED_LOG_ATTRS = set(
    logging.LogRecord(
        name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
    ).__dict__.keys()
) | {"message", "asctime"}


def configure_logging(settings: Settings) -> None:
    """Configure the root logger idempotently based on ``settings``."""
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)

    # Remove pre-existing handlers so re-configuration (e.g. tests) is safe.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(stream=sys.stdout)
    if settings.LOG_JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root.addHandler(handler)

    # Align popular third-party loggers with our configuration.
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).handlers = []
        logging.getLogger(noisy).propagate = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Thin wrapper to keep imports consistent."""
    return logging.getLogger(name)
