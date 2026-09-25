from fastapi import APIRouter, Query

from app.services.property_lookup_service import (
    PropertyLookupService,
)


router = APIRouter(
    prefix="/api/v1/properties",
    tags=["Property Lookup"],
)

property_lookup_service = PropertyLookupService()


@router.get("/search")
def search_property(
    address: str = Query(
        ...,
        description="Property address or partial address",
    ),
    city: str | None = Query(None),
    state: str | None = Query(None),
    postal_code: str | None = Query(None),
):

    results = property_lookup_service.search_property(
        address=address,
        city=city,
        state=state,
        postal_code=postal_code,
    )

    if not results:
        return {
            "found": False,
            "query": {
                "address": address,
                "city": city,
                "state": state,
                "postal_code": postal_code,
            },
            "match_count": 0,
            "matches": [],
        }

    primary = results[0]

    matches = []

    for result in results:
        matches.append(
            {
                "property_identity_id": result[
                    "property_identity_id"
                ],
                "listing_key_numeric": result[
                    "listing_key_numeric"
                ],
                "address": result["normalized_address"],
                "city": result["city"],
                "state": result["state_or_province"],
                "postal_code": result["postal_code"],
                "has_active_listing": result[
                    "has_active_listing"
                ],
                "latest_event_date": result[
                    "latest_event_date"
                ],
                "identity_source": result[
                    "identity_source"
                ],
                "confidence": result["confidence"],
                "latitude": result["latitude"],
                "longitude": result["longitude"],
            }
        )

    return {
        "found": True,
        "query": {
            "address": address,
            "city": city,
            "state": state,
            "postal_code": postal_code,
        },
        "primary_match": {
            "property_identity_id": primary["property_identity_id"],
            "match_reason": (
                "active_listing"
                if primary["has_active_listing"]
                else "latest_property_activity"
            ),
            "latitude":primary["latitude"],
            "longitude":primary["longitude"],
        },
        "match_count": len(matches),
        "matches": matches,
    }