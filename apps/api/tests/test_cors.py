"""CORS configuration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from wingsaver_api.config import Settings
from wingsaver_api.main import create_app


def test_cors_allows_configured_origin() -> None:
    settings = Settings(
        environment="local",
        cors_origins=["http://localhost:3000"],
        redis_url=None,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code in {200, 204}
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_rejects_unknown_origin() -> None:
    settings = Settings(
        environment="local",
        cors_origins=["http://localhost:3000"],
        redis_url=None,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"Origin": "https://evil.example"},
        )
    # Starlette omits ACAO when origin is not allowed
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_origin_regex_allows_preview() -> None:
    settings = Settings(
        environment="staging",
        cors_origins=["https://wingsaver.vercel.app"],
        cors_origin_regex=r"https://wingsaver(-git-[\w-]+)?-[\w-]+\.vercel\.app",
        redis_url=None,
    )
    app = create_app(settings)
    preview = "https://wingsaver-git-feature-team.vercel.app"
    with TestClient(app) as client:
        response = client.get("/health", headers={"Origin": preview})
    assert response.headers.get("access-control-allow-origin") == preview


def test_request_id_echo_and_generate() -> None:
    settings = Settings(environment="local", redis_url=None)
    app = create_app(settings)
    with TestClient(app) as client:
        generated = client.get("/health")
        assert generated.headers.get("X-Request-ID")
        custom = client.get("/health", headers={"X-Request-ID": "req-custom-123"})
        assert custom.headers.get("X-Request-ID") == "req-custom-123"
