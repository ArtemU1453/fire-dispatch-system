"""Administration-specific exceptions.

Subclasses of the shared ``AppError`` so the existing global exception handler
translates them to HTTP responses automatically — no change to the core module.
"""

from __future__ import annotations

from fastapi import status

from app.core.exceptions import AppError


class AuthorizationError(AppError):
    """Raised when a user lacks a required permission."""

    status_code = status.HTTP_403_FORBIDDEN
    message = "Forbidden"
