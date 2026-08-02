"""Redis fixed-window rate limiter (multi-instance safe)."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int
    failed_open: bool = False


class RateLimiter:
    """INCR + EXPIRE fixed window. Fail-open when Redis is missing or errors."""

    def __init__(
        self,
        redis: Redis | None,
        *,
        fail_open: bool = True,
    ) -> None:
        self._redis = redis
        self._fail_open = fail_open

    async def hit(
        self,
        *,
        bucket: str,
        identity: str,
        limit: int,
        window_seconds: int = 60,
    ) -> RateLimitResult:
        if limit <= 0:
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=0,
                retry_after_seconds=0,
            )

        if self._redis is None:
            logger.warning("rate_limit_skipped_no_redis", bucket=bucket)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                retry_after_seconds=0,
                failed_open=True,
            )

        window = int(time.time()) // window_seconds
        key = f"rl:{bucket}:{identity}:{window}"
        try:
            count = int(await self._redis.incr(key))
            if count == 1:
                await self._redis.expire(key, window_seconds)
            remaining = max(0, limit - count)
            if count > limit:
                ttl = await self._redis.ttl(key)
                retry = int(ttl) if ttl and int(ttl) > 0 else window_seconds
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    retry_after_seconds=retry,
                )
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                retry_after_seconds=0,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("rate_limit_redis_error", error=str(exc), bucket=bucket)
            if self._fail_open:
                return RateLimitResult(
                    allowed=True,
                    limit=limit,
                    remaining=limit,
                    retry_after_seconds=0,
                    failed_open=True,
                )
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                retry_after_seconds=window_seconds,
            )


def hash_identity(value: str) -> str:
    """Short hash so raw IPs are not stored verbatim in Redis keys."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]


def client_ip_from_request(
    *,
    client_host: str | None,
    x_forwarded_for: str | None,
    trusted_proxy_hops: int,
) -> str:
    """Pick client IP from X-Forwarded-For using trusted hop count.

    Example with trusted_proxy_hops=1 and header ``client, edge-proxy``:
    returns ``client``. Verify hop count on first FastAPI Cloud staging deploy.
    """
    if x_forwarded_for:
        parts = [p.strip() for p in x_forwarded_for.split(",") if p.strip()]
        if parts:
            hops = max(0, trusted_proxy_hops)
            if hops > 0 and len(parts) > hops:
                return parts[-(hops + 1)]
            return parts[0]
    return client_host or "unknown"
