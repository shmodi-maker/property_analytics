"""
ListingTour Data Normalizer

This module converts raw responses from the external ListingTour APIs
into a smaller and consistent internal data structure.

The normalized data is used by the ListingTour service and eventually
provided to the Bedrock LLM for AI summary generation.
"""

from typing import Any


def normalize_card(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract the property information required by ListingTour
    from the raw Card API response.
    """

    events = data.get("events") or {}

    return {
        "listing_key": data.get("id"),
        "listing_id": data.get("listing_id"),
        "address": data.get("address"),
        "asking_price": data.get("price"),
        "beds": data.get("beds"),
        "baths": data.get("baths"),
        "sqft": data.get("sqft"),
        "city": data.get("city"),
        "state": data.get("state"),
        "zip": data.get("zip") or data.get("zipcode"),
        "property_type": data.get("property_type"),
        "property_class": data.get("property_class"),
        "status": data.get("standard_status"),
        "sold_price": data.get("sold_price"),
        "on_market_date": events.get("on_market_date"),
    }


def normalize_price_history(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract relevant price-history information from the raw
    Price History API response.
    """

    fields = {
        item.get("key"): item.get("value")
        for item in (
            data.get("listing_meta", {}).get("fields", [])
        )
    }

    return {
        "displayable": data.get("display_mode") != "hidden",
        "hidden_reason": data.get(
            "section_hidden_reason"
        ),
        "events": data.get("events", []),
        "events_total": data.get(
            "events_total",
            0,
        ),
        "close_date": fields.get("CloseDate"),
        "close_price": fields.get("ClosePrice"),
        "listing_contract_date": fields.get(
            "ListingContractDate"
        ),
        "listing_terms": fields.get("ListingTerms"),
        "off_market_days": fields.get(
            "OffMarketDays"
        ),
        "on_market_date": fields.get(
            "OnMarketDate"
        ),
        "original_on_market_date": fields.get(
            "OriginalOnMarketDate"
        ),
    }


def normalize_pricing_data(
    card: dict[str, Any],
    price_history: dict[str, Any],
) -> dict[str, Any]:
    """
    Combine the normalized Card and Price History data into
    the internal structure used by the Page 1 pricing summary.

    Estimate and comparable-sales data will be added once the
    required authentication for that API is available.
    """

    return {
        "property": normalize_card(card),
        "price_history": normalize_price_history(
            price_history
        ),
        "estimate": None,
        "comparable_sales": [],
    }

def normalize_facts(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize the raw Facts API response.

    The Facts API contains many property attributes organized
    into sections. This function extracts the fields that are
    useful for ListingTour summaries while preserving the
    original unit information and public remarks.
    """

    # Flatten all section fields into a key-value dictionary.
    # Example:
    # "CapRate" -> "3.41"
    # "NumberOfUnitsTotal" -> "4"
    fields = {}

    for section in data.get("sections", []):
        for field in section.get("fields", []):
            key = field.get("key")

            if key:
                fields[key] = field.get("value")

    # Extract individual property units separately because
    # they contain structured information about each unit.
    units = []

    for section in data.get("sections", []):
        if section.get("id") != "property_units":
            continue

        for field in section.get("fields", []):
            units.append({
                "unit": field.get("label"),
                "details": field.get("value"),
            })

    # Values displayed separately by the API.
    fact_display = data.get("fact_display", {})

    return {
        "listing_key": data.get("listing_key_numeric"),

        # Public MLS remarks about the property.
        "remarks": data.get("remarks", {}).get("public"),

        # Basic property information.
        "property_type": fields.get("PropertyType"),
        "property_sub_type": fields.get("PropertySubType"),
        "stories": fields.get("Stories"),

        # Investment-related information.
        "cap_rate": fields.get("CapRate"),
        "total_units": fields.get("NumberOfUnitsTotal"),
        "leased_units": fields.get("NumberOfUnitsLeased"),
        "number_of_buildings": fields.get("NumberOfBuildings"),

        # Physical property information.
        "lot_size": fields.get("LotSizeSquareFeet"),
        "zoning": fields.get("Zoning"),
        "year_built": fact_display.get("YearBuilt"),

        # Financial/property cost information.
        "tax_annual_amount": fact_display.get(
            "TaxAnnualAmount"
        ),
        "price_per_sqft": fact_display.get(
            "ComputedPricePerSqFt"
        ),

        # Parking information.
        "parking_total": fields.get("ParkingTotal"),
        "parking_features": fields.get("ParkingFeatures"),
        "garage_spaces": fields.get("GarageSpaces"),
        "carport_spaces": fields.get("CarportSpaces"),

        # Property comfort/features.
        "heating": fields.get("Heating"),
        "cooling": fields.get("Cooling"),

        # Utilities.
        "utilities": fields.get("Utilities"),
        "water_source": fields.get("WaterSource"),
        "sewer": fields.get("Sewer"),
        "gas": fields.get("Gas"),

        # Community information.
        "hoa": fields.get("AssociationYN"),
        "lease_term": fields.get("LeaseTerm"),
        "walk_score": fields.get("WalkScore"),

        # Individual rental units.
        "units": units,
    }