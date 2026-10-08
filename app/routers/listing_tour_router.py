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


# @router.get("/{listing_key}/pricing-data")
# async def get_pricing_data(
#     listing_key: str,
# ):
#     """
#     Return normalized property data required for the
#     Page 1 "Is it priced right?" summary.
#     """

#     try:
#         service = ListingTourService()

#         return await service.get_pricing_data(
#             listing_key
#         )

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=str(e),
#         )

# @router.get("/{listing_key}/buy-now-data")
# async def get_buy_now_data(
#     listing_key: str,
# ):
#     """
#     Return the normalized data used to generate the
#     Page 2 "Why Buy Now?" summary.

#     This endpoint is currently used to verify the
#     upstream APIs before integrating Bedrock.
#     """

#     try:
#         service = ListingTourService()

#         return await service.get_buy_now_data(
#             listing_key
#         )

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=str(e),
#         )

# @router.get("/{listing_key}/schools-data")
# async def get_schools_data(listing_key: str):
#     """
#     Temporary endpoint used to inspect the raw Schools API response.

#     This endpoint is for development/testing and can be removed after
#     the schools response structure has been confirmed.
#     """
#     try:
#         service = ListingTourService()
#         return await service.get_schools_data(listing_key)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.get("/{listing_key}/buy-now-summary")
async def get_buy_now_summary(
    listing_key: str,
):
    """
    Generate the AI-powered "Why Buy Now?" summary
    for the requested listing.
    """

    try:
        service = ListingTourService()

        return {
            "listing_key": listing_key,
            "page": 2,
            "summary": await service.generate_buy_now_summary(
                listing_key
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

@router.get("/{listing_key}/schools-summary")
async def get_schools_summary(listing_key: str):
    """
    Generate the AI-powered Page 3 "Schools" summary.
    """
    try:
        service = ListingTourService()

        return {
            "listing_key": listing_key,
            "page": 3,
            "summary": await service.generate_schools_summary(listing_key),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

@router.get("/{listing_key}/home-summary")
async def get_home_summary(
    listing_key: str,
):
    """
    Generate the AI-powered Page 4
    "About This Home" summary.
    """

    try:
        service = ListingTourService()

        return {
            "listing_key": listing_key,
            "page": 4,
            "summary": await service.generate_home_summary(
                listing_key
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

# app/routers/listing_tour_router.py

@router.get("/{listing_key}/lifestyle-summary")
async def get_lifestyle_summary(listing_key: str):
    """
    Generate the AI-powered Page 5
    "ZIP Code & Lifestyle" summary.
    """

    try:
        service = ListingTourService()

        return {
            "listing_key": listing_key,
            "page": 5,
            "summary": await service.generate_lifestyle_summary(
                listing_key
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    