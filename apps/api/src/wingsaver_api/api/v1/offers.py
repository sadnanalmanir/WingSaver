"""Offer detail endpoint (store-only; no provider re-fetch)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from wingsaver_api.dependencies import get_search_service
from wingsaver_api.errors import AppError
from wingsaver_api.schemas.offer import OfferPublic
from wingsaver_api.services.search import SearchService

router = APIRouter()


@router.get(
    "/offers/{offer_id}",
    response_model=OfferPublic,
    summary="Get offer detail from local/Redis offer store",
)
async def get_offer(
    offer_id: str,
    service: Annotated[SearchService, Depends(get_search_service)],
) -> OfferPublic:
    offer = await service.get_offer(offer_id)
    if offer is None:
        raise AppError(
            code="OFFER_NOT_FOUND",
            message="Offer not found or expired. Search again.",
            status_code=404,
            details={"offer_id": offer_id},
        )
    return offer
