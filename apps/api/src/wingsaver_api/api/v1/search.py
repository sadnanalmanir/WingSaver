"""Flight search endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from wingsaver_api.dependencies import enforce_search_rate_limit, get_search_service
from wingsaver_api.errors import AppError, get_request_id
from wingsaver_api.schemas.search import SearchRequest, SearchResponse
from wingsaver_api.services.search import SearchService

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search flights (server-side filter/sort/page)",
    dependencies=[Depends(enforce_search_rate_limit)],
)
async def search_flights(
    body: SearchRequest,
    request: Request,
    response: Response,
    service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    try:
        result = await service.search(body, request_id=get_request_id(request))
    except AppError as exc:
        if exc.code == "SEARCH_BUSY":
            retry = 1
            if isinstance(exc.details, dict) and "retry_after" in exc.details:
                retry = int(exc.details["retry_after"])
            response.headers["Retry-After"] = str(retry)
        raise
    response.headers["X-Cache"] = result.cache
    return result
