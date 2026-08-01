"""Async Redis connection helpers."""

from __future__ import annotations

from redis.asyncio import Redis


async def create_redis_pool(url: str, *, max_connections: int = 20) -> Redis:
    """Create a Redis client. Callers own close via close_redis_pool."""
    return Redis.from_url(
        url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=max_connections,
    )


async def close_redis_pool(redis: Redis | None) -> None:
    if redis is not None:
        await redis.aclose()


async def ping_redis(redis: Redis) -> bool:
    result = await redis.ping()
    return bool(result)
