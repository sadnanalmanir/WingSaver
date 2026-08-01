"""Request ID middleware: bind correlation id and echo X-Request-ID.

Implemented as pure ASGI middleware (not BaseHTTPMiddleware) so FastAPI
exception handlers still run for unhandled errors.
"""

from __future__ import annotations

import uuid

import structlog
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_HEADER_LOWER = "x-request-id"


def generate_request_id() -> str:
    """Return a new opaque request id (UUIDv4 hex)."""
    return uuid.uuid4().hex


class RequestIdMiddleware:
    """Ensure every HTTP request has a request_id in scope/context and response headers."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)
        incoming = headers.get(REQUEST_ID_HEADER_LOWER)
        request_id = incoming.strip() if incoming and incoming.strip() else generate_request_id()

        # Available to route handlers via request.state (Starlette copies scope state)
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                response_headers[REQUEST_ID_HEADER] = request_id
            await send(message)

        await self.app(scope, receive, send_with_request_id)
