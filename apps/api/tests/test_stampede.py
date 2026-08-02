"""Stampede lock: concurrent miss fill should not double-call provider."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from wingsaver_api.config import Settings
from wingsaver_api.errors import AppError
from wingsaver_api.schemas.offer import Money, Offer, Segment, Slice
from wingsaver_api.schemas.search import Passengers, SearchRequest
from wingsaver_api.services.offer_store import InMemoryOfferStore
from wingsaver_api.services.search import SearchService


def _request() -> SearchRequest:
    depart = date.today() + timedelta(days=40)
    return SearchRequest(
        trip_type="one_way",
        origin="JFK",
        destination="LHR",
        departure_date=depart,
        passengers=Passengers(adults=1, children=0, infants=0),
        cabin_class="economy",
        currency="USD",
    )


def _offer() -> Offer:
    depart = datetime.now(UTC)
    return Offer(
        id="temp_0",
        provider="mock",
        price=Money(amount="200.00", currency="USD"),
        cabin_class="economy",
        validating_airline="BA",
        slices=[
            Slice(
                direction="outbound",
                duration_minutes=400,
                stops=0,
                segments=[
                    Segment(
                        origin="JFK",
                        destination="LHR",
                        depart_at=depart,
                        arrive_at=depart + timedelta(minutes=400),
                        marketing_carrier="BA",
                        flight_number="BA1",
                        duration_minutes=400,
                    )
                ],
            )
        ],
    )


@pytest.mark.asyncio
async def test_concurrent_miss_single_provider_call() -> None:
    store = InMemoryOfferStore()
    settings = Settings(
        environment="local",
        redis_url=None,
        stampede_wait_timeout_ms=2000,
        stampede_lock_ttl_ms=5000,
        provider_max_inflight=20,
    )
    provider = AsyncMock()
    provider.name = "mock"

    async def slow_search(_req: SearchRequest) -> list[Offer]:
        await asyncio.sleep(0.15)
        return [_offer()]

    provider.search = AsyncMock(side_effect=slow_search)
    service = SearchService(provider=provider, store=store, settings=settings)
    req = _request()

    results = await asyncio.gather(
        service.search(req, request_id="a"),
        service.search(req, request_id="b"),
        service.search(req, request_id="c"),
    )
    assert provider.search.await_count == 1
    assert all(r.total >= 1 for r in results)
    # First filler is MISS; waiters become HIT once key appears
    statuses = {r.cache for r in results}
    assert "MISS" in statuses
    assert "HIT" in statuses or all(r.cache == "MISS" for r in results)
    # At least one result must succeed with offers
    assert results[0].offers[0].id.startswith("mock_")


@pytest.mark.asyncio
async def test_waiter_timeout_search_busy() -> None:
    store = InMemoryOfferStore()
    settings = Settings(
        environment="local",
        redis_url=None,
        stampede_wait_timeout_ms=100,
        stampede_lock_ttl_ms=5000,
    )
    provider = AsyncMock()
    provider.name = "mock"

    async def very_slow(_req: SearchRequest) -> list[Offer]:
        await asyncio.sleep(1.0)
        return [_offer()]

    provider.search = AsyncMock(side_effect=very_slow)
    service = SearchService(provider=provider, store=store, settings=settings)
    req = _request()

    async def filler() -> None:
        try:
            await service.search(req, request_id="filler")
        except AppError:
            pass

    task = asyncio.create_task(filler())
    await asyncio.sleep(0.05)  # let filler take the lock
    with pytest.raises(AppError) as exc_info:
        await service.search(req, request_id="waiter")
    assert exc_info.value.code == "SEARCH_BUSY"
    await task
