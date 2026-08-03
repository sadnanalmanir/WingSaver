"""Sentry, log redaction, security headers, production docs lockdown."""

from __future__ import annotations

from fastapi.testclient import TestClient

from wingsaver_api.config import Settings
from wingsaver_api.logging import redact_mapping, redact_value
from wingsaver_api.main import create_app
from wingsaver_api.observability import init_sentry


def test_redact_secrets_and_tokens() -> None:
    data = {
        "event": "login",
        "password": "super-secret",
        "jwt_secret": "abc",
        "authorization": "Bearer xyz",
        "amadeus_client_secret": "s3cr3t",
        "origin": "JFK",
    }
    redacted = redact_mapping(data)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["jwt_secret"] == "[REDACTED]"
    assert redacted["authorization"] == "[REDACTED]"
    assert redacted["amadeus_client_secret"] == "[REDACTED]"
    assert redacted["origin"] == "JFK"


def test_email_partial_mask() -> None:
    assert redact_value("email", "alice@example.com") == "a***@example.com"


def test_security_headers_on_health() -> None:
    settings = Settings(environment="local", redis_url=None)
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "no-referrer"


def test_docs_and_openapi_disabled_in_production() -> None:
    settings = Settings(
        environment="production",
        jwt_secret="x" * 32,
        redis_url="redis://localhost:6379/0",
        cors_origins=["https://app.example"],
    )
    app = create_app(settings)
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/health").status_code == 200


def test_docs_available_in_local() -> None:
    settings = Settings(environment="local", redis_url=None)
    with TestClient(create_app(settings)) as client:
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200


def test_init_sentry_noop_without_dsn() -> None:
    settings = Settings(environment="local", sentry_dsn=None)
    assert init_sentry(settings) is False
