"""FastAPI dependency injection helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Request
from redis.asyncio import Redis

from wingsaver_api.config import Settings, get_settings
from wingsaver_api.errors import AppError
from wingsaver_api.providers.base import FlightProvider
from wingsaver_api.providers.mock import MockFlightProvider
from wingsaver_api.services.offer_store import InMemoryOfferStore
from wingsaver_api.services.search import SearchService


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


def get_offer_store(request: Request) -> InMemoryOfferStore:
    store = getattr(request.app.state, "offer_store", None)
    if store is None:
        # Safety net if lifespan did not run (should not happen with TestClient)
        store = InMemoryOfferStore()
        request.app.state.offer_store = store
    return store


def get_flight_provider(request: Request) -> FlightProvider:
    provider = getattr(request.app.state, "flight_provider", None)
    if provider is not None:
        return provider  # type: ignore[no-any-return]

    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    if settings.flight_provider == "mock":
        provider = MockFlightProvider()
    else:
        # Amadeus/Duffel adapters land in later PRs; fall back to mock with explicit name
        provider = MockFlightProvider()
    request.app.state.flight_provider = provider
    return provider


def get_search_service(request: Request) -> SearchService:
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    return SearchService(
        provider=get_flight_provider(request),
        store=get_offer_store(request),
        settings=settings,
    )
