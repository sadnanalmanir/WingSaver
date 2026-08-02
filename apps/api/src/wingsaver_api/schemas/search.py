"""Search request/response schemas and trip-identity cache key helpers."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from wingsaver_api.schemas.offer import CabinClass, OfferPublic

TripType = Literal["one_way", "round_trip"]
SearchSort = Literal[
    "price_asc",
    "price_desc",
    "duration_asc",
    "departure_asc",
]

_IATA = re.compile(r"^[A-Za-z]{3}$")
_CURRENCY = re.compile(r"^[A-Za-z]{3}$")


class Passengers(BaseModel):
    adults: int = Field(1, ge=1, le=9)
    children: int = Field(0, ge=0, le=9)
    infants: int = Field(0, ge=0, le=9)

    @model_validator(mode="after")
    def infants_not_exceed_adults(self) -> Passengers:
        if self.infants > self.adults:
            raise ValueError("infants cannot exceed adults")
        if self.adults + self.children + self.infants < 1:
            raise ValueError("at least one passenger required")
        return self


class SearchFilters(BaseModel):
    max_stops: int | None = Field(default=None, ge=0, le=3)
    airlines: list[str] | None = None
    max_price: float | None = Field(default=None, gt=0)
    max_duration_minutes: int | None = Field(default=None, gt=0)

    @field_validator("airlines")
    @classmethod
    def airlines_upper(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [code.upper() for code in value]


class SearchRequest(BaseModel):
    trip_type: TripType
    origin: str
    destination: str
    departure_date: date
    return_date: date | None = None
    passengers: Passengers = Field(
        default_factory=lambda: Passengers(adults=1, children=0, infants=0)
    )
    cabin_class: CabinClass = "economy"
    currency: str = "USD"
    filters: SearchFilters | None = None
    sort: SearchSort = "price_asc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=50)

    @field_validator("origin", "destination")
    @classmethod
    def validate_iata(cls, value: str) -> str:
        if not _IATA.match(value):
            raise ValueError("must be a 3-letter IATA code")
        return value.upper()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if not _CURRENCY.match(value):
            raise ValueError("must be a 3-letter currency code")
        return value.upper()

    @model_validator(mode="after")
    def validate_trip_dates(self) -> SearchRequest:
        if self.origin == self.destination:
            raise ValueError("origin and destination must differ")
        if self.trip_type == "round_trip":
            if self.return_date is None:
                raise ValueError("return_date is required for round_trip")
            if self.return_date < self.departure_date:
                raise ValueError("return_date must be on or after departure_date")
        elif self.return_date is not None:
            raise ValueError("return_date must be omitted for one_way")
        return self


class SearchResponse(BaseModel):
    request_id: str | None = None
    cache: Literal["HIT", "MISS"]
    cached_at: str
    stale: bool = False
    price_disclaimer: str = "Prices are estimates and may change before booking."
    currency: str
    total: int
    page: int
    page_size: int
    offers: list[OfferPublic]


def trip_identity_dict(request: SearchRequest, *, provider: str) -> dict[str, Any]:
    """Material hashed for search cache keys — excludes filters/sort/page/page_size."""
    return {
        "provider": provider,
        "trip_type": request.trip_type,
        "origin": request.origin,
        "destination": request.destination,
        "departure_date": request.departure_date.isoformat(),
        "return_date": request.return_date.isoformat() if request.return_date else None,
        "passengers": {
            "adults": request.passengers.adults,
            "children": request.passengers.children,
            "infants": request.passengers.infants,
        },
        "cabin_class": request.cabin_class,
        "currency": request.currency,
    }


def trip_identity_cache_key(request: SearchRequest, *, provider: str) -> str:
    """Stable cache key for trip identity only."""
    payload = trip_identity_dict(request, provider=provider)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"search:v1:{provider}:{digest}"
