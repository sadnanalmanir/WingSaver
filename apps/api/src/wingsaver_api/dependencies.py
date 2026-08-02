"""FastAPI dependency injection helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request, Response
from redis.asyncio import Redis

from wingsaver_api.config import Settings, get_settings
from wingsaver_api.errors import AppError
from wingsaver_api.providers.base import FlightProvider
from wingsaver_api.providers.mock import MockFlightProvider
from wingsaver_api.services.offer_store import InMemoryOfferStore, OfferStore
from wingsaver_api.services.rate_limit import (
    RateLimiter,
    client_ip_from_request,
    hash_identity,
)
from wingsaver_api.services.search import SearchService


def settings_dep(request: Request) -> Settings:
    return getattr(request.app.state, "settings", None) or get_settings()


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


def get_offer_store(request: Request) -> OfferStore:
    store = getattr(request.app.state, "offer_store", None)
    if store is None:
        store = InMemoryOfferStore()
        request.app.state.offer_store = store
    return store


def get_rate_limiter(request: Request) -> RateLimiter:
    limiter = getattr(request.app.state, "rate_limiter", None)
    if limiter is not None:
        return limiter  # type: ignore[no-any-return]
    settings = settings_dep(request)
    redis = getattr(request.app.state, "redis", None)
    limiter = RateLimiter(redis, fail_open=settings.rate_limit_fail_open)
    request.app.state.rate_limiter = limiter
    return limiter


def get_flight_provider(request: Request) -> FlightProvider:
    provider = getattr(request.app.state, "flight_provider", None)
    if provider is not None:
        return provider  # type: ignore[no-any-return]

    settings = settings_dep(request)
    if settings.flight_provider == "mock":
        provider = MockFlightProvider()
    else:
        provider = MockFlightProvider()
    request.app.state.flight_provider = provider
    return provider


def get_search_service(request: Request) -> SearchService:
    settings = settings_dep(request)
    return SearchService(
        provider=get_flight_provider(request),
        store=get_offer_store(request),
        settings=settings,
    )


async def enforce_search_rate_limit(
    request: Request,
    response: Response,
    settings: Annotated[Settings, Depends(settings_dep)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Apply per-IP search rate limit; set X-RateLimit-Remaining when known."""
    xff = request.headers.get("X-Forwarded-For")
    client_host = request.client.host if request.client else None
    ip = client_ip_from_request(
        client_host=client_host,
        x_forwarded_for=xff,
        trusted_proxy_hops=settings.trusted_proxy_hops,
    )
    identity = hash_identity(ip)
    result = await limiter.hit(
        bucket="search",
        identity=identity,
        limit=settings.rate_limit_search_per_minute,
        window_seconds=60,
    )
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    if not result.allowed:
        raise AppError(
            code="RATE_LIMITED",
            message="Too many search requests; please slow down.",
            status_code=429,
            details={"retry_after": result.retry_after_seconds},
        )
