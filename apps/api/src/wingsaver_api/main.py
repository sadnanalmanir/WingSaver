"""Application entrypoint for FastAPI Cloud and local `fastapi dev`."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wingsaver_api.api.router import api_router
from wingsaver_api.config import Settings, get_settings
from wingsaver_api.db.redis import close_redis_pool, create_redis_pool
from wingsaver_api.errors import register_exception_handlers
from wingsaver_api.logging import configure_logging
from wingsaver_api.middleware.request_id import RequestIdMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    configure_logging(settings)

    app.state.redis = None
    app.state.http = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.http_timeout_seconds),
        headers={"User-Agent": "WingSaver-API/0.1"},
    )

    if settings.redis_url:
        try:
            app.state.redis = await create_redis_pool(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
            )
            logger.info("redis_connected")
        except Exception as exc:  # noqa: BLE001 — boot continues; readiness reports failure
            logger.error("redis_connect_failed", error=str(exc))
            app.state.redis = None

    yield

    await app.state.http.aclose()
    await close_redis_pool(getattr(app.state, "redis", None))
    app.state.redis = None


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    Pass ``settings`` in tests to avoid relying on process-wide env cache.
    """
    resolved = settings or get_settings()
    resolved.validate_runtime()

    app = FastAPI(
        title="WingSaver API",
        version="0.1.0",
        description="Airline search API",
        lifespan=lifespan,
        docs_url="/docs" if resolved.environment != "production" else None,
        redoc_url=None,
    )
    app.state.settings = resolved

    # Middleware order: last added runs first on request (RequestId outermost).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-Cache"],
        allow_origin_regex=resolved.cors_origin_regex,
    )
    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)

    @app.get("/health", tags=["health"], summary="Unversioned liveness probe")
    async def root_health() -> dict[str, str]:
        """Liveness for platform/uptime probes (no dependency checks)."""
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
