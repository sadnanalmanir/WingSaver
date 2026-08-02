"""Search orchestration: provider call, WingSaver ids, filter/sort/page."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from ulid import ULID

from wingsaver_api.config import Settings
from wingsaver_api.providers.base import FlightProvider
from wingsaver_api.schemas.offer import Offer, OfferPublic
from wingsaver_api.schemas.search import (
    SearchRequest,
    SearchResponse,
    trip_identity_cache_key,
)
from wingsaver_api.services.offer_store import InMemoryOfferStore


def new_offer_id(provider: str) -> str:
    """WingSaver-owned public id: ``{provider}_{ulid}``."""
    return f"{provider}_{ULID()}"


class SearchService:
    def __init__(
        self,
        *,
        provider: FlightProvider,
        store: InMemoryOfferStore,
        settings: Settings,
    ) -> None:
        self.provider = provider
        self.store = store
        self.settings = settings

    async def search(self, request: SearchRequest, *, request_id: str | None) -> SearchResponse:
        provider_name = getattr(self.provider, "name", self.settings.flight_provider)
        cache_key = trip_identity_cache_key(request, provider=provider_name)

        cached = self.store.get_search(cache_key)
        cache_status: str
        if cached is None:
            cache_status = "MISS"
            raw_offers = await self.provider.search(request)
            # Cap at 50 per design
            raw_offers = raw_offers[:50]
            offer_ids: list[str] = []
            expires_at = datetime.now(UTC) + timedelta(
                seconds=self.settings.offer_cache_ttl_seconds
            )
            for raw in raw_offers:
                offer = self._assign_id(raw, provider_name=provider_name, expires_at=expires_at)
                self.store.put_offer(offer, ttl_seconds=self.settings.offer_cache_ttl_seconds)
                offer_ids.append(offer.id)
            cached = self.store.put_search(
                cache_key,
                offer_ids,
                ttl_seconds=self.settings.search_cache_ttl(),
            )
        else:
            cache_status = "HIT"

        offers: list[Offer] = []
        for oid in cached.offer_ids:
            found = self.store.get_offer(oid)
            if found is not None:
                offers.append(found)
        filtered = self._apply_filters(offers, request)
        sorted_offers = self._apply_sort(filtered, request.sort)
        total = len(sorted_offers)
        page_items = self._paginate(sorted_offers, request.page, request.page_size)

        return SearchResponse(
            request_id=request_id,
            cache=cache_status,  # type: ignore[arg-type]
            cached_at=cached.cached_at.isoformat().replace("+00:00", "Z"),
            stale=False,
            currency=request.currency,
            total=total,
            page=request.page,
            page_size=request.page_size,
            offers=[o.to_public() for o in page_items],
        )

    def get_offer(self, offer_id: str) -> OfferPublic | None:
        offer = self.store.get_offer(offer_id)
        if offer is None:
            return None
        return offer.to_public()

    def _assign_id(
        self,
        offer: Offer,
        *,
        provider_name: str,
        expires_at: datetime,
    ) -> Offer:
        public_id = new_offer_id(provider_name)
        payload = dict(offer.provider_payload or {})
        # Preserve any temporary/upstream id inside server-only payload
        if offer.id and not offer.id.startswith(f"{provider_name}_"):
            payload.setdefault("upstream_temp_id", offer.id)
        return offer.model_copy(
            update={
                "id": public_id,
                "provider": provider_name,
                "expires_at": expires_at,
                "provider_payload": payload or None,
            }
        )

    def _apply_filters(self, offers: list[Offer], request: SearchRequest) -> list[Offer]:
        filters = request.filters
        if filters is None:
            return list(offers)

        result: list[Offer] = []
        for offer in offers:
            max_stops = max((s.stops for s in offer.slices), default=0)
            if filters.max_stops is not None and max_stops > filters.max_stops:
                continue
            if filters.airlines:
                allowed = {a.upper() for a in filters.airlines}
                if offer.validating_airline.upper() not in allowed:
                    continue
            if filters.max_price is not None:
                if Decimal(offer.price.amount) > Decimal(str(filters.max_price)):
                    continue
            if filters.max_duration_minutes is not None:
                total_dur = sum(s.duration_minutes for s in offer.slices)
                if total_dur > filters.max_duration_minutes:
                    continue
            result.append(offer)
        return result

    def _apply_sort(self, offers: list[Offer], sort: str) -> list[Offer]:
        def price_key(o: Offer) -> Decimal:
            return Decimal(o.price.amount)

        def duration_key(o: Offer) -> int:
            return sum(s.duration_minutes for s in o.slices)

        def depart_key(o: Offer) -> datetime:
            return o.slices[0].segments[0].depart_at

        if sort == "price_asc":
            return sorted(offers, key=price_key)
        if sort == "price_desc":
            return sorted(offers, key=price_key, reverse=True)
        if sort == "duration_asc":
            return sorted(offers, key=duration_key)
        if sort == "departure_asc":
            return sorted(offers, key=depart_key)
        return list(offers)

    def _paginate(self, offers: list[Offer], page: int, page_size: int) -> list[Offer]:
        start = (page - 1) * page_size
        end = start + page_size
        return offers[start:end]
