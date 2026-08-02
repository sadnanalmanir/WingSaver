"""Trip-identity cache key excludes filters/sort/pagination."""

from __future__ import annotations

from datetime import date

from wingsaver_api.schemas.search import (
    Passengers,
    SearchFilters,
    SearchRequest,
    trip_identity_cache_key,
    trip_identity_dict,
)


def _base(**overrides: object) -> SearchRequest:
    data: dict[str, object] = {
        "trip_type": "round_trip",
        "origin": "jfk",
        "destination": "lhr",
        "departure_date": date(2026, 9, 10),
        "return_date": date(2026, 9, 20),
        "passengers": Passengers(adults=1, children=0, infants=0),
        "cabin_class": "economy",
        "currency": "usd",
        "filters": None,
        "sort": "price_asc",
        "page": 1,
        "page_size": 20,
    }
    data.update(overrides)
    return SearchRequest.model_validate(data)


def test_cache_key_excludes_filters_sort_page() -> None:
    a = _base(
        filters=SearchFilters(max_stops=0, airlines=["BA"]),
        sort="price_asc",
        page=1,
        page_size=20,
    )
    b = _base(
        filters=SearchFilters(max_stops=1),
        sort="duration_asc",
        page=3,
        page_size=10,
    )
    assert trip_identity_cache_key(a, provider="mock") == trip_identity_cache_key(
        b, provider="mock"
    )
    identity = trip_identity_dict(a, provider="mock")
    assert "filters" not in identity
    assert "sort" not in identity
    assert "page" not in identity
    assert "page_size" not in identity


def test_cache_key_changes_when_origin_changes() -> None:
    a = _base(origin="JFK")
    b = _base(origin="EWR")
    assert trip_identity_cache_key(a, provider="mock") != trip_identity_cache_key(
        b, provider="mock"
    )


def test_cache_key_changes_when_departure_date_changes() -> None:
    a = _base(departure_date=date(2026, 9, 10))
    b = _base(departure_date=date(2026, 9, 11))
    assert trip_identity_cache_key(a, provider="mock") != trip_identity_cache_key(
        b, provider="mock"
    )


def test_iata_and_currency_normalized_in_identity() -> None:
    identity = trip_identity_dict(_base(origin="jfk", currency="usd"), provider="mock")
    assert identity["origin"] == "JFK"
    assert identity["currency"] == "USD"
