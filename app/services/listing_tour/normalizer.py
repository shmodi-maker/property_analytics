"""
ListingTour Data Normalizer

This module converts raw responses from the external ListingTour APIs
into a smaller and consistent internal data structure.

The normalized data is used by the ListingTour service and eventually
provided to the Bedrock LLM for AI summary generation.
"""

from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    """Return value if it is a dictionary; otherwise return an empty dictionary."""
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    """Return value if it is a list; otherwise return an empty list."""
    return value if isinstance(value, list) else []


def normalize_card(data: dict[str, Any]) -> dict[str, Any]:
    """Extract the property information required from the raw Card API response."""
    data = _as_dict(data)
    events = _as_dict(data.get("events"))

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


def normalize_price_history(data: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant price-history information from the raw API response."""
    data = _as_dict(data)
    listing_meta = _as_dict(data.get("listing_meta"))
    fields_list = _as_list(listing_meta.get("fields"))
    fields = {
        item.get("key"): item.get("value")
        for item in fields_list
        if isinstance(item, dict) and item.get("key")
    }

    return {
        "displayable": data.get("display_mode") != "hidden",
        "hidden_reason": data.get("section_hidden_reason"),
        "events": _as_list(data.get("events")),
        "events_total": data.get("events_total", 0),
        "close_date": fields.get("CloseDate"),
        "close_price": fields.get("ClosePrice"),
        "listing_contract_date": fields.get("ListingContractDate"),
        "listing_terms": fields.get("ListingTerms"),
        "off_market_days": fields.get("OffMarketDays"),
        "on_market_date": fields.get("OnMarketDate"),
        "original_on_market_date": fields.get("OriginalOnMarketDate"),
    }


def normalize_facts(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize the raw Facts API response into useful property attributes."""
    data = _as_dict(data)
    sections = _as_list(data.get("sections"))
    fields: dict[str, Any] = {}

    # Flatten section fields while ignoring malformed section/field entries.
    for section in sections:
        if not isinstance(section, dict):
            continue
        for field in _as_list(section.get("fields")):
            if not isinstance(field, dict):
                continue
            key = field.get("key")
            if key:
                fields[key] = field.get("value")

    # Extract individual property units separately.
    units = []
    for section in sections:
        if not isinstance(section, dict) or section.get("id") != "property_units":
            continue
        for field in _as_list(section.get("fields")):
            if isinstance(field, dict):
                units.append({"unit": field.get("label"), "details": field.get("value")})

    fact_display = _as_dict(data.get("fact_display"))
    remarks = _as_dict(data.get("remarks"))
    display_policy = _as_dict(data.get("display_policy"))

    fireplace_count = fields.get("FireplacesTotal")
    try:
        fireplace_count_number = int(fireplace_count)
    except (TypeError, ValueError):
        fireplace_count_number = 0

    return {
        "listing_key": data.get("listing_key_numeric"),
        "remarks": remarks.get("public"),
        "property_type": fields.get("PropertyType"),
        "property_sub_type": fields.get("PropertySubType"),
        "stories": fields.get("Stories"),
        "new_construction": fields.get("NewConstructionYN"),
        "lot_size": fields.get("LotSizeSquareFeet"),
        "zoning": fields.get("Zoning"),
        "bedrooms": fields.get("BedroomsTotal"),
        "full_bathrooms": fields.get("BathroomsFull"),
        "half_bathrooms": fields.get("BathroomsHalf"),
        "kitchen": {
            "features": fields.get("RoomKitchenFeatures"),
            "appliances": fields.get("Appliances"),
        },
        "bedroom_features": fields.get("RoomBedroomFeatures"),
        "dining": fields.get("RoomDiningFeatures"),
        "family_room": fields.get("RoomFamilyRoomFeatures"),
        "laundry": fields.get("LaundryFeatures"),
        "fireplace": {
            "exists": fireplace_count_number > 0,
            "count": fireplace_count,
            "features": fields.get("FireplaceFeatures"),
        },
        "interior_features": fields.get("InteriorFeatures"),
        "flooring": fields.get("Flooring"),
        "heating": fields.get("Heating"),
        "cooling": fields.get("Cooling"),
        "exterior_features": fields.get("PatioAndPorchFeatures"),
        "parking_total": fields.get("ParkingTotal"),
        "parking_features": fields.get("ParkingFeatures"),
        "garage_spaces": fields.get("GarageSpaces"),
        "garage": fields.get("GarageYN"),
        "carport_spaces": fields.get("CarportSpaces"),
        "carport": fields.get("CarportYN"),
        "foundation": fields.get("FoundationDetails"),
        "roof": fields.get("Roof"),
        "utilities": fields.get("Utilities"),
        "water_source": fields.get("WaterSource"),
        "sewer": fields.get("Sewer"),
        "gas": fields.get("Gas"),
        "hoa": fields.get("AssociationYN"),
        "hoa_fee": fields.get("AssociationFee"),
        "hoa_fee_frequency": fields.get("AssociationFeeFrequency"),
        "hoa_amenities": fields.get("AssociationAmenities"),
        "lease_term": fields.get("LeaseTerm"),
        "total_units": fields.get("NumberOfUnitsTotal"),
        "leased_units": fields.get("NumberOfUnitsLeased"),
        "number_of_buildings": fields.get("NumberOfBuildings"),
        "zipcode": fields.get("PostalCode") or fields.get("PostalCodeFull") or data.get("zipcode"),
        "walk_score": fields.get("WalkScore"),
        "cap_rate": fields.get("CapRate"),
        "year_built": fact_display.get("YearBuilt"),
        "price_per_sqft": fact_display.get("ComputedPricePerSqFt"),
        "tax_annual_amount": fact_display.get("TaxAnnualAmount"),
        "county": fact_display.get("CountyOrParish"),
        "units": units,
        "display_policy": {
            "avm_display_allowed": display_policy.get("avm_display_allowed"),
            "consumer_comment_allowed": display_policy.get("consumer_comment_allowed"),
        },
    }


def normalize_schools(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize school information and omit unnecessary source-data objects."""
    data = _as_dict(data)
    mls = _as_dict(data.get("mls"))
    normalized_tiers = []

    for tier in _as_list(data.get("tiers")):
        if not isinstance(tier, dict):
            continue
        schools = []
        for school in _as_list(tier.get("schools")):
            if not isinstance(school, dict):
                continue
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
                "county": mls.get("county"),
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
            "elementary": mls.get("elementary_district"),
            "high_school": mls.get("high_school_district"),
        },
        "county": mls.get("county"),
        "tiers": normalized_tiers,
    }


def normalize_home_card(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize the Card API response for the Page 4 home summary."""
    data = _as_dict(data)
    photo_categories = []

    for media in _as_list(data.get("media")):
        if not isinstance(media, dict):
            continue
        category = media.get("image_of_display") or media.get("label") or media.get("image_of")
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
        "media": {
            "photos_count": data.get("photos_count"),
            "categories": photo_categories,
        },
    }


def normalize_lifestyle_data(
    facts: dict[str, Any],
    zip_insights: dict[str, Any],
    housing_market: dict[str, Any],
) -> dict[str, Any]:
    """Normalize ZIP-code, lifestyle, crime, and housing-market information."""
    facts = _as_dict(facts)
    zip_insights = _as_dict(zip_insights)
    housing_market = _as_dict(housing_market)

    crime = _as_dict(zip_insights.get("crime_rate"))
    location_summary = _as_dict(housing_market.get("location_summary"))
    zipcode_metrics = _as_dict(housing_market.get("zipcode_metrics"))
    meta = _as_dict(location_summary.get("meta"))
    chart = _as_dict(location_summary.get("chart"))
    kpis = _as_list(location_summary.get("kpis"))
    indices = _as_list(location_summary.get("indices"))

    market_kpis: dict[str, Any] = {}
    for kpi in kpis:
        if not isinstance(kpi, dict):
            continue
        kpi_id = kpi.get("id")
        if kpi_id:
            market_kpis[kpi_id] = {
                "title": kpi.get("title"),
                "value": kpi.get("value"),
                "delta": kpi.get("delta"),
                "up": kpi.get("up"),
            }

    lifestyle_indices: dict[str, Any] = {}
    for index in indices:
        if not isinstance(index, dict):
            continue
        index_id = index.get("id")
        if index_id:
            lifestyle_indices[index_id] = {
                "label": index.get("label"),
                "score": index.get("score"),
                "status": index.get("status"),
                "confidence": index.get("confidence"),
                "is_estimated": index.get("is_estimated"),
            }

    latest_price_per_sqft = None
    labels = _as_list(chart.get("labels"))
    values = _as_list(chart.get("values"))
    if labels and values and len(labels) == len(values):
        latest_price_per_sqft = {"period": labels[-1], "value": values[-1]}

    walk_score = facts.get("walk_score")
    if walk_score is None:
        walk_score = _as_dict(facts.get("location")).get("walk_score")

    top_offenses = []
    for offense in _as_list(crime.get("top_three_offenses")):
        if isinstance(offense, dict):
            top_offenses.append({
                "type": offense.get("type"),
                "share_pct": offense.get("share_pct"),
            })

    return {
        "zipcode": zip_insights.get("zipcode") or housing_market.get("zipcode"),
        "walk_score": walk_score,
        "lifestyle_indices": lifestyle_indices,
        "crime": {
            "crime_index": crime.get("index"),
            "crime_level": crime.get("level"),
            "safety_score_0_100": crime.get("safety_score_0_100"),
            "safety_index_10": crime.get("safety_index_10"),
            "three_year_change_pct": crime.get("three_year_change_pct"),
            "most_common_offense": crime.get("most_common_offense"),
            "top_three_offenses": top_offenses,
        },
        "market": {
            "listed_houses": market_kpis.get("listed"),
            "pending_houses": market_kpis.get("pending"),
            "just_sold_30_days": market_kpis.get("sold30"),
            "average_days_on_market": market_kpis.get("dom"),
            "median_estimated_market_value": zipcode_metrics.get("median_est_market_value"),
            "median_price_per_sqft": zipcode_metrics.get("median_price_per_sqft"),
            "latest_average_price_per_sqft": latest_price_per_sqft,
        },
        "as_of": meta.get("as_of") or housing_market.get("as_of"),
    }


def normalize_pricing_data(
    card: dict[str, Any],
    price_history: dict[str, Any],
    estimate_response: dict[str, Any],
) -> dict[str, Any]:
    """Normalize Card, Price History, and Estimate API responses for Page 1."""
    card = _as_dict(card)
    price_history = _as_dict(price_history)
    estimate_response = _as_dict(estimate_response)
    estimate = _as_dict(estimate_response.get("estimate"))

    comparables = []
    for item in _as_list(estimate_response.get("comparables")):
        if not isinstance(item, dict):
            continue
        comparables.append({
            "address": item.get("address"),
            "close_date": item.get("close_date"),
            "sqft": item.get("sqft"),
            "sale_price": item.get("sale_price"),
            "adjusted_price": item.get("adjusted_price"),
        })

    return {
        "listing_key": estimate_response.get("listing_key_numeric") or card.get("id"),
        "listing_id": estimate_response.get("listing_id"),
        "standard_status": estimate_response.get("standard_status"),
        "market": estimate_response.get("market"),
        "property": normalize_card(card),
        "pricing": {
            "asking_price": estimate_response.get("asking_price"),
            "sale_price": estimate_response.get("sale_price"),
            "sale_date": estimate_response.get("sale_date"),
            "estimate": {
                "low": estimate.get("low"),
                "mid": estimate.get("mid"),
                "high": estimate.get("high"),
            },
            "days_listed": estimate_response.get("days_listed"),
            "price_changes": _as_list(estimate_response.get("price_changes")),
        },
        "comparable_sales": comparables,
        "price_history": normalize_price_history(price_history),
    }
