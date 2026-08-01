"""Health and readiness endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from wingsaver_api.config import Settings, get_settings
from wingsaver_api.db.redis import ping_redis

router = APIRouter()


class DependencyStatus(BaseModel):
    status: Literal["ok", "error", "skipped"]
    detail: str | None = None


class ReadyResponse(BaseModel):
    status: Literal["ok", "error"]
    environment: str
    checks: dict[str, DependencyStatus] = Field(default_factory=dict)


@router.get(
    "/health",
    response_model=dict[str, str],
    summary="Versioned liveness (prefer unversioned GET /health for probes)",
)
async def health_v1() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={
        503: {
            "description": "One or more required dependencies failed",
        }
    },
    summary="Readiness checks (Redis required in staging/production)",
)
async def ready(request: Request) -> ReadyResponse | JSONResponse:
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    checks: dict[str, DependencyStatus] = {}

    redis_required = settings.environment in {"staging", "production"}
    redis = getattr(request.app.state, "redis", None)

    if redis is None:
        if redis_required:
            checks["redis"] = DependencyStatus(status="error", detail="not configured")
        elif settings.redis_url:
            checks["redis"] = DependencyStatus(
                status="error",
                detail="REDIS_URL set but client not connected",
            )
        else:
            checks["redis"] = DependencyStatus(status="skipped", detail="REDIS_URL unset")
    else:
        try:
            ok = await ping_redis(redis)
            checks["redis"] = (
                DependencyStatus(status="ok")
                if ok
                else DependencyStatus(status="error", detail="PING failed")
            )
        except Exception as exc:  # noqa: BLE001 — surface dependency failure
            checks["redis"] = DependencyStatus(status="error", detail=str(exc))

    if settings.database_url:
        checks["database"] = DependencyStatus(
            status="skipped",
            detail="engine not initialized (accounts PR)",
        )
    else:
        checks["database"] = DependencyStatus(status="skipped", detail="DATABASE_URL unset")

    hard_fail = checks["redis"].status == "error" and (
        redis_required or settings.redis_url is not None
    )

    body = ReadyResponse(
        status="error" if hard_fail else "ok",
        environment=settings.environment,
        checks=checks,
    )

    if hard_fail:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=body.model_dump(),
        )
    return body
