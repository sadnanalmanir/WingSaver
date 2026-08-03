"""Settings and production boot validation tests."""

from __future__ import annotations

import pytest

from wingsaver_api.config import Settings, clear_settings_cache


def test_cors_origins_parse_from_csv() -> None:
    settings = Settings(cors_origins="http://a.example, http://b.example")  # type: ignore[arg-type]
    assert settings.cors_origins == ["http://a.example", "http://b.example"]


def test_cors_origins_from_dotenv_style_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression: plain CORS_ORIGINS=http://localhost:3000 must not SettingsError."""
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    clear_settings_cache()
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.cors_origins == ["http://localhost:3000"]
    clear_settings_cache()


def test_search_cache_ttl_by_provider() -> None:
    mock = Settings(flight_provider="mock")
    live = Settings(flight_provider="amadeus")
    assert mock.search_cache_ttl() == mock.search_cache_ttl_seconds_mock
    assert live.search_cache_ttl() == live.search_cache_ttl_seconds_live


def test_validate_runtime_noop_for_local() -> None:
    settings = Settings(environment="local", jwt_secret="short")
    settings.validate_runtime()  # does not raise


def test_validate_runtime_rejects_weak_jwt_in_production() -> None:
    settings = Settings(
        environment="production",
        jwt_secret="dev-only-change-me",
        redis_url="redis://localhost:6379/0",
        cors_origins=["https://app.example"],
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        settings.validate_runtime()


def test_validate_runtime_rejects_missing_redis_in_production() -> None:
    settings = Settings(
        environment="production",
        jwt_secret="x" * 32,
        redis_url=None,
        cors_origins=["https://app.example"],
    )
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        settings.validate_runtime()


def test_validate_runtime_rejects_amadeus_without_credentials() -> None:
    settings = Settings(
        environment="production",
        jwt_secret="x" * 32,
        redis_url="redis://localhost:6379/0",
        cors_origins=["https://app.example"],
        flight_provider="amadeus",
        amadeus_client_id=None,
        amadeus_client_secret=None,
    )
    with pytest.raises(RuntimeError, match="Amadeus"):
        settings.validate_runtime()


def test_create_app_fails_closed_in_production() -> None:
    from wingsaver_api.main import create_app

    settings = Settings(
        environment="production",
        jwt_secret="short",
        redis_url="redis://localhost:6379/0",
        cors_origins=["https://app.example"],
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        create_app(settings)
