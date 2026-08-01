"""Top-level API router (mounted at /api)."""

from fastapi import APIRouter

from wingsaver_api.api.v1 import health as health_v1

api_router = APIRouter()
api_router.include_router(health_v1.router, prefix="/v1", tags=["health"])
