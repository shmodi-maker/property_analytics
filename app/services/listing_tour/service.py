"""
ListingTour Service

This module contains the business logic for the ListingTour feature.

It coordinates:
- Fetching data from external APIs
- Running API requests in parallel where appropriate
- Normalizing the returned data
- Preparing the data for AI summary generation

Bedrock and database functionality will be integrated into this
service as the ListingTour implementation progresses.
"""


import asyncio

from app.services.listing_tour.api_client import (
    ListingTourAPIClient,
)
from app.services.listing_tour.normalizer import (
    normalize_card,
    normalize_facts,
    normalize_pricing_data,
)

class ListingTourService:

    def __init__(self):

        self.api_client = ListingTourAPIClient()

    async def get_pricing_data(
        self,
        listing_key: str,
    ) -> dict:

        card, price_history = await asyncio.gather(
            self.api_client.get_card(listing_key),
            self.api_client.get_price_history(listing_key),
        )

        return {
            "listing_key": listing_key,
            "card": card,
            "price_history": price_history,
        }
    async def get_buy_now_data(
        self,
        listing_key: str,
    ) -> dict:
        """
        Collect all data required for the Page 2
        "Why Buy Now?" summary.

        Card, Facts, and Five-Year Projection are independent
        API requests, so they are fetched concurrently.
        """

        card, facts, projection = await asyncio.gather(
            self.api_client.get_card(listing_key),
            self.api_client.get_facts(listing_key),
            self.api_client.get_projection(listing_key),
        )

        return {
            "listing_key": listing_key,
            "property": normalize_card(card),
            "facts": normalize_facts(facts),
            "projection": projection,
        }