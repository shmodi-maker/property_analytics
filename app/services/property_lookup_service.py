from app.repositories.property_lookup_repository import (
    PropertyLookupRepository,
)


class PropertyLookupService:

    def __init__(self):
        self.repository = PropertyLookupRepository()

    def search_property(
        self,
        address: str,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
    ):

        results = self.repository.search_by_address(
            address=address,
            city=city,
            state=state,
            postal_code=postal_code,
        )

        # Keep only properties that have a valid identity ID.
        results = [
            result
            for result in results
            if result["property_identity_id"] is not None
        ]

        # Deduplicate listings belonging to the same property.
        unique_properties = {}

        for result in results:
            property_id = result["property_identity_id"]

            if property_id not in unique_properties:
                unique_properties[property_id] = result

        properties = list(unique_properties.values())

        # Repository already orders these, but explicitly
        # sort here so the service owns the business rule.
        properties.sort(
            key=lambda x: (
                x["has_active_listing"],
                x["latest_event_date"] is not None,
                x["latest_event_date"] or "",
            ),
            reverse=True,
        )

        return properties