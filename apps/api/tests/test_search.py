"""Search and offer API tests (mock provider + in-memory store)."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from wingsaver_api.config import Settings
from wingsaver_api.main import create_app
from wingsaver_api.services.search import new_offer_id


def _client() -> TestClient:
    settings = Settings(environment="local", redis_url=None, flight_provider="mock")
    return TestClient(create_app(settings))


def _search_body(**overrides: object) -> dict[str, object]:
    depart = date.today() + timedelta(days=30)
    ret = depart + timedelta(days=10)
    body: dict[str, object] = {
        "trip_type": "round_trip",
        "origin": "JFK",
        "destination": "LHR",
        "departure_date": depart.isoformat(),
        "return_date": ret.isoformat(),
        "passengers": {"adults": 1, "children": 0, "infants": 0},
        "cabin_class": "economy",
        "currency": "USD",
        "sort": "price_asc",
        "page": 1,
        "page_size": 10,
    }
    body.update(overrides)
    return body


def test_search_returns_offers_and_disclaimer() -> None:
    with _client() as client:
        response = client.post("/api/v1/search", json=_search_body())
    assert response.status_code == 200
    body = response.json()
    assert body["cache"] == "MISS"
    assert body["total"] >= 1
    assert len(body["offers"]) <= 10
    assert body["price_disclaimer"]
    assert body["stale"] is False
    assert response.headers.get("X-Cache") == "MISS"
    offer = body["offers"][0]
    assert offer["id"].startswith("mock_")
    assert "provider_payload" not in offer
    assert offer["slices"]


def test_second_search_is_cache_hit() -> None:
    with _client() as client:
        first = client.post("/api/v1/search", json=_search_body())
        second = client.post("/api/v1/search", json=_search_body())
    assert first.json()["cache"] == "MISS"
    assert second.json()["cache"] == "HIT"
    assert second.headers.get("X-Cache") == "HIT"
    # Same trip ⇒ same offer ids (store hit)
    assert first.json()["offers"][0]["id"] == second.json()["offers"][0]["id"]


def test_filter_change_does_not_require_new_provider_miss() -> None:
    """Filters excluded from cache key — second call with filters should HIT."""
    with _client() as client:
        base = client.post("/api/v1/search", json=_search_body())
        filtered = client.post(
            "/api/v1/search",
            json=_search_body(filters={"max_stops": 0}, page=1, page_size=5),
        )
    assert base.json()["cache"] == "MISS"
    assert filtered.json()["cache"] == "HIT"
    for offer in filtered.json()["offers"]:
        max_stops = max(s["stops"] for s in offer["slices"])
        assert max_stops <= 0


def test_get_offer_detail() -> None:
    with _client() as client:
        search = client.post("/api/v1/search", json=_search_body())
        offer_id = search.json()["offers"][0]["id"]
        detail = client.get(f"/api/v1/offers/{offer_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == offer_id
    assert "provider_payload" not in body


def test_get_offer_not_found() -> None:
    with _client() as client:
        response = client.get("/api/v1/offers/mock_01DOESNOTEXIST000000000000")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "OFFER_NOT_FOUND"


def test_offer_ids_are_unique_across_two_searches() -> None:
    """Two searches must not collide on public ids (WingSaver ULID ownership)."""
    with _client() as client:
        a = client.post("/api/v1/search", json=_search_body(origin="JFK", destination="LHR"))
        b = client.post("/api/v1/search", json=_search_body(origin="JFK", destination="CDG"))
    ids_a = {o["id"] for o in a.json()["offers"]}
    ids_b = {o["id"] for o in b.json()["offers"]}
    assert ids_a.isdisjoint(ids_b)


def test_new_offer_id_format() -> None:
    oid = new_offer_id("mock")
    assert oid.startswith("mock_")
    assert len(oid) > len("mock_")


def test_validation_error_for_round_trip_without_return() -> None:
    with _client() as client:
        body = _search_body()
        del body["return_date"]
        response = client.post("/api/v1/search", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_sort_price_asc() -> None:
    with _client() as client:
        response = client.post(
            "/api/v1/search",
            json=_search_body(sort="price_asc", page_size=50),
        )
    amounts = [float(o["price"]["amount"]) for o in response.json()["offers"]]
    assert amounts == sorted(amounts)
