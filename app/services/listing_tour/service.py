
"""
ListingTour Service

Collects property data from upstream APIs, normalizes it, generates
AI summaries through AWS Bedrock, and caches successful summaries
in PostgreSQL for seven days.
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Awaitable

from app.config import BEDROCK_MODEL_ID
from app.repositories.listing_tour_repository import (
    get_fresh_summary,
    save_summary,
)
from app.services.listing_tour.api_client import ListingTourAPIClient
from app.services.listing_tour.bedrock_service import BedrockService
from app.services.listing_tour.normalizer import (
    normalize_card,
    normalize_pricing_data,
    normalize_facts,
    normalize_schools,
    normalize_home_card,
    normalize_lifestyle_data,
)

logger = logging.getLogger(__name__)


class ListingTourService:
    """Collect listing data and generate cached ListingTour summaries."""

    def __init__(self):
        self.api_client = ListingTourAPIClient()

    # ---------------------------------------------------------
    # SUMMARY CACHE
    # ---------------------------------------------------------

    
    
    async def _get_or_generate_summary(
        self,
        listing_key: str,
        page_number: int,
        generator: Callable[[str], Awaitable[Any]],
    ) -> Any:
        """
        Return a fresh cached summary or generate a new one.

        If the cache database is unavailable, generate the summary
        normally rather than failing solely because caching failed.
        """

        # Try reading the cache; continue without it if PostgreSQL fails.
        start = time.perf_counter()

        try:
            cached_summary = get_fresh_summary(
                listing_key=listing_key,
                page_number=page_number,
            )
        except Exception:
            logger.exception(
                "Cache read failed for listing=%s page=%s",
                listing_key,
                page_number,
            )
            cached_summary = None

        elapsed = time.perf_counter() - start
       
        if cached_summary is not None:
            logger.info(
                "ListingTour cache HIT: listing=%s page=%s",
                listing_key,
                page_number,
            )
            return cached_summary

        logger.info(
            "ListingTour cache MISS/STALE: listing=%s page=%s",
            listing_key,
            page_number,
        )

        # If generation fails, the previous cached record is not overwritten.
        summary = await generator(listing_key)

        # Cache persistence is best-effort; return the generated result
        # even if saving it to PostgreSQL fails.
        try:
            save_summary(
                listing_key=listing_key,
                page_number=page_number,
                summary=summary,
                model_name=BEDROCK_MODEL_ID,
                prompt_version=f"page-{page_number}-v1",
            )
        except Exception:
            logger.exception(
                "Cache save failed for listing=%s page=%s",
                listing_key,
                page_number,
            )

        return summary



    # ---------------------------------------------------------
    # PUBLIC SUMMARY METHODS USED BY THE ROUTER
    # ---------------------------------------------------------

    async def generate_pricing_summary(self, listing_key: str) -> dict:
        """Return the cached or newly generated Page 1 pricing summary."""
        return await self._get_or_generate_summary(
            listing_key,
            1,
            self._generate_pricing_summary_uncached,
        )

    async def generate_buy_now_summary(self, listing_key: str) -> dict:
        """Return the cached or newly generated Page 2 summary."""
        return await self._get_or_generate_summary(
            listing_key,
            2,
            self._generate_buy_now_summary_uncached,
        )

    async def generate_schools_summary(self, listing_key: str) -> dict:
        """Return the cached or newly generated Page 3 schools summary."""
        return await self._get_or_generate_summary(
            listing_key,
            3,
            self._generate_schools_summary_uncached,
        )

    async def generate_home_summary(self, listing_key: str) -> dict:
        """Return the cached or newly generated Page 4 home summary."""
        return await self._get_or_generate_summary(
            listing_key,
            4,
            self._generate_home_summary_uncached,
        )

    async def generate_lifestyle_summary(self, listing_key: str) -> dict:
        """Return the cached or newly generated Page 5 lifestyle summary."""
        return await self._get_or_generate_summary(
            listing_key,
            5,
            self._generate_lifestyle_summary_uncached,
        )

    # ---------------------------------------------------------
    # PAGE 1: PRICING DATA
    # ---------------------------------------------------------

    async def get_pricing_data(self, listing_key: str) -> dict:
        """
        Fetch and normalize the card, price history, and estimate data
        required for the Page 1 pricing summary.
        """

        card, price_history, estimate_response = await asyncio.gather(
            self.api_client.get_card(listing_key),
            self.api_client.get_price_history(listing_key),
            self.api_client.get_estimate(listing_key),
        )

        return normalize_pricing_data(
            card=card,
            price_history=price_history,
            estimate_response=estimate_response,
        )

    # ---------------------------------------------------------
    # PAGE 2: WHY BUY NOW? DATA
    # ---------------------------------------------------------

    async def get_buy_now_data(self, listing_key: str) -> dict:
        """Fetch the card, facts, and projection data for Page 2."""

        tasks = {
            "card": self.api_client.get_card,
            "facts": self.api_client.get_facts,
            "projection": self.api_client.get_projection,
        }

        results = {}

        for name, api_method in tasks.items():
            try:
                results[name] = await api_method(listing_key)
                logger.info("ListingTour %s API succeeded", name)
            except Exception:
                logger.exception("ListingTour %s API failed", name)
                raise

        return {
            "listing_key": listing_key,
            "property": normalize_card(results["card"]),
            "facts": normalize_facts(results["facts"]),
            "projection": results["projection"],
        }

    # ---------------------------------------------------------
    # PAGE 3: SCHOOLS DATA
    # ---------------------------------------------------------

    async def get_schools_data(self, listing_key: str) -> dict:
        """Fetch and normalize school information for Page 3."""

        schools = await self.api_client.get_schools(listing_key)

        return {
            "listing_key": listing_key,
            "schools": normalize_schools(schools),
        }

    # ---------------------------------------------------------
    # PAGE 4: ABOUT THIS HOME DATA
    # ---------------------------------------------------------

    async def get_home_data(self, listing_key: str) -> dict:
        """Fetch and normalize property card and facts data for Page 4."""

        card, facts = await asyncio.gather(
            self.api_client.get_card(listing_key),
            self.api_client.get_facts(listing_key),
        )

        return {
            "listing_key": listing_key,
            "property": normalize_home_card(card),
            "facts": normalize_facts(facts),
        }

    # ---------------------------------------------------------
    # PAGE 5: ZIP CODE AND LIFESTYLE DATA
    # ---------------------------------------------------------

    async def get_lifestyle_data(self, listing_key: str) -> dict:
        """
        Fetch listing facts and card data, identify the ZIP code,
        then fetch ZIP Insights and housing market trends.
        """

        facts, card = await asyncio.gather(
            self.api_client.get_facts(listing_key),
            self.api_client.get_card(listing_key),
        )

        normalized_facts = normalize_facts(facts)

        # First try the normalized card response.
        zipcode = card.get("zipcode") or card.get("zip")

        # Fall back to the raw Facts API response if needed.
        if not zipcode:
            zipcode = (
                facts.get("zipcode")
                or facts.get("postal_code")
                or facts.get("property", {}).get("zipcode")
            )

        if not zipcode:
            raise ValueError(
                f"ZIP code not available for listing {listing_key}"
            )

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

    # ---------------------------------------------------------
    # PAGE 1: GENERATE PRICING SUMMARY
    # ---------------------------------------------------------

    async def _generate_pricing_summary_uncached(
        self,
        listing_key: str,
    ) -> dict:
        """Generate the Page 1 pricing summary without using the cache."""

        data = await self.get_pricing_data(listing_key)

        bedrock = BedrockService()
        prompt_template = bedrock.load_prompt("pricing.txt")

        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(data, indent=2, default=str),
        )

        response = bedrock.generate_summary(prompt)

        try:
            result = json.loads(response)

            if not isinstance(result, dict):
                raise ValueError(
                    "Pricing summary must be a JSON object"
                )

            return result

        except json.JSONDecodeError:
            return {
                "headline": "How the Asking Price Compares",
                "summary": response,
            }

    # ---------------------------------------------------------
    # PAGE 2: GENERATE WHY BUY NOW? SUMMARY
    # ---------------------------------------------------------

    async def _generate_buy_now_summary_uncached(
        self,
        listing_key: str,
    ) -> dict:
        """Generate the Page 2 summary without using the cache."""

        data = await self.get_buy_now_data(listing_key)

        bedrock = BedrockService()
        prompt_template = bedrock.load_prompt("buy_now.txt")

        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(data, indent=2, default=str),
        )

        response = bedrock.generate_summary(prompt)

        try:
            result = json.loads(response)

            if isinstance(result, dict):
                return result

            return {
                "headline": "Why Buy Now?",
                "summary": result,
                "projection_available": (
                    data.get("projection", {}).get(
                        "projection_available",
                        False,
                    )
                ),
            }

        except json.JSONDecodeError:
            return {
                "headline": "Why Buy Now?",
                "summary": response,
                "projection_available": (
                    data.get("projection", {}).get(
                        "projection_available",
                        False,
                    )
                ),
            }

    # ---------------------------------------------------------
    # PAGE 3: GENERATE SCHOOLS SUMMARY
    # ---------------------------------------------------------

    async def _generate_schools_summary_uncached(
        self,
        listing_key: str,
    ) -> dict:
        """Generate the Page 3 schools summary without using the cache."""

        data = await self.get_schools_data(listing_key)

        bedrock = BedrockService()
        prompt_template = bedrock.load_prompt("schools.txt")

        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(data, indent=2, default=str),
        )

        response = bedrock.generate_summary(prompt)

        try:
            result = json.loads(response)

            if isinstance(result, dict):
                return result

            return {
                "headline": "Schools",
                "summary": result,
            }

        except json.JSONDecodeError:
            return {
                "headline": "Schools",
                "summary": response,
            }

    # ---------------------------------------------------------
    # PAGE 4: GENERATE ABOUT THIS HOME SUMMARY
    # ---------------------------------------------------------

    async def _generate_home_summary_uncached(
        self,
        listing_key: str,
    ) -> dict:
        """Generate the Page 4 home summary without using the cache."""

        data = await self.get_home_data(listing_key)

        bedrock = BedrockService()
        prompt_template = bedrock.load_prompt("home.txt")

        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(data, indent=2, default=str),
        )

        response = bedrock.generate_summary(prompt)

        try:
            result = json.loads(response)

            if isinstance(result, dict):
                return result

            return {
                "headline": "About This Home",
                "summary": result,
            }

        except json.JSONDecodeError:
            return {
                "headline": "About This Home",
                "summary": response,
            }

    # ---------------------------------------------------------
    # PAGE 5: GENERATE LIFESTYLE SUMMARY
    # ---------------------------------------------------------

    async def _generate_lifestyle_summary_uncached(
        self,
        listing_key: str,
    ) -> dict:
        """Generate the Page 5 lifestyle summary without using the cache."""

        data = await self.get_lifestyle_data(listing_key)

        bedrock = BedrockService()
        prompt_template = bedrock.load_prompt("lifestyle.txt")

        prompt = prompt_template.replace(
            "{{PROPERTY_DATA}}",
            json.dumps(data, indent=2, default=str),
        )

        response = bedrock.generate_summary(prompt)

        try:
            result = json.loads(response)

            if isinstance(result, dict):
                return result

            return {
                "headline": "ZIP Code & Lifestyle",
                "summary": result,
            }

        except json.JSONDecodeError:
            return {
                "headline": "ZIP Code & Lifestyle",
                "summary": response,
            }
