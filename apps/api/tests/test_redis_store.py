"""Redis offer store + search cache integration (fakeredis)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fakeredis import FakeAsyncRedis

from wingsaver_api.schemas.offer import Money, Offer, Segment, Slice
from wingsaver_api.services.offer_store import RedisOfferStore, offer_redis_key


def _sample_offer(offer_id: str = "mock_01TEST") -> Offer:
    depart = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    return Offer(
        id=offer_id,
        provider="mock",
        price=Money(amount="100.00", currency="USD"),
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
                        flight_number="BA178",
                        duration_minutes=400,
                    )
                ],
            )
        ],
        provider_payload={"upstream": "1"},
        expires_at=depart + timedelta(days=1),
    )


@pytest.mark.asyncio
async def test_redis_put_get_offer_roundtrip() -> None:
    redis = FakeAsyncRedis(decode_responses=True)
    store = RedisOfferStore(redis)
    offer = _sample_offer()
    await store.put_offer(offer, ttl_seconds=60)
    raw = await redis.get(offer_redis_key(offer.id))
    assert raw is not None
    loaded = await store.get_offer(offer.id)
    assert loaded is not None
    assert loaded.id == offer.id
    assert loaded.provider_payload == {"upstream": "1"}
    await redis.aclose()


@pytest.mark.asyncio
async def test_redis_search_cache_and_lock() -> None:
    redis = FakeAsyncRedis(decode_responses=True)
    store = RedisOfferStore(redis)
    key = "search:v1:mock:abc"
    assert await store.try_acquire_lock(key, ttl_ms=5000) is True
    assert await store.try_acquire_lock(key, ttl_ms=5000) is False
    await store.release_lock(key)
    assert await store.try_acquire_lock(key, ttl_ms=5000) is True
    await store.release_lock(key)

    cached = await store.put_search(key, ["mock_a", "mock_b"], ttl_seconds=60)
    loaded = await store.get_search(key)
    assert loaded is not None
    assert loaded.offer_ids == ["mock_a", "mock_b"]
    assert loaded.cached_at == cached.cached_at
    await redis.aclose()


@pytest.mark.asyncio
async def test_provider_inflight_cap() -> None:
    redis = FakeAsyncRedis(decode_responses=True)
    store = RedisOfferStore(redis)
    assert await store.try_begin_provider_call(max_inflight=2) is True
    assert await store.try_begin_provider_call(max_inflight=2) is True
    assert await store.try_begin_provider_call(max_inflight=2) is False
    await store.end_provider_call()
    assert await store.try_begin_provider_call(max_inflight=2) is True
    await store.end_provider_call()
    await store.end_provider_call()
    await redis.aclose()
