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
    fields = {}

    for section in data.get("sections", []):
        for field in section.get("fields", []):
            key = field.get("key")

            if key:
                fields[key] = field.get("value")

    # Extract individual property units separately.
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

    # Normalize fireplace count because the API returns it as a string.
    
    fireplace_count = fields.get("FireplacesTotal")
    try:
        fireplace_count_number = int(fireplace_count)
    except (TypeError, ValueError):
        fireplace_count_number = 0

    return {
        "listing_key": data.get("listing_key_numeric"),

        # ---------------------------------------------------------
        # Public MLS remarks
        # ---------------------------------------------------------
        "remarks": data.get("remarks", {}).get("public"),

        # ---------------------------------------------------------
        # Basic property information
        # ---------------------------------------------------------
        "property_type": fields.get("PropertyType"),
        "property_sub_type": fields.get("PropertySubType"),
        "stories": fields.get("Stories"),
        "new_construction": fields.get("NewConstructionYN"),

        # ---------------------------------------------------------
        # Size / lot information
        # ---------------------------------------------------------
        "lot_size": fields.get("LotSizeSquareFeet"),
        "zoning": fields.get("Zoning"),

        # ---------------------------------------------------------
        # Beds / bathrooms
        # ---------------------------------------------------------
        "bedrooms": fields.get("BedroomsTotal"),
        "full_bathrooms": fields.get("BathroomsFull"),
        "half_bathrooms": fields.get("BathroomsHalf"),

        # ---------------------------------------------------------
        # Kitchen
        # ---------------------------------------------------------
        "kitchen": {
            "features": fields.get("RoomKitchenFeatures"),
            "appliances": fields.get("Appliances"),
        },

        # ---------------------------------------------------------
        # Bedroom features
        # ---------------------------------------------------------
        "bedroom_features": fields.get("RoomBedroomFeatures"),

        # ---------------------------------------------------------
        # Living / dining areas
        # ---------------------------------------------------------
        "dining": fields.get("RoomDiningFeatures"),
        "family_room": fields.get("RoomFamilyRoomFeatures"),

        # ---------------------------------------------------------
        # Laundry
        # ---------------------------------------------------------
        "laundry": fields.get("LaundryFeatures"),

        # ---------------------------------------------------------
        # Fireplace
        # ---------------------------------------------------------
        "fireplace": {
            "exists": fireplace_count_number > 0,
            "count": fireplace_count,
            "features": fields.get("FireplaceFeatures"),
        },

        # ---------------------------------------------------------
        # Interior / comfort features
        # ---------------------------------------------------------
        "interior_features": fields.get("InteriorFeatures"),
        "flooring": fields.get("Flooring"),
        "heating": fields.get("Heating"),
        "cooling": fields.get("Cooling"),

        # ---------------------------------------------------------
        # Exterior
        # ---------------------------------------------------------
        "exterior_features": fields.get("PatioAndPorchFeatures"),

        # ---------------------------------------------------------
        # Parking / garage
        # ---------------------------------------------------------
        "parking_total": fields.get("ParkingTotal"),
        "parking_features": fields.get("ParkingFeatures"),
        "garage_spaces": fields.get("GarageSpaces"),
        "garage": fields.get("GarageYN"),
        "carport_spaces": fields.get("CarportSpaces"),
        "carport": fields.get("CarportYN"),

        # ---------------------------------------------------------
        # Construction
        # ---------------------------------------------------------
        "foundation": fields.get("FoundationDetails"),
        "roof": fields.get("Roof"),

        # ---------------------------------------------------------
        # Utilities
        # ---------------------------------------------------------
        "utilities": fields.get("Utilities"),
        "water_source": fields.get("WaterSource"),
        "sewer": fields.get("Sewer"),
        "gas": fields.get("Gas"),

        # ---------------------------------------------------------
        # Community / HOA
        # ---------------------------------------------------------
        "hoa": fields.get("AssociationYN"),
        "hoa_fee": fields.get("AssociationFee"),
        "hoa_fee_frequency": fields.get("AssociationFeeFrequency"),
        "hoa_amenities": fields.get("AssociationAmenities"),

        # ---------------------------------------------------------
        # Community information
        # ---------------------------------------------------------
        "lease_term": fields.get("LeaseTerm"),
        "total_units": fields.get("NumberOfUnitsTotal"),
        "leased_units": fields.get("NumberOfUnitsLeased"),
        "number_of_buildings": fields.get("NumberOfBuildings"),

        # ---------------------------------------------------------
        # Location
        # ---------------------------------------------------------
        "zipcode": (
            fields.get("PostalCode")
            or fields.get("PostalCodeFull")
            or data.get("zipcode")
            ),
        "walk_score": fields.get("WalkScore"),

        # ---------------------------------------------------------
        # Investment-related information
        # ---------------------------------------------------------
        "cap_rate": fields.get("CapRate"),

        # ---------------------------------------------------------
        # Display information
        # ---------------------------------------------------------
        "year_built": fact_display.get("YearBuilt"),
        "price_per_sqft": fact_display.get(
            "ComputedPricePerSqFt"
        ),
        "tax_annual_amount": fact_display.get(
            "TaxAnnualAmount"
        ),
        "county": fact_display.get("CountyOrParish"),

        # ---------------------------------------------------------
        # Individual rental/property units
        # ---------------------------------------------------------
        "units": units,

        # ---------------------------------------------------------
        # Display policy
        # ---------------------------------------------------------
        "display_policy": {
            "avm_display_allowed": data.get(
                "display_policy", {}
            ).get("avm_display_allowed"),

            "consumer_comment_allowed": data.get(
                "display_policy", {}
            ).get("consumer_comment_allowed"),
        },
    }

def normalize_schools(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize the raw Schools API response.

    This keeps only the school information needed by the ListingTour
    AI summary and removes large nested NCES/source-data objects that
    are not needed by Bedrock.
    """
    normalized_tiers = []

    for tier in data.get("tiers", []):
        schools = []

        for school in tier.get("schools", []):
            schools.append({
                "name": school.get("school_name") or school.get("name"),
                "level": school.get("school_level"),
                "address": school.get("address"),
                "distance_miles": school.get("distance_miles"),
                "rating": school.get("rating"),
                "school_sector": school.get("school_sector"),
                "education_type": school.get("education_type"),
                "grades_offered": school.get("grades_offered"),
                "district_name": school.get("district_name"),
                "county": data.get("mls", {}).get("county"),
                "match_status": school.get("match_status"),
            })

        normalized_tiers.append({
            "level": tier.get("level"),
            "label": tier.get("label"),
            "mode": tier.get("mode"),
            "schools": schools,
        })

    return {
        "listing_key": data.get("listing_key_numeric"),
        "zipcode": data.get("zipcode"),
        "resolution_mode": data.get("mode"),
        "districts": {
            "elementary": data.get("mls", {}).get("elementary_district"),
            "high_school": data.get("mls", {}).get("high_school_district"),
        },
        "county": data.get("mls", {}).get("county"),
        "tiers": normalized_tiers,
    }

# Normalize home details has to be added here but check normalize facts() before adding it
def normalize_home_card(
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize the Card API response for the Page 4
    "About This Home" summary.

    This keeps the listing-level information needed by Bedrock
    and removes the large image URL list.
    """

    # Collect unique photo categories.
    photo_categories = []

    for media in data.get("media", []):
        category = (
            media.get("image_of_display")
            or media.get("label")
            or media.get("image_of")
        )

        if category and category not in photo_categories:
            photo_categories.append(category)

    return {
        "listing_key": data.get("id"),
        "listing_id": data.get("listing_id"),
        "address": data.get("address"),
        "price": data.get("price"),
        "beds": data.get("beds"),
        "baths": data.get("baths"),
        "sqft": data.get("sqft"),
        "city": data.get("city"),
        "state": data.get("state"),
        "zipcode": data.get("zipcode") or data.get("zip"),
        "standard_status": data.get("standard_status"),
        "property_type": data.get("property_type"),
        "property_class": data.get("property_class"),

        # We only send the photo count and categories to Bedrock.
        # The frontend handles the actual images.
        "media": {
            "photos_count": data.get("photos_count"),
            "categories": photo_categories,
        },
    }

# app/services/listing_tour/normalizer.py

def normalize_lifestyle_data(
    facts: dict[str, Any],
    zip_insights: dict[str, Any],
    housing_market: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize all Page 5 ZIP-code and lifestyle information.

    The source APIs return a large amount of data, including long
    historical series and property-sale records. This function keeps
    only the fields required for the ListingTour AI summary.

    The normalized structure contains:
    - ZIP code
    - Walk Score
    - lifestyle indices
    - crime and safety information
    - housing-market KPIs
    - latest price-per-square-foot information
    """

    crime = zip_insights.get("crime_rate", {})

    location_summary = housing_market.get("location_summary", {})
    kpis = location_summary.get("kpis", [])
    chart = location_summary.get("chart", {})
    indices = location_summary.get("indices", [])
    zipcode_metrics = housing_market.get("zipcode_metrics", {})

    # Convert the KPI list into a simple dictionary.
    market_kpis = {}

    for kpi in kpis:
        kpi_id = kpi.get("id")

        if kpi_id:
            market_kpis[kpi_id] = {
                "title": kpi.get("title"),
                "value": kpi.get("value"),
                "delta": kpi.get("delta"),
                "up": kpi.get("up"),
            }

    # Convert the index list into a simple dictionary.
    lifestyle_indices = {}

    for index in indices:
        index_id = index.get("id")

        if index_id:
            lifestyle_indices[index_id] = {
                "label": index.get("label"),
                "score": index.get("score"),
                "status": index.get("status"),
                "confidence": index.get("confidence"),
                "is_estimated": index.get("is_estimated"),
            }

    # Get the latest price-per-square-foot value from the chart.
    latest_price_per_sqft = None

    labels = chart.get("labels", [])
    values = chart.get("values", [])

    if labels and values and len(labels) == len(values):
        latest_price_per_sqft = {
            "period": labels[-1],
            "value": values[-1],
        }

    # Walk Score is supplied by the Facts API.
    walk_score = None

    # The exact location of Walk Score can vary in the Facts response,
    # so first check the normalized facts structure.
    if isinstance(facts, dict):
        walk_score = facts.get("walk_score")

        if walk_score is None:
            location = facts.get("location")

            if isinstance(location, dict):
                walk_score = location.get("walk_score")

    return {
        "zipcode": zip_insights.get("zipcode")
        or housing_market.get("zipcode"),

        "walk_score": walk_score,

        "lifestyle_indices": lifestyle_indices,

        "crime": {
            "crime_index": crime.get("index"),
            "crime_level": crime.get("level"),
            "safety_score_0_100": crime.get("safety_score_0_100"),
            "safety_index_10": crime.get("safety_index_10"),
            "three_year_change_pct": crime.get("three_year_change_pct"),
            "most_common_offense": crime.get("most_common_offense"),
            "top_three_offenses": [
                {
                    "type": offense.get("type"),
                    "share_pct": offense.get("share_pct"),
                }
                for offense in crime.get("top_three_offenses", [])
            ],
        },

        "market": {
            "listed_houses": market_kpis.get("listed"),
            "pending_houses": market_kpis.get("pending"),
            "just_sold_30_days": market_kpis.get("sold30"),
            "average_days_on_market": market_kpis.get("dom"),

            "median_estimated_market_value": zipcode_metrics.get(
                "median_est_market_value"
            ),

            "median_price_per_sqft": zipcode_metrics.get(
                "median_price_per_sqft"
            ),

            "latest_average_price_per_sqft": latest_price_per_sqft,
        },

        "as_of": location_summary.get("meta", {}).get("as_of")
        or housing_market.get("as_of"),
    }
