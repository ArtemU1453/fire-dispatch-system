"""Application factory and ASGI entry point.

Assembles the FastAPI application from independently-testable pieces:
configuration, logging, middleware, exception handlers and routers. The factory
pattern keeps construction explicit and lets tests build a fresh app instance
with overridden dependencies.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import health as health_endpoint
from app.api.v1.router import api_router
from app.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.gis.cache import create_cache
from app.gis.providers import create_provider
from app.middleware import RequestContextMiddleware
from app.observability import install as install_observability
from app.observability.middleware import ObservabilityMiddleware
from app.routing.config import RoutingConfig
from app.routing.providers import create_provider as create_routing_provider
from app.routing.repositories import create_route_cache
from app.search.cache import create_search_cache

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""
    settings: Settings = app.state.settings
    logger.info(
        "Starting %s v%s (env=%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )
    # GIS provider and caches are created once and shared across requests
    # (avoids per-request HTTP client creation). Exposed via app.state.
    app.state.geo_provider = create_provider(settings)
    app.state.geo_cache = create_cache(settings)
    app.state.search_cache = create_search_cache(settings)
    # Dispatch norms now live in the database (Rule Engine); nothing to preload.
    # Routing provider + route-reuse cache (shared, created once).
    routing_config = RoutingConfig.from_settings(settings)
    app.state.route_provider = create_routing_provider(routing_config)
    app.state.route_cache = create_route_cache(
        backend=routing_config.cache_backend,
        ttl_seconds=routing_config.cache_ttl_seconds,
        max_entries=routing_config.cache_max_entries,
    )
    logger.info(
        "GIS provider: %s | routing provider: %s",
        app.state.geo_provider.name,
        app.state.route_provider.name,
    )
    try:
        yield
    finally:
        await app.state.geo_provider.aclose()
        await app.state.geo_cache.aclose()
        await app.state.search_cache.aclose()
        await app.state.route_provider.aclose()
        await app.state.route_cache.aclose()
        logger.info("Shutting down %s", settings.APP_NAME)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure a :class:`FastAPI` application instance."""
    settings = settings or get_settings()
    configure_logging(settings)
    # Observability: capture recent logs + stamp every record with the Trace ID.
    install_observability()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.state.settings = settings

    # --- Middleware -------------------------------------------------------
    # Order: CORS (outermost) → Observability (Trace ID + metrics) →
    # RequestContext (access log, sees the Trace ID) → app.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(ObservabilityMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Error handling ---------------------------------------------------
    register_exception_handlers(app)

    # --- Routes -----------------------------------------------------------
    # Top-level /health for infrastructure probes (unversioned)...
    app.include_router(health_endpoint.router)
    # ...and the full versioned API surface.
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


# ASGI application instance used by Uvicorn (``app.main:app``).
app = create_app()
