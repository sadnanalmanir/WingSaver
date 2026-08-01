"""FastAPI dependency injection helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Request
from redis.asyncio import Redis

from wingsaver_api.config import Settings, get_settings
from wingsaver_api.errors import AppError


def settings_dep() -> Settings:
    return get_settings()


async def get_redis(request: Request) -> AsyncIterator[Redis]:
    """Yield the process-scoped Redis client, or 503 if not configured."""
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        raise AppError(
            code="SERVICE_UNAVAILABLE",
            message="Redis is not configured",
            status_code=503,
        )
    yield redis
