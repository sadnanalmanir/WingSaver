"""Deterministic mock flight inventory for MVP / CI / local demos."""

from __future__ import annotations

import hashlib
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from wingsaver_api.schemas.offer import Money, Offer, Segment, Slice
from wingsaver_api.schemas.search import SearchRequest

# Small static carrier set for variety
_CARRIERS = ("BA", "AA", "DL", "UA", "LH", "AF", "EK", "QR", "VS", "IB")


def _seed_for(request: SearchRequest) -> int:
    material = "|".join(
        [
            request.trip_type,
            request.origin,
            request.destination,
            request.departure_date.isoformat(),
            request.return_date.isoformat() if request.return_date else "",
            str(request.passengers.adults),
            str(request.passengers.children),
            str(request.passengers.infants),
            request.cabin_class,
            request.currency,
        ]
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _cabin_multiplier(cabin: str) -> Decimal:
    return {
        "economy": Decimal("1"),
        "premium_economy": Decimal("1.45"),
        "business": Decimal("2.8"),
        "first": Decimal("4.2"),
    }[cabin]


class MockFlightProvider:
    """Seeded RNG offers — same criteria ⇒ same set of flights (before WingSaver ids)."""

    name = "mock"

    def __init__(self, *, min_offers: int = 12, max_offers: int = 28) -> None:
        self.min_offers = min_offers
        self.max_offers = max_offers

    async def search(self, request: SearchRequest) -> list[Offer]:
        rng = random.Random(_seed_for(request))
        count = rng.randint(self.min_offers, self.max_offers)
        offers: list[Offer] = []

        for rank in range(count):
            offers.append(self._build_offer(request, rng, rank))
        return offers

    def _build_offer(self, request: SearchRequest, rng: random.Random, rank: int) -> Offer:
        stops = rng.choices([0, 1, 2], weights=[0.45, 0.4, 0.15])[0]
        base_minutes = rng.randint(360, 780)
        extra = stops * rng.randint(60, 150)
        duration = base_minutes + extra

        depart_hour = rng.randint(6, 22)
        depart_minute = rng.choice([0, 15, 30, 45])
        # Naive local-style datetimes with UTC for simplicity in mock
        depart_at = datetime(
            request.departure_date.year,
            request.departure_date.month,
            request.departure_date.day,
            depart_hour,
            depart_minute,
            tzinfo=UTC,
        )
        arrive_at = depart_at + timedelta(minutes=duration)

        carrier = rng.choice(_CARRIERS)
        flight_num = f"{carrier}{rng.randint(100, 999)}"

        segments = self._segments(
            origin=request.origin,
            destination=request.destination,
            depart_at=depart_at,
            arrive_at=arrive_at,
            duration=duration,
            stops=stops,
            carrier=carrier,
            flight_num=flight_num,
            rng=rng,
        )
        outbound = Slice(
            direction="outbound",
            duration_minutes=duration,
            stops=stops,
            segments=segments,
        )
        slices: list[Slice] = [outbound]

        if request.trip_type == "round_trip" and request.return_date is not None:
            ret_duration = duration + rng.randint(-40, 40)
            ret_duration = max(300, ret_duration)
            ret_stops = rng.choices([0, 1, 2], weights=[0.5, 0.35, 0.15])[0]
            ret_depart = datetime(
                request.return_date.year,
                request.return_date.month,
                request.return_date.day,
                rng.randint(7, 21),
                rng.choice([0, 15, 30, 45]),
                tzinfo=UTC,
            )
            ret_arrive = ret_depart + timedelta(minutes=ret_duration + ret_stops * 70)
            ret_carrier = rng.choice(_CARRIERS)
            ret_segments = self._segments(
                origin=request.destination,
                destination=request.origin,
                depart_at=ret_depart,
                arrive_at=ret_arrive,
                duration=ret_duration + ret_stops * 70,
                stops=ret_stops,
                carrier=ret_carrier,
                flight_num=f"{ret_carrier}{rng.randint(100, 999)}",
                rng=rng,
            )
            slices.append(
                Slice(
                    direction="inbound",
                    duration_minutes=ret_duration + ret_stops * 70,
                    stops=ret_stops,
                    segments=ret_segments,
                )
            )

        pax = (
            request.passengers.adults
            + request.passengers.children
            + Decimal("0.75") * request.passengers.infants
        )
        base = Decimal(rng.randint(280, 1100)) + Decimal(rank * 12)
        amount = (base * _cabin_multiplier(request.cabin_class) * pax).quantize(Decimal("0.01"))

        # Temporary id — SearchService replaces with mock_{ulid}
        temp_id = f"temp_{rank}"
        return Offer(
            id=temp_id,
            provider="mock",
            price=Money(amount=str(amount), currency=request.currency),
            cabin_class=request.cabin_class,
            validating_airline=carrier,
            slices=slices,
            baggage_summary="1 personal item; checked bags vary by fare",
            provider_payload={"mock_rank": rank, "seed_temp_id": temp_id},
        )

    def _segments(
        self,
        *,
        origin: str,
        destination: str,
        depart_at: datetime,
        arrive_at: datetime,
        duration: int,
        stops: int,
        carrier: str,
        flight_num: str,
        rng: random.Random,
    ) -> list[Segment]:
        if stops == 0:
            return [
                Segment(
                    origin=origin,
                    destination=destination,
                    depart_at=depart_at,
                    arrive_at=arrive_at,
                    marketing_carrier=carrier,
                    flight_number=flight_num,
                    duration_minutes=duration,
                )
            ]

        hubs = [
            h
            for h in ("BOS", "DUB", "AMS", "CDG", "FRA", "MAD", "ORD")
            if h not in {origin, destination}
        ]
        via_points = rng.sample(hubs, k=min(stops, len(hubs)))
        airports = [origin, *via_points, destination]
        leg_count = len(airports) - 1
        leg_minutes = max(60, duration // leg_count)
        cursor = depart_at
        segments: list[Segment] = []
        for i in range(leg_count):
            leg_depart = cursor
            leg_arrive = leg_depart + timedelta(minutes=leg_minutes)
            segments.append(
                Segment(
                    origin=airports[i],
                    destination=airports[i + 1],
                    depart_at=leg_depart,
                    arrive_at=leg_arrive,
                    marketing_carrier=carrier,
                    flight_number=flight_num if i == 0 else f"{carrier}{rng.randint(100, 999)}",
                    duration_minutes=leg_minutes,
                )
            )
            # Connection time between legs
            gap = rng.randint(45, 100) if i < leg_count - 1 else 0
            cursor = leg_arrive + timedelta(minutes=gap)
        return segments
