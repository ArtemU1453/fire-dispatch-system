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

    # ---------------------------------------------------------------- gis ----
    # Active geocoding provider (nominatim | photon | pelias | arcgis | fake).
    GIS_PROVIDER: str = "nominatim"
    GIS_HTTP_TIMEOUT: float = 10.0
    GIS_USER_AGENT: str = "ai-dispatcher-mchs/0.1 (+https://example.local)"
    # Default locale / country bias for geocoding requests.
    GIS_DEFAULT_LANGUAGE: str = "ru"
    GIS_DEFAULT_COUNTRY_CODES: list[str] = Field(default_factory=lambda: ["ru"])
    # Provider endpoints (overridable to point at self-hosted instances).
    GIS_NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"
    GIS_PHOTON_URL: str = "https://photon.komoot.io"
    GIS_PELIAS_URL: str = "https://api.geocode.earth/v1"
    GIS_PELIAS_API_KEY: str | None = None
    GIS_ARCGIS_URL: str = (
        "https://geocode-api.arcgis.com/arcgis/rest/services/World/GeocodeServer"
    )
    GIS_ARCGIS_TOKEN: str | None = None
    # Caching (Redis-ready; "memory" or "none" for now — Redis wired later).
    GIS_CACHE_BACKEND: Literal["memory", "none"] = "memory"
    GIS_CACHE_TTL_SECONDS: int = 86400
    GIS_CACHE_MAX_ENTRIES: int = 10000
    GIS_REDIS_URL: str | None = None

    # ------------------------------------------------------------- search ----
    # Result caching for the search engine (same Redis-ready abstraction).
    SEARCH_CACHE_BACKEND: Literal["memory", "none"] = "memory"
    SEARCH_CACHE_TTL_SECONDS: int = 60
    SEARCH_CACHE_MAX_ENTRIES: int = 5000

    # ------------------------------------------------------------ routing ----
    # Routing / ETA. Default provider is the dependency-free straight-line
    # estimator so the module works out of the box; set ROUTING_OSRM_URL to use
    # OSRM (with automatic fallback to the estimator when it is unavailable).
    ROUTING_PROVIDER: Literal["haversine", "osrm"] = "haversine"
    ROUTING_OSRM_URL: str | None = None
    ROUTING_HTTP_TIMEOUT: float = 8.0
    # Straight-line estimator parameters.
    ROUTING_AVERAGE_SPEED_KMH: float = 50.0
    ROUTING_ROAD_FACTOR: float = 1.3  # detour factor applied to straight-line distance
    ROUTING_ENABLE_FALLBACK: bool = True
    # Route reuse cache (in-memory; Redis-ready abstraction, not wired yet).
    ROUTING_CACHE_BACKEND: Literal["memory", "none"] = "memory"
    ROUTING_CACHE_TTL_SECONDS: int = 120
    ROUTING_CACHE_MAX_ENTRIES: int = 2000

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
