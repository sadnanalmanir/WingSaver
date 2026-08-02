"""HTTP-level rate limit on POST /api/v1/search."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from wingsaver_api.config import Settings
from wingsaver_api.main import create_app


def _body() -> dict[str, object]:
    depart = date.today() + timedelta(days=30)
    return {
        "trip_type": "one_way",
        "origin": "JFK",
        "destination": "LHR",
        "departure_date": depart.isoformat(),
        "passengers": {"adults": 1, "children": 0, "infants": 0},
        "cabin_class": "economy",
        "currency": "USD",
        "page": 1,
        "page_size": 5,
    }


def test_search_rate_limit_returns_429() -> None:
    settings = Settings(
        environment="local",
        redis_url=None,
        rate_limit_search_per_minute=2,
        rate_limit_fail_open=True,
    )
    # Without Redis, limiter fail-opens — force in-memory path by using a
    # process-local limiter via redis faker is better. Here we monkey via
    # creating app and swapping rate limiter with one that has redis.
    from fakeredis import FakeAsyncRedis

    from wingsaver_api.services.rate_limit import RateLimiter

    app = create_app(settings)

    # Install fake redis + limiter before TestClient lifespan... lifespan overwrites.
    # Patch lifespan state after startup using a dependency override pattern:
    # create client, then replace app.state.rate_limiter and offer_store.

    with TestClient(app) as client:
        fake = FakeAsyncRedis(decode_responses=True)
        client.app.state.redis = fake  # type: ignore[attr-defined]
        client.app.state.rate_limiter = RateLimiter(fake, fail_open=False)  # type: ignore[attr-defined]
        # keep memory store for offers
        r1 = client.post("/api/v1/search", json=_body())
        r2 = client.post("/api/v1/search", json=_body())
        r3 = client.post("/api/v1/search", json=_body())

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 429
    body = r3.json()
    assert body["error"]["code"] == "RATE_LIMITED"
    assert r3.headers.get("Retry-After") is not None
