"""Centralized structured logging (stage §4).

A single ``LoggingService`` gives every subsystem the same six levels
(TRACE / DEBUG / INFO / WARNING / ERROR / CRITICAL), a consistent **structured**
format, automatic **Trace ID** correlation and **masking** of sensitive fields.
It wraps the stdlib logging (configured elsewhere) — no external dependency and
no monitoring-system lock-in.
"""

from __future__ import annotations

import logging
from enum import IntEnum
from typing import Any

from app.observability.utils.masking import mask_value

# stdlib logging has no TRACE level — add one below DEBUG.
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


class LogLevel(IntEnum):
    TRACE = TRACE_LEVEL
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggingService:
    """A thin, structured facade over a named stdlib logger."""

    def __init__(self, name: str = "app") -> None:
        self._logger = logging.getLogger(name)

    def log(self, level: LogLevel, message: str, **fields: Any) -> None:
        safe = {key: mask_value(key, value) for key, value in fields.items()}
        self._logger.log(int(level), message, extra=safe)

    def trace(self, message: str, **fields: Any) -> None:
        self.log(LogLevel.TRACE, message, **fields)

    def debug(self, message: str, **fields: Any) -> None:
        self.log(LogLevel.DEBUG, message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self.log(LogLevel.INFO, message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self.log(LogLevel.WARNING, message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self.log(LogLevel.ERROR, message, **fields)

    def critical(self, message: str, **fields: Any) -> None:
        self.log(LogLevel.CRITICAL, message, **fields)
