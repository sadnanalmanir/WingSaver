"""Normalized flight offer models (provider-agnostic)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CabinClass = Literal["economy", "premium_economy", "business", "first"]
ProviderName = Literal["mock", "amadeus", "duffel"]
SliceDirection = Literal["outbound", "inbound"]


class Money(BaseModel):
    amount: str = Field(..., description="Decimal string, e.g. '542.30'")
    currency: str = Field(..., min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, value: str) -> str:
        return value.upper()

    @field_validator("amount")
    @classmethod
    def amount_is_decimal(cls, value: str) -> str:
        try:
            Decimal(value)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("amount must be a decimal string") from exc
        return value


class Segment(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    depart_at: datetime
    arrive_at: datetime
    marketing_carrier: str = Field(..., min_length=2, max_length=3)
    flight_number: str
    duration_minutes: int = Field(..., ge=1)

    @field_validator("origin", "destination")
    @classmethod
    def iata_upper(cls, value: str) -> str:
        return value.upper()

    @field_validator("marketing_carrier")
    @classmethod
    def carrier_upper(cls, value: str) -> str:
        return value.upper()


class Slice(BaseModel):
    direction: SliceDirection
    duration_minutes: int = Field(..., ge=1)
    stops: int = Field(..., ge=0)
    segments: list[Segment] = Field(..., min_length=1)


class Offer(BaseModel):
    """Internal offer including optional server-only provider payload."""

    model_config = ConfigDict(extra="ignore")

    id: str
    provider: ProviderName
    price: Money
    cabin_class: CabinClass
    validating_airline: str = Field(..., min_length=2, max_length=3)
    slices: list[Slice] = Field(..., min_length=1)
    baggage_summary: str | None = None
    expires_at: datetime | None = None
    # Server-only: never serialize to public API responses
    provider_payload: dict[str, Any] | None = Field(default=None, exclude=True)

    @field_validator("validating_airline")
    @classmethod
    def airline_upper(cls, value: str) -> str:
        return value.upper()

    def to_public(self) -> OfferPublic:
        return OfferPublic.model_validate(self.model_dump(exclude={"provider_payload"}))


class OfferPublic(BaseModel):
    """Client-facing offer (no provider_payload)."""

    id: str
    provider: ProviderName
    price: Money
    cabin_class: CabinClass
    validating_airline: str
    slices: list[Slice]
    baggage_summary: str | None = None
    expires_at: datetime | None = None
