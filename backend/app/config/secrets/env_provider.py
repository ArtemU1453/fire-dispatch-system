"""Environment-variable secrets provider (12-factor default)."""

from __future__ import annotations

import os
from collections.abc import Mapping

from app.config.secrets.base import SecretsProvider


class EnvSecretsProvider(SecretsProvider):
    """Resolve secrets from process environment variables.

    An optional *prefix* is prepended before lookup, so a corporate convention
    like ``DISPATCHER_POSTGRES_PASSWORD`` can back the logical key
    ``POSTGRES_PASSWORD`` without changing call sites.
    """

    name = "env"

    def __init__(
        self, prefix: str = "", environ: Mapping[str, str] | None = None
    ) -> None:
        self._prefix = prefix
        self._environ = environ if environ is not None else os.environ

    def _lookup(self, key: str) -> str | None:
        return self._environ.get(f"{self._prefix}{key}")
