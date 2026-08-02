"""In-memory offer + search result storage (PR3; Redis lands in PR4)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock

from wingsaver_api.schemas.offer import Offer


@dataclass
class CachedSearch:
    offer_ids: list[str]
    cached_at: datetime


class InMemoryOfferStore:
    """Process-local store for offers and pre-filter search id lists.

    Suitable for local/dev and unit tests. Not shared across instances —
    production uses Redis (PR4).
    """

    def __init__(self) -> None:
        self._offers: dict[str, tuple[Offer, datetime]] = {}
        self._searches: dict[str, tuple[CachedSearch, datetime]] = {}
        self._lock = Lock()

    def put_offer(self, offer: Offer, *, ttl_seconds: int) -> None:
        expires = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        with self._lock:
            self._offers[offer.id] = (offer, expires)

    def get_offer(self, offer_id: str) -> Offer | None:
        with self._lock:
            item = self._offers.get(offer_id)
            if item is None:
                return None
            offer, expires = item
            if expires <= datetime.now(UTC):
                del self._offers[offer_id]
                return None
            return offer

    def put_search(self, cache_key: str, offer_ids: list[str], *, ttl_seconds: int) -> CachedSearch:
        cached_at = datetime.now(UTC)
        expires = cached_at + timedelta(seconds=ttl_seconds)
        entry = CachedSearch(offer_ids=list(offer_ids), cached_at=cached_at)
        with self._lock:
            self._searches[cache_key] = (entry, expires)
        return entry

    def get_search(self, cache_key: str) -> CachedSearch | None:
        with self._lock:
            item = self._searches.get(cache_key)
            if item is None:
                return None
            entry, expires = item
            if expires <= datetime.now(UTC):
                del self._searches[cache_key]
                return None
            return entry

    def clear(self) -> None:
        with self._lock:
            self._offers.clear()
            self._searches.clear()
