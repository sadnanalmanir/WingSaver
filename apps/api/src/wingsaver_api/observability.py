"""Sentry and related observability helpers."""

from __future__ import annotations

import sentry_sdk
import structlog
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from wingsaver_api.config import Settings

logger = structlog.get_logger(__name__)


def init_sentry(settings: Settings) -> bool:
    """Initialize Sentry when ``SENTRY_DSN`` is set. Returns True if enabled."""
    if not settings.sentry_dsn:
        logger.info("sentry_disabled", reason="SENTRY_DSN unset")
        return False

    traces_sample_rate = 1.0 if settings.environment == "local" else 0.1
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=traces_sample_rate,
        send_default_pii=False,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            LoggingIntegration(level=None, event_level=None),
        ],
    )
    logger.info("sentry_enabled", environment=settings.environment)
    return True
