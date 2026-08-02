"""Flight provider port (protocol)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from wingsaver_api.schemas.offer import Offer
from wingsaver_api.schemas.search import SearchRequest


@runtime_checkable
class FlightProvider(Protocol):
    """External inventory adapter.

    Implementations return normalized offers **without** WingSaver public ids
    (id may be temporary). SearchService assigns `{provider}_{ulid}` ids.
    Detail fetch by id is NOT part of this port — offers are stored after search.
    """

    name: str

    async def search(self, request: SearchRequest) -> list[Offer]:
        """Return normalized offers for the criteria (max ~50)."""
        ...
