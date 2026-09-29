# app/services/comparable_service.py

from app.calculations.comparable_calculator import (
    ComparableCalculator,
)
from app.config import (
    COMPARABLE_RADIUS_MILES,
    COMPARABLE_LIMIT,
    COMPARABLE_MATCH_PROPERTY_CLASS,
)
from app.repositories.property_repository import (
    PropertyRepository,
)


class ComparableService:

    def __init__(self):
        self.repository = PropertyRepository()

    def get_comparables(
        self,
        property_id: str,
        radius_miles: float = COMPARABLE_RADIUS_MILES,
        limit: int = COMPARABLE_LIMIT,
        match_property_class: bool = COMPARABLE_MATCH_PROPERTY_CLASS,
    ):

        if radius_miles <= 0:
            raise ValueError(
                "radius_miles must be greater than 0"
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than 0"
            )

        # ----------------------------------------------------
        # Get subject property
        # ----------------------------------------------------

        subject = self.repository.get_property_by_id(
            property_id
        )

        if not subject:
            raise ValueError(
                f"Property '{property_id}' was not found."
            )

        if (
            subject.get("latitude") is None
            or subject.get("longitude") is None
        ):
            raise ValueError(
                "Subject property does not have valid "
                "latitude/longitude."
            )

        # ----------------------------------------------------
        # Get candidate listings
        # ----------------------------------------------------

        property_class = (
            subject.get("property_class")
            if match_property_class
            else None
        )

        candidates = (
            self.repository.get_nearby_active_properties(
                latitude=subject["latitude"],
                longitude=subject["longitude"],
                radius_miles=radius_miles,
                property_class=property_class,
                exclude_listing_id=property_id,
            )
        )

        # ----------------------------------------------------
        # Calculate comparability score
        # ----------------------------------------------------

        scored_comps = []

        for comp in candidates:

            scored = (
                ComparableCalculator.prepare_comparable(
                    subject=subject,
                    comp=comp,
                    radius_miles=radius_miles,
                )
            )

            scored_comps.append(scored)

        # ----------------------------------------------------
        # Rank by comparability score
        # ----------------------------------------------------

        scored_comps.sort(
            key=lambda x: x["comparability_score"],
            reverse=True,
        )

        # Top N
        selected_comps = scored_comps[:limit]

        # ----------------------------------------------------
        # Calculate valuation
        # ----------------------------------------------------

        valuation = (
            ComparableCalculator.calculate_valuation(
                subject=subject,
                comparables=selected_comps,
            )
        )

        # ----------------------------------------------------
        # Compare asking price
        # ----------------------------------------------------

        asking_price_comparison = (
            ComparableCalculator.compare_asking_price(
                asking_price=subject.get("list_price"),
                valuation=valuation,
            )
        )

        return {
            "property_id": property_id,

            "subject_property": subject,

            "search_parameters": {
                "radius_miles": radius_miles,
                "limit": limit,
                "match_property_class": match_property_class,
            },

            "valuation": valuation,

            "asking_price_comparison": (
                asking_price_comparison
            ),

            "comparables": selected_comps,

            "comparable_count": len(selected_comps),
        }