"""Secrets management (Stage 16 §2).

A small abstraction that keeps secrets out of the repository and out of source
code: the application resolves passwords, API keys, tokens, certificates and
encryption keys through a :class:`SecretsProvider`, chosen by configuration.
"""

from app.config.secrets.base import SecretNotFoundError, SecretsProvider
from app.config.secrets.env_provider import EnvSecretsProvider
from app.config.secrets.factory import (
    build_secrets_provider,
    get_secrets_provider,
    set_vault_client,
)
from app.config.secrets.file_provider import FileSecretsProvider
from app.config.secrets.vault_provider import (
    VaultClient,
    VaultNotConfiguredError,
    VaultSecretsProvider,
)

__all__ = [
    "SecretsProvider",
    "SecretNotFoundError",
    "EnvSecretsProvider",
    "FileSecretsProvider",
    "VaultSecretsProvider",
    "VaultClient",
    "VaultNotConfiguredError",
    "build_secrets_provider",
    "get_secrets_provider",
    "set_vault_client",
]
