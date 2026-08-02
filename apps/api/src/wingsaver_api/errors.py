"""Domain exceptions and unified API error envelope."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger(__name__)


class AppError(Exception):
    """Application error mapped to the unified JSON envelope."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details if details is not None else {}


def get_request_id(request: Request) -> str | None:
    from_state = getattr(request.state, "request_id", None)
    if isinstance(from_state, str):
        return from_state
    scope_state = request.scope.get("state")
    if isinstance(scope_state, dict):
        value = scope_state.get("request_id")
        if isinstance(value, str):
            return value
    return None


def error_body(
    *,
    code: str,
    message: str,
    request_id: str | None,
    details: dict[str, Any] | list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "details": details if details is not None else {},
        }
    }


def _http_exception_code(status_code: int) -> str:
    mapping = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        502: "SEARCH_PROVIDER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, "HTTP_ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    """Register handlers that always return the unified error envelope."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = get_request_id(request)
        headers: dict[str, str] = {}
        if exc.status_code == 429 or exc.code == "SEARCH_BUSY":
            retry = 1
            if isinstance(exc.details, dict) and "retry_after" in exc.details:
                try:
                    retry = int(exc.details["retry_after"])
                except (TypeError, ValueError):
                    retry = 1
            headers["Retry-After"] = str(retry)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                code=exc.code,
                message=exc.message,
                request_id=request_id,
                details=exc.details,
            ),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = get_request_id(request)
        # Normalize Pydantic/FastAPI error dicts for the FE
        details: list[dict[str, Any]] = []
        for err in exc.errors():
            details.append(
                {
                    "loc": list(err.get("loc", ())),
                    "msg": err.get("msg", ""),
                    "type": err.get("type", ""),
                }
            )
        # Prefer the non-deprecated Starlette constant when available
        unprocessable = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
        return JSONResponse(
            status_code=unprocessable,
            content=error_body(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                request_id=request_id,
                details=details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = get_request_id(request)
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
        else:
            message = "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                code=_http_exception_code(exc.status_code),
                message=message,
                request_id=request_id,
                details={} if isinstance(detail, str) else {"detail": detail},
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = get_request_id(request)
        logger.exception("unhandled_error", request_id=request_id, error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_body(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                request_id=request_id,
                details={},
            ),
        )
