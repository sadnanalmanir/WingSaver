"""Unified error envelope tests."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from wingsaver_api.config import Settings
from wingsaver_api.errors import AppError
from wingsaver_api.main import create_app


class _SampleBody(BaseModel):
    value: int = Field(..., ge=1)


def _app_with_routes(
    settings: Settings | None = None,
    *,
    raise_server_exceptions: bool = True,
) -> TestClient:
    resolved = settings or Settings(environment="local", redis_url=None)
    app = create_app(resolved)
    router = APIRouter()

    @router.get("/_test/app-error")
    async def boom() -> None:
        raise AppError(
            code="OFFER_NOT_FOUND",
            message="Offer not found",
            status_code=404,
            details={"offer_id": "mock_x"},
        )

    @router.get("/_test/unhandled")
    async def unhandled() -> None:
        raise RuntimeError("secret stack should not leak")

    @router.post("/_test/validate")
    async def validate(payload: _SampleBody) -> _SampleBody:
        return payload

    app.include_router(router)
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


def test_app_error_envelope() -> None:
    with _app_with_routes() as client:
        response = client.get("/_test/app-error")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "OFFER_NOT_FOUND"
    assert body["error"]["message"] == "Offer not found"
    assert body["error"]["details"] == {"offer_id": "mock_x"}
    assert body["error"]["request_id"] is not None
    assert response.headers.get("X-Request-ID") == body["error"]["request_id"]


def test_validation_error_is_422_unified_envelope() -> None:
    with _app_with_routes() as client:
        # Missing required field → validation error (unified 422 envelope)
        response = client.post("/_test/validate", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed"
    assert isinstance(body["error"]["details"], list)
    assert body["error"]["details"]
    assert "request_id" in body["error"]


def test_http_404_envelope(client: TestClient) -> None:
    response = client.get("/no-such-route")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["request_id"] is not None


def test_unhandled_error_hides_internals() -> None:
    # raise_server_exceptions=False so TestClient returns the 500 envelope
    # instead of re-raising after ServerErrorMiddleware.
    with _app_with_routes(raise_server_exceptions=False) as client:
        response = client.get("/_test/unhandled")
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "secret stack" not in body["error"]["message"]
    assert body["error"]["details"] == {}
