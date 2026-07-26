"""Select and build the active :class:`SecretsProvider` from settings.

The provider is chosen by ``SECRETS_PROVIDER`` and cached, so the rest of the
application depends only on the abstraction, never on how secrets are stored.
"""

from __future__ import annotations

from functools import lru_cache

from app.config.secrets.base import SecretsProvider
from app.config.secrets.env_provider import EnvSecretsProvider
from app.config.secrets.file_provider import FileSecretsProvider
from app.config.secrets.vault_provider import VaultClient, VaultSecretsProvider
from app.config.settings import Settings, get_settings

# An operator may register a concrete vault client at process start without
# touching call sites: ``set_vault_client(hvac_backed_client)``.
_vault_client: VaultClient | None = None


def set_vault_client(client: VaultClient | None) -> None:
    """Inject the corporate secrets-manager client used by the vault provider."""
    global _vault_client
    _vault_client = client
    build_secrets_provider.cache_clear()


def _build(settings: Settings) -> SecretsProvider:
    provider = settings.SECRETS_PROVIDER
    if provider == "env":
        return EnvSecretsProvider(prefix=settings.SECRETS_ENV_PREFIX)
    if provider == "file":
        return FileSecretsProvider(directory=settings.SECRETS_DIR)
    if provider == "vault":
        return VaultSecretsProvider(
            address=settings.VAULT_ADDR,
            secret_path=settings.VAULT_SECRET_PATH,
            namespace=settings.VAULT_NAMESPACE,
            client=_vault_client,
        )
    raise ValueError(f"unknown SECRETS_PROVIDER: {provider!r}")


@lru_cache
def build_secrets_provider() -> SecretsProvider:
    """Return the cached provider selected by the active settings."""
    return _build(get_settings())


def get_secrets_provider() -> SecretsProvider:
    """FastAPI-friendly accessor for the active secrets provider."""
    return build_secrets_provider()
