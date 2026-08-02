"""Rate limiter and client IP helper tests."""

from __future__ import annotations

import pytest
from fakeredis import FakeAsyncRedis

from wingsaver_api.services.rate_limit import (
    RateLimiter,
    client_ip_from_request,
    hash_identity,
)


def test_client_ip_from_xff_with_one_trusted_hop() -> None:
    ip = client_ip_from_request(
        client_host="10.0.0.1",
        x_forwarded_for="203.0.113.10, 10.0.0.1",
        trusted_proxy_hops=1,
    )
    assert ip == "203.0.113.10"


def test_client_ip_falls_back_to_direct() -> None:
    ip = client_ip_from_request(
        client_host="127.0.0.1",
        x_forwarded_for=None,
        trusted_proxy_hops=1,
    )
    assert ip == "127.0.0.1"


def test_hash_identity_stable() -> None:
    assert hash_identity("1.2.3.4") == hash_identity("1.2.3.4")
    assert hash_identity("1.2.3.4") != hash_identity("1.2.3.5")


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_limit() -> None:
    redis = FakeAsyncRedis(decode_responses=True)
    limiter = RateLimiter(redis, fail_open=False)
    identity = hash_identity("9.9.9.9")
    for _ in range(3):
        result = await limiter.hit(bucket="search", identity=identity, limit=3, window_seconds=60)
        assert result.allowed
    blocked = await limiter.hit(bucket="search", identity=identity, limit=3, window_seconds=60)
    assert not blocked.allowed
    assert blocked.retry_after_seconds >= 1
    await redis.aclose()


@pytest.mark.asyncio
async def test_rate_limiter_fail_open_without_redis() -> None:
    limiter = RateLimiter(None, fail_open=True)
    result = await limiter.hit(bucket="search", identity="x", limit=1, window_seconds=60)
    assert result.allowed
    assert result.failed_open
