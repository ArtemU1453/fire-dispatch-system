"""Domain / application exception hierarchy and FastAPI handlers.

Defining a small, explicit exception hierarchy keeps error handling consistent
(DRY) and lets the API layer translate domain errors into HTTP responses in one
place, without leaking implementation details into services.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base class for all application-level errors.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code the API layer should return.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource not found"


class ConflictError(AppError):
    """Raised when an operation conflicts with current state."""

    status_code = status.HTTP_409_CONFLICT
    message = "Conflict"


class ValidationError(AppError):
    """Raised for domain validation failures (not request schema errors)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "Validation error"


def register_exception_handlers(app: FastAPI) -> None:
    """Attach application exception handlers to ``app``."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        logger.warning("Application error: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
