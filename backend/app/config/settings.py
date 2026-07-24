"""Application settings.

Centralised, typed configuration loaded from environment variables / ``.env``.
Uses Pydantic v2 (``pydantic-settings``) so that every setting is validated at
startup and can be injected wherever it is needed (Dependency Injection).

Nothing else in the code base should read ``os.environ`` directly — always go
through :func:`get_settings` so configuration stays DRY and testable.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are read (in order of precedence) from real environment variables
    and then from a local ``.env`` file. Unknown variables are ignored so the
    same ``.env`` can be shared with other tooling.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----------------------------------------------------------------- app ---
    APP_NAME: str = "AI Dispatcher МЧС"
    APP_ENV: Literal["local", "dev", "staging", "production"] = "local"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # -------------------------------------------------------------- server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ------------------------------------------------------------ logging ----
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_JSON: bool = False

    # ---------------------------------------------------------- database -----
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "dispatcher"
    POSTGRES_PASSWORD: str = "dispatcher"
    POSTGRES_DB: str = "dispatcher"

    # SQLAlchemy engine tuning.
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True

    # --------------------------------------------------------------- cors ----
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Async DSN used by the SQLAlchemy engine (asyncpg driver)."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI_SYNC(self) -> str:
        """Sync DSN used by Alembic migrations (psycopg driver)."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Cached so the ``.env`` file is parsed only once. Tests may clear the cache
    via ``get_settings.cache_clear()`` to inject a different configuration.
    """
    return Settings()
