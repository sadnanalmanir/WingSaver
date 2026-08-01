"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from wingsaver_api.config import Settings, clear_settings_cache
from wingsaver_api.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Default local settings for unit tests (no Redis required)."""
    clear_settings_cache()
    return Settings(
        environment="local",
        jwt_secret="dev-only-change-me",
        cors_origins=["http://localhost:3000"],
        redis_url=None,
        database_url=None,
        flight_provider="mock",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
    clear_settings_cache()
