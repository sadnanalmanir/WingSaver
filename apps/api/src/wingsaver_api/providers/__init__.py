"""Flight inventory providers."""

from wingsaver_api.providers.base import FlightProvider
from wingsaver_api.providers.mock import MockFlightProvider

__all__ = ["FlightProvider", "MockFlightProvider"]
