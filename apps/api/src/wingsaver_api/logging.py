"""Structured logging configuration (structlog) with secret/PII redaction."""

from __future__ import annotations

import logging
import sys
from collections.abc import Mapping, MutableMapping
from typing import Any

import structlog

from wingsaver_api.config import Settings

# Keys (case-insensitive) whose values are redacted in log events.
_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "client_secret",
    "jwt",
    "cookie",
    "set-cookie",
    "credit_card",
    "card_number",
    "ssn",
)

_REDACTED = "[REDACTED]"


def _is_sensitive_key(key: str) -> bool:
    lower = key.lower()
    return any(fragment in lower for fragment in _SENSITIVE_KEY_FRAGMENTS)


def redact_value(key: str, value: Any) -> Any:
    """Redact sensitive values; partially mask emails."""
    if _is_sensitive_key(key):
        return _REDACTED
    if key.lower() in {"email", "user_email"} and isinstance(value, str):
        return _mask_email(value)
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, list):
        return [redact_value(key, item) for item in value]
    return value


def _mask_email(email: str) -> str:
    if "@" not in email:
        return _REDACTED
    local, _, domain = email.partition("@")
    if not local:
        return _REDACTED
    return f"{local[0]}***@{domain}"


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {k: redact_value(str(k), v) for k, v in data.items()}


def redact_log_event(
    _logger: Any,
    _method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Structlog processor: scrub secrets and obvious PII from log events."""
    redacted = redact_mapping(event_dict)
    event_dict.clear()
    event_dict.update(redacted)
    return event_dict


def configure_logging(settings: Settings) -> None:
    """Configure stdlib + structlog. Safe to call once per process."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        redact_log_event,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.environment == "local":
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
