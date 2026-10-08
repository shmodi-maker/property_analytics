"""
ListingTour API Client

This module handles communication between the ListingTour service
and the external APIs used to collect property data.

It keeps external API communication separate from the business logic
and applies authentication only to APIs that require it.
"""

import httpx

from app.config import (
    LISTING_TOUR_API_BASE_URL_1,
    LISTING_TOUR_API_BASE_URL_2,
    JAINAM_API_TOKEN,
    PROJECTION_API_KEY,
)


class ListingTourAPIClient:

    def __init__(self):
        self.base_url_1 = LISTING_TOUR_API_BASE_URL_1
        self.base_url_2 = LISTING_TOUR_API_BASE_URL_2

    # ---------------------------------------------------------
    # Jainam APIs - NO AUTH
    # ---------------------------------------------------------

    async def get_card(
        self,
        listing_key: str,
    ) -> dict:

        url = (
            f"{self.base_url_2}"
            f"/api/idx/v1/listings/{listing_key}/card/"
        )

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(url)

        response.raise_for_status()

        return response.json()

    async def get_price_history(
        self,
        listing_key: str,
    ) -> dict:

        url = (
            f"{self.base_url_2}"
            f"/api/idx/v1/listings/{listing_key}/price-history/"
        )

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(url)

        response.raise_for_status()

        return response.json()

    # ---------------------------------------------------------
    # Jainam Estimate API - AUTH REQUIRED
    # ---------------------------------------------------------

    async def get_estimate(
        self,
        listing_key: str,
    ) -> dict:

        if not JAINAM_API_TOKEN:
            raise RuntimeError(
                "JAINAM_API_TOKEN is not configured"
            )

        url = (
            f"{self.base_url_2}"
            f"/api/client/my-home-estimate/"
        )

        params = {
            "selection": f"idx:{listing_key}",
            "detail": "core",
        }

        headers = {
            "Authorization": f"Bearer {JAINAM_API_TOKEN}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(
                url,
                params=params,
                headers=headers,
            )

        response.raise_for_status()

        return response.json()

    # ---------------------------------------------------------
    # Our Projection API - API KEY REQUIRED
    # ---------------------------------------------------------

    async def get_projection(
        self,
        listing_key: str,
    ) -> dict:

        if not PROJECTION_API_KEY:
            raise RuntimeError(
                "PROJECTION_API_KEY is not configured"
            )

        url = (
            f"{self.base_url_1}"
            f"/api/v1/projection/listing/{listing_key}"
        )

        headers = {
            "x-api-key": PROJECTION_API_KEY,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:

            response = await client.get(
                url,
                headers=headers,
            )

        response.raise_for_status()

        return response.json()

    async def get_facts(
        self,
        listing_key: str,
    ) -> dict:
        """
        Fetch property facts required by the ListingTour pages.

        This endpoint provides additional property-level facts that
        are not necessarily included in the Card API response.
        """

        url = (
            f"{self.base_url_2}"
            f"/api/idx/v1/listings/{listing_key}/facts/"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)

        response.raise_for_status()

        return response.json()