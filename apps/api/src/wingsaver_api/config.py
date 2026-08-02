"""Application settings (pydantic-settings) and production boot checks."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        # Allow constructor kwargs (redis_url=...) while env still uses REDIS_URL
        populate_by_name=True,
    )

    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"

    # Neon: pooled URL for app runtime; optional direct for Alembic (later PRs)
    # Env names are uppercase field names by default (DATABASE_URL, REDIS_URL, …)
    database_url: str | None = None
    database_url_direct: str | None = None
    redis_url: str | None = None

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    # Vercel preview regex; None/empty disables allow_origin_regex
    cors_origin_regex: str | None = None

    flight_provider: Literal["mock", "amadeus", "duffel"] = "mock"
    amadeus_client_id: str | None = None
    amadeus_client_secret: str | None = None
    amadeus_hostname: Literal["test", "production"] = "test"
    duffel_access_token: str | None = None

    # Weak default is local-only; validate_runtime() refuses it in production
    jwt_secret: str = "dev-only-change-me"
    jwt_access_ttl_minutes: int = 30
    jwt_refresh_ttl_days: int = 7

    search_cache_ttl_seconds_mock: int = 900
    search_cache_ttl_seconds_live: int = 180
    offer_cache_ttl_seconds: int = 86400
    rate_limit_search_per_minute: int = 30
    rate_limit_fail_open: bool = True
    http_timeout_seconds: float = 25.0
    trusted_proxy_hops: int = 1

    # Stampede control (search miss fill)
    stampede_lock_ttl_ms: int = 30_000
    stampede_wait_timeout_ms: int = 2_500
    provider_max_inflight: int = 20

    db_pool_size: int = 5
    db_max_overflow: int = 5
    redis_max_connections: int = 20

    sentry_dsn: str | None = None
    # Invite-only at launch (product decision)
    auth_registration_enabled: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_origin_regex", mode="before")
    @classmethod
    def empty_regex_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    def search_cache_ttl(self) -> int:
        if self.flight_provider == "mock":
            return self.search_cache_ttl_seconds_mock
        return self.search_cache_ttl_seconds_live

    def validate_runtime(self) -> None:
        """Fail closed on production misconfiguration (called from create_app)."""
        if self.environment != "production":
            return
        weak_secrets = {"dev-only-change-me", "change-me-in-production"}
        if self.jwt_secret in weak_secrets or len(self.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be a strong secret (>=32 chars) in production")
        if not self.redis_url:
            raise RuntimeError("REDIS_URL required in production (cache + rate limits)")
        if self.flight_provider == "amadeus" and not (
            self.amadeus_client_id and self.amadeus_client_secret
        ):
            raise RuntimeError("Amadeus credentials required when FLIGHT_PROVIDER=amadeus")
        if self.flight_provider == "duffel" and not self.duffel_access_token:
            raise RuntimeError("DUFFEL_ACCESS_TOKEN required when FLIGHT_PROVIDER=duffel")
        if not self.cors_origins and not self.cors_origin_regex:
            raise RuntimeError("CORS_ORIGINS or CORS_ORIGIN_REGEX required in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings (tests / process reloads)."""
    get_settings.cache_clear()
