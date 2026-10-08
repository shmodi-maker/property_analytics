"""
ListingTour Service

This module collects property data from the required APIs,
normalizes the data, and generates AI summaries using AWS Bedrock
for the ListingTour pages.
"""

import asyncio
import json

from app.services.listing_tour.api_client import ListingTourAPIClient
from app.services.listing_tour.bedrock_service import BedrockService
from app.services.listing_tour.normalizer import (
    normalize_card,
    normalize_price_history,
    normalize_pricing_data,
    normalize_facts,
    normalize_schools,
    normalize_home_card,
    normalize_lifestyle_data,
)


class ListingTourService:

    def __init__(self):
        self.api_client = ListingTourAPIClient()

    # ----------------- DATA COLLECTION -----------------

    # Page 1 "Pricing"
    async def get_pricing_data(
        self,
        listing_key: str,
    ) -> dict:
        """
        Collect pricing-related data for a listing.

        Card and price history are fetched concurrently because
        they are independent API requests.
        """

        card, price_history = await asyncio.gather(
            self.api_client.get_card(listing_key),
            self.api_client.get_price_history(listing_key),
        )

        return {
            "listing_key": listing_key,
            "card": card,
            "price_history": price_history,
        }

    # Page 2 "Why Buy Now?"
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

    # Page 3 "Schools"
    async def get_schools_data(
        self,
        listing_key: str,
    ) -> dict:
        """
        Fetch and normalize school information for a listing.

        This method prepares the school data used by the Page 3
        "Schools" AI summary.
        """

        schools = await self.api_client.get_schools(listing_key)

        return {
            "listing_key": listing_key,
            "schools": normalize_schools(schools),
        }

    # Page 4 "About This Home" 
    async def get_home_data(self, listing_key: str) -> dict:
        """
        Collect and normalize the Card API and Facts API data
        required for the Page 4 "About This Home" summary.
        """

        card, facts = await asyncio.gather(
            self.api_client.get_card(listing_key),
            self.api_client.get_facts(listing_key),
        )

        return {
            "listing_key": listing_key,
            "property": normalize_home_card(card),
            "facts": normalize_facts(facts),
        }

    
    async def get_lifestyle_data(self, listing_key: str) -> dict:
        """
        Collect and normalize all data required for Page 5
        "ZIP Code & Lifestyle".

        The listing's ZIP code comes from the Facts API. Once the ZIP
        code is known, the service fetches ZIP Insights and Housing
        Market Trends for that ZIP.
        """

        # Facts contains the ZIP code and Walk Score for the listing.
        facts, card = await asyncio.gather(
            self.api_client.get_facts(listing_key),
            self.api_client.get_card(listing_key),
        )

        normalized_facts = normalize_facts(facts)

        # Extract ZIP code from the normalized Facts response.
        zipcode = (
            card.get("zipcode")
            or card.get("zip")
        )

        if not zipcode:
            # Fallback to the raw response if normalize_facts does not
            # currently expose the ZIP code.
            zipcode = (
                facts.get("zipcode")
                or facts.get("postal_code")
                or facts.get("property", {}).get("zipcode")
            )

        if not zipcode:
            raise ValueError(
                f"ZIP code not available for listing {listing_key}"
            )

        # Fetch both ZIP-level APIs in parallel.
        zip_insights, housing_market = await asyncio.gather(
            self.api_client.get_zip_insights(str(zipcode)),
            self.api_client.get_housing_market_trends(str(zipcode)),
        )

        lifestyle = normalize_lifestyle_data(
            facts=normalized_facts,
            zip_insights=zip_insights,
            housing_market=housing_market,
        )

        return {
            "listing_key": listing_key,
            "lifestyle": lifestyle,
        }

    # ----------------- SUMMARY GENERATION -----------------

    # Page 2 "Why Buy Now?"
    async def generate_buy_now_summary(
        self,
        listing_key: str,
    ) -> str:
        """
        Generate the AI summary for Page 2: "Why Buy Now?"

        The method first collects the required property data and then
        sends the normalized data to the reusable Bedrock service.
        """

        # Fetch Card, Facts, and Projection data.
        data = await self.get_buy_now_data(listing_key)

        # Load the Page 2-specific prompt.
        bedrock = BedrockService()

        prompt_template = bedrock.load_prompt("buy_now.txt")

        # Insert the actual property data into the prompt.
        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(
                data,
                indent=2,
                default=str,
            ),
        )

        # Generate the final AI summary.
        response = bedrock.generate_summary(prompt)

        try:
            return json.loads(response)

        except json.JSONDecodeError:
            # Return the raw response if Bedrock did not return valid JSON.
            return {
                "headline": "Why Buy Now?",
                "summary": response,
                "projection_available": (
                    data.get("projection", {})
                    .get("projection_available", False)
                ),
            }

    # Page 3 "Schools"
    async def generate_schools_summary(
        self,
        listing_key: str,
    ) -> dict:
        """
        Generate the AI-powered Page 3 "Schools" summary.

        The method fetches normalized school data, inserts it into the
        schools prompt, sends the prompt to Bedrock, and parses the
        returned JSON.
        """

        # Fetch normalized school data.
        data = await self.get_schools_data(listing_key)

        # Load the Page 3-specific prompt.
        bedrock = BedrockService()

        prompt_template = bedrock.load_prompt("schools.txt")

        # Insert the school data into the prompt.
        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(
                data,
                indent=2,
                default=str,
            ),
        )

        # Generate the final AI summary.
        response = bedrock.generate_summary(prompt)

        try:
            return json.loads(response)

        except json.JSONDecodeError:
            # Return the raw response if Bedrock did not return valid JSON.
            return {
                "headline": "Schools",
                "summary": response,
            }

    # Page 4 "About This Home"
    async def generate_home_summary(
        self,
        listing_key: str,
    ) -> dict:
        """
        Generate the AI-powered Page 4 "About This Home" summary.

        The method fetches the Card and Facts APIs, normalizes
        the data, sends it to Bedrock, and parses the response.
        """

        data = await self.get_home_data(listing_key)

        bedrock = BedrockService()

        prompt_template = bedrock.load_prompt("home.txt")

        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(
                data,
                indent=2,
                default=str,
            ),
        )

        response = bedrock.generate_summary(prompt)

        try:
            return json.loads(response)

        except json.JSONDecodeError:
            return {
                "headline": "About This Home",
                "summary": response,
            }

    # Page 5 "ZIP Code and Lifestyle"
    # app/services/listing_tour/service.py

    async def generate_lifestyle_summary(self, listing_key: str) -> dict:
        """
        Generate the AI-powered Page 5 "ZIP Code & Lifestyle" summary.

        The method collects ZIP-level lifestyle, safety, and market data,
        inserts the normalized data into the lifestyle prompt, sends the
        prompt to Bedrock, and parses the returned JSON.
        """

        data = await self.get_lifestyle_data(listing_key)
  
        bedrock = BedrockService()

        prompt_template = bedrock.load_prompt("lifestyle.txt")

        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(data, indent=2, default=str),
        )

        response = bedrock.generate_summary(prompt)

        try:
            return json.loads(response)

        except json.JSONDecodeError:
            # Fallback if Bedrock returns plain text instead of JSON.
            return {
                "headline": "ZIP Code & Lifestyle",
                "summary": response,
            }