"""Health and readiness endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from wingsaver_api.config import Settings
from wingsaver_api.main import create_app


def test_root_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_v1_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_local_without_redis(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["environment"] == "local"
    assert body["checks"]["redis"]["status"] == "skipped"
    assert body["checks"]["database"]["status"] == "skipped"


def test_ready_staging_requires_redis() -> None:
    settings = Settings(
        environment="staging",
        jwt_secret="dev-only-change-me",
        cors_origins=["http://localhost:3000"],
        redis_url=None,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        response = client.get("/api/v1/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["checks"]["redis"]["status"] == "error"


def test_openapi_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    body = response.json()
    assert body["info"]["title"] == "WingSaver API"
    paths = body["paths"]
    assert "/health" in paths
    assert "/api/v1/ready" in paths
