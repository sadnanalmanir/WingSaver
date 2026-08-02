"""Flight search endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from wingsaver_api.dependencies import get_search_service
from wingsaver_api.errors import get_request_id
from wingsaver_api.schemas.search import SearchRequest, SearchResponse
from wingsaver_api.services.search import SearchService

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search flights (server-side filter/sort/page)",
)
async def search_flights(
    body: SearchRequest,
    request: Request,
    response: Response,
    service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    result = await service.search(body, request_id=get_request_id(request))
    response.headers["X-Cache"] = result.cache
    return result
