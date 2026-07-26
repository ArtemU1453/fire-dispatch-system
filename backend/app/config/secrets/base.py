"""Secrets-provider abstraction (Stage 16 §2).

The application must never read secrets — database passwords, API keys, access
tokens, TLS certificates, encryption keys — from the repository or from
hard-coded literals. Instead it resolves them at runtime through a
:class:`SecretsProvider`, so the *same* code runs against environment variables
in development, mounted secret files in a container, or a corporate secrets
manager in production, selected purely by configuration.

This module defines the interface only; concrete providers live alongside it
(``env_provider``, ``file_provider``, ``vault_provider``) and are chosen by
:func:`app.config.secrets.factory.get_secrets_provider`.
"""

from __future__ import annotations

import abc


class SecretNotFoundError(KeyError):
    """Raised when a required secret is absent and no default was supplied."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"secret {self.key!r} is not available from this provider"


# Sentinel distinguishing "no default given" from ``default=None``.
_UNSET: object = object()


class SecretsProvider(abc.ABC):
    """Read-only source of named secret values.

    Providers resolve a logical *key* (e.g. ``"POSTGRES_PASSWORD"``) to its
    secret string. They never write, never log the value, and never fall back
    to the repository. Lookups are intended to happen at startup / on demand,
    not in hot paths, so implementations may perform I/O.
    """

    name: str = "abstract"

    @abc.abstractmethod
    def _lookup(self, key: str) -> str | None:
        """Return the raw secret for *key*, or ``None`` if absent."""

    def get(self, key: str, default: object = _UNSET) -> str | None:
        """Return the secret for *key*.

        Raises :class:`SecretNotFoundError` if the key is absent and no
        *default* was provided; otherwise returns *default*.
        """
        value = self._lookup(key)
        if value is not None:
            return value
        if default is _UNSET:
            raise SecretNotFoundError(key)
        return default  # type: ignore[return-value]

    def get_required(self, key: str) -> str:
        """Return the secret for *key* or raise :class:`SecretNotFoundError`."""
        value = self.get(key)
        assert value is not None  # get() raises rather than return None here
        return value

    def has(self, key: str) -> bool:
        """Return whether *key* can be resolved by this provider."""
        return self._lookup(key) is not None
