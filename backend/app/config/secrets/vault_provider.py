"""Corporate secrets-manager seam (HashiCorp Vault-style).

Stage 16 requires the *architecture* for integrating a corporate secrets
manager — not a live integration (no real vault is provisioned). This provider
captures the integration contract: connection settings are taken from the
centralised configuration, and a pluggable ``client`` performs the actual KV
read. Until an operator supplies that client, lookups fail closed rather than
silently returning nothing that could be mistaken for "no secret configured".

To go live, an operator installs their vendor SDK (e.g. ``hvac`` for HashiCorp
Vault) and passes an object exposing ``read_secret(path, key) -> str | None``
when constructing the provider — no application code changes required.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.config.secrets.base import SecretsProvider


@runtime_checkable
class VaultClient(Protocol):
    """Minimal contract a concrete vault client must satisfy."""

    def read_secret(self, path: str, key: str) -> str | None:
        """Return the value at *key* under the KV *path*, or ``None``."""
        ...


class VaultNotConfiguredError(RuntimeError):
    """Raised when the vault provider is selected but no client is wired."""


class VaultSecretsProvider(SecretsProvider):
    """Resolve secrets from a corporate secrets manager (seam)."""

    name = "vault"

    def __init__(
        self,
        *,
        address: str | None,
        secret_path: str | None,
        client: VaultClient | None = None,
        namespace: str | None = None,
    ) -> None:
        self._address = address
        self._secret_path = secret_path
        self._namespace = namespace
        self._client = client

    def _lookup(self, key: str) -> str | None:
        if self._client is None:
            raise VaultNotConfiguredError(
                "SECRETS_PROVIDER=vault requires a VaultClient. Configure "
                "VAULT_ADDR / VAULT_SECRET_PATH and inject a client via "
                "app.config.secrets.factory. See docs/production/secrets.md."
            )
        if not self._secret_path:
            raise VaultNotConfiguredError("VAULT_SECRET_PATH is not set.")
        return self._client.read_secret(self._secret_path, key)
