"""Offer + search result stores (in-memory for local; Redis for multi-instance)."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable

from redis.asyncio import Redis

from wingsaver_api.schemas.offer import Offer


@dataclass
class CachedSearch:
    offer_ids: list[str]
    cached_at: datetime


def offer_redis_key(offer_id: str) -> str:
    return f"offer:v1:{offer_id}"


def lock_redis_key(search_cache_key: str) -> str:
    return f"lock:{search_cache_key}"


@runtime_checkable
class OfferStore(Protocol):
    async def put_offer(self, offer: Offer, *, ttl_seconds: int) -> None: ...

    async def get_offer(self, offer_id: str) -> Offer | None: ...

    async def put_search(
        self, cache_key: str, offer_ids: list[str], *, ttl_seconds: int
    ) -> CachedSearch: ...

    async def get_search(self, cache_key: str) -> CachedSearch | None: ...

    async def try_acquire_lock(self, cache_key: str, *, ttl_ms: int) -> bool: ...

    async def release_lock(self, cache_key: str) -> None: ...

    async def try_begin_provider_call(self, *, max_inflight: int) -> bool: ...

    async def end_provider_call(self) -> None: ...


class InMemoryOfferStore:
    """Process-local store for local/dev and unit tests without Redis."""

    def __init__(self) -> None:
        self._offers: dict[str, tuple[Offer, datetime]] = {}
        self._searches: dict[str, tuple[CachedSearch, datetime]] = {}
        self._locks: set[str] = set()
        self._inflight = 0
        self._guard = asyncio.Lock()

    async def put_offer(self, offer: Offer, *, ttl_seconds: int) -> None:
        expires = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        async with self._guard:
            self._offers[offer.id] = (offer, expires)

    async def get_offer(self, offer_id: str) -> Offer | None:
        async with self._guard:
            item = self._offers.get(offer_id)
            if item is None:
                return None
            offer, expires = item
            if expires <= datetime.now(UTC):
                del self._offers[offer_id]
                return None
            return offer

    async def put_search(
        self, cache_key: str, offer_ids: list[str], *, ttl_seconds: int
    ) -> CachedSearch:
        cached_at = datetime.now(UTC)
        expires = cached_at + timedelta(seconds=ttl_seconds)
        entry = CachedSearch(offer_ids=list(offer_ids), cached_at=cached_at)
        async with self._guard:
            self._searches[cache_key] = (entry, expires)
        return entry

    async def get_search(self, cache_key: str) -> CachedSearch | None:
        async with self._guard:
            item = self._searches.get(cache_key)
            if item is None:
                return None
            entry, expires = item
            if expires <= datetime.now(UTC):
                del self._searches[cache_key]
                return None
            return entry

    async def try_acquire_lock(self, cache_key: str, *, ttl_ms: int) -> bool:
        # ttl_ms ignored in-memory; lock released explicitly or process death
        del ttl_ms
        async with self._guard:
            lock_key = lock_redis_key(cache_key)
            if lock_key in self._locks:
                return False
            self._locks.add(lock_key)
            return True

    async def release_lock(self, cache_key: str) -> None:
        async with self._guard:
            self._locks.discard(lock_redis_key(cache_key))

    async def try_begin_provider_call(self, *, max_inflight: int) -> bool:
        async with self._guard:
            if self._inflight >= max_inflight:
                return False
            self._inflight += 1
            return True

    async def end_provider_call(self) -> None:
        async with self._guard:
            self._inflight = max(0, self._inflight - 1)

    async def clear(self) -> None:
        async with self._guard:
            self._offers.clear()
            self._searches.clear()
            self._locks.clear()
            self._inflight = 0


class RedisOfferStore:
    """Redis-backed store shared across FastAPI Cloud instances."""

    PROVIDER_INFLIGHT_KEY = "provider:inflight"

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def put_offer(self, offer: Offer, *, ttl_seconds: int) -> None:
        # Store full internal model (incl. provider_payload) for future revalidation
        payload = offer.model_dump(mode="json")
        await self._redis.set(
            offer_redis_key(offer.id),
            json.dumps(payload),
            ex=ttl_seconds,
        )

    async def get_offer(self, offer_id: str) -> Offer | None:
        raw = await self._redis.get(offer_redis_key(offer_id))
        if raw is None:
            return None
        data = json.loads(raw)
        return Offer.model_validate(data)

    async def put_search(
        self, cache_key: str, offer_ids: list[str], *, ttl_seconds: int
    ) -> CachedSearch:
        cached_at = datetime.now(UTC)
        entry = CachedSearch(offer_ids=list(offer_ids), cached_at=cached_at)
        payload = {
            "offer_ids": entry.offer_ids,
            "cached_at": cached_at.isoformat(),
        }
        await self._redis.set(cache_key, json.dumps(payload), ex=ttl_seconds)
        return entry

    async def get_search(self, cache_key: str) -> CachedSearch | None:
        raw = await self._redis.get(cache_key)
        if raw is None:
            return None
        data = json.loads(raw)
        cached_at = datetime.fromisoformat(data["cached_at"])
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=UTC)
        return CachedSearch(offer_ids=list(data["offer_ids"]), cached_at=cached_at)

    async def try_acquire_lock(self, cache_key: str, *, ttl_ms: int) -> bool:
        # SET key NX PX ttl_ms
        result = await self._redis.set(
            lock_redis_key(cache_key),
            "1",
            nx=True,
            px=ttl_ms,
        )
        return result is True

    async def release_lock(self, cache_key: str) -> None:
        await self._redis.delete(lock_redis_key(cache_key))

    async def try_begin_provider_call(self, *, max_inflight: int) -> bool:
        # INCR then check; if over limit DECR and reject
        count = await self._redis.incr(self.PROVIDER_INFLIGHT_KEY)
        if count == 1:
            await self._redis.expire(self.PROVIDER_INFLIGHT_KEY, 120)
        if count > max_inflight:
            await self._redis.decr(self.PROVIDER_INFLIGHT_KEY)
            return False
        return True

    async def end_provider_call(self) -> None:
        count = await self._redis.decr(self.PROVIDER_INFLIGHT_KEY)
        if count < 0:
            await self._redis.set(self.PROVIDER_INFLIGHT_KEY, 0)
