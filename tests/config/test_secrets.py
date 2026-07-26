"""Unit tests for the secrets-provider abstraction (Stage 16 §2)."""

from __future__ import annotations

import pytest

from app.config.secrets import (
    EnvSecretsProvider,
    FileSecretsProvider,
    SecretNotFoundError,
    VaultNotConfiguredError,
    VaultSecretsProvider,
)


def test_env_provider_reads_from_mapping() -> None:
    p = EnvSecretsProvider(environ={"POSTGRES_PASSWORD": "s3cret"})
    assert p.get("POSTGRES_PASSWORD") == "s3cret"
    assert p.get_required("POSTGRES_PASSWORD") == "s3cret"
    assert p.has("POSTGRES_PASSWORD") is True


def test_env_provider_applies_prefix() -> None:
    p = EnvSecretsProvider(
        prefix="DISPATCHER_", environ={"DISPATCHER_API_KEY": "abc"}
    )
    assert p.get("API_KEY") == "abc"
    assert p.has("API_KEY") is True
    assert p.has("MISSING") is False


def test_missing_secret_raises_or_defaults() -> None:
    p = EnvSecretsProvider(environ={})
    with pytest.raises(SecretNotFoundError):
        p.get("NOPE")
    assert p.get("NOPE", default=None) is None
    assert p.get("NOPE", default="fallback") == "fallback"


def test_file_provider_reads_and_trims(tmp_path) -> None:
    (tmp_path / "TOKEN").write_text("tok-value\n", encoding="utf-8")
    p = FileSecretsProvider(directory=tmp_path)
    assert p.get("TOKEN") == "tok-value"
    assert p.has("TOKEN") is True


def test_file_provider_missing_and_traversal(tmp_path) -> None:
    p = FileSecretsProvider(directory=tmp_path)
    assert p.has("ABSENT") is False
    # Path-traversal attempts resolve to "not found", never escape the dir.
    assert p.get("../etc/passwd", default=None) is None
    assert p.get("a/b", default=None) is None


def test_vault_provider_fails_closed_without_client() -> None:
    p = VaultSecretsProvider(address="https://vault.local", secret_path="app")
    with pytest.raises(VaultNotConfiguredError):
        p.get("ANY")


def test_vault_provider_uses_injected_client() -> None:
    class FakeClient:
        def read_secret(self, path: str, key: str) -> str | None:
            return f"{path}:{key}" if key == "DB" else None

    p = VaultSecretsProvider(
        address="https://vault.local",
        secret_path="apps/dispatcher",
        client=FakeClient(),
    )
    assert p.get("DB") == "apps/dispatcher:DB"
    assert p.get("OTHER", default=None) is None
