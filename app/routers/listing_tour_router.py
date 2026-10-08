"""
ListingTour Router

This module defines the HTTP endpoints exposed by the ListingTour
feature.

The router receives requests from the frontend and delegates the
actual business logic to ListingTourService.
"""

from fastapi import APIRouter, HTTPException

from app.services.listing_tour.service import (
    ListingTourService,
)


router = APIRouter(
    prefix="/api/v1/listing-tour",
    tags=["ListingTour"],
)


@router.get("/{listing_key}/pricing-data")
async def get_pricing_data(
    listing_key: str,
):
    """
    Return normalized property data required for the
    Page 1 "Is it priced right?" summary.
    """

    try:
        service = ListingTourService()

        return await service.get_pricing_data(
            listing_key
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

@router.get("/{listing_key}/buy-now-data")
async def get_buy_now_data(
    listing_key: str,
):
    """
    Return the normalized data used to generate the
    Page 2 "Why Buy Now?" summary.

    This endpoint is currently used to verify the
    upstream APIs before integrating Bedrock.
    """

    try:
        service = ListingTourService()

        return await service.get_buy_now_data(
            listing_key
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )