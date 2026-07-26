"""Masking of sensitive data in logs, metrics and traces (stage §10).

Logs and metrics must never contain passwords, secrets, access keys, personal
data that need not be stored, or full conversation texts. These helpers scrub
such fields from arbitrary structured payloads before they are recorded.
"""

from __future__ import annotations

from typing import Any

MASK = "***"

# Keys whose value is replaced wholesale (case-insensitive substring match).
_SENSITIVE_KEYS = (
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "access_key", "private_key", "authorization", "auth", "credential",
    "hashed_password", "session_token", "secret_ref",
)

# Keys whose (possibly long / personal) text is truncated, not fully masked.
_TRUNCATE_KEYS = ("text", "text_content", "transcript", "prompt", "body", "message")
_TRUNCATE_AT = 120


def _is_sensitive(key: str) -> bool:
    low = key.lower()
    return any(s in low for s in _SENSITIVE_KEYS)


def _should_truncate(key: str) -> bool:
    return key.lower() in _TRUNCATE_KEYS


def mask_value(key: str, value: Any) -> Any:
    if _is_sensitive(key):
        return MASK
    if _should_truncate(key) and isinstance(value, str) and len(value) > _TRUNCATE_AT:
        return value[:_TRUNCATE_AT] + "…"
    return mask_data(value)


def mask_data(value: Any) -> Any:
    """Recursively mask sensitive keys in dicts / lists."""
    if isinstance(value, dict):
        return {k: mask_value(k, v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [mask_data(v) for v in value]
    return value
