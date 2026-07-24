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
from app.middleware import RequestContextMiddleware

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
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure a :class:`FastAPI` application instance."""
    settings = settings or get_settings()
    configure_logging(settings)

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
    app.add_middleware(RequestContextMiddleware)
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
