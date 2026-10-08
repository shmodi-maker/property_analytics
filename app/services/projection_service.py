from datetime import date
from app.repositories.property_repository import (
    PropertyRepository,
)

from app.repositories.sales_repository import (
    SalesRepository,
)

from app.repositories.zip_sales_repository import (
    ZipSalesRepository,
)

from app.calculations.growth_calculator import (
    calculate_repeat_sale_growth,
    calculate_median_growth,
)

from app.calculations.zip_growth_calculator import (
    calculate_zip_repeat_sale_growth,
    calculate_growth_percentiles,
    remove_growth_outliers,
    MIN_ZIP_REPEAT_SALES,
)

from app.calculations.projection_calculator import (
    calculate_five_year_projection,
)


MIN_PROPERTY_REPEAT_SALES = 2
PROPERTY_RANGE_SAMPLE_SIZE = 5


class ProjectionService:

    def __init__(self):
        self.property_repository = (
            PropertyRepository()
        )

        self.sales_repository = (
            SalesRepository()
        )

        self.zip_sales_repository = (
            ZipSalesRepository()
        )

    def get_projection(
        self,
        property_identity_id: int,
        listing_key: str | None = None,
    ):

        # --------------------------------------------------
        # 1. Property identity
        # --------------------------------------------------

        property_identity = (
            self.property_repository
            .get_property_identity(
                property_identity_id
            )
        )

        if not property_identity:

            return {
                "projection_available": False,
                "message": "Property not found",
            }

        # --------------------------------------------------
        # 2. Current active listing
        # --------------------------------------------------

        if listing_key:
            current_listing = (
                self.property_repository
                .get_listing_for_projection(listing_key)
            )
        else:
            # Preserve existing property-ID endpoint behavior.
            current_listing = (
                self.property_repository
                .get_active_listing(
                    property_identity_id
                )
            )

        if not current_listing:
            return {
                "projection_available": False,
                "property_identity_id": property_identity_id,
                "message": "Listing not found",
            }

        standard_status = current_listing.get(
            "standard_status"
        )

        price_basis = None
        current_price = None
        projection_start_date = None

        MARKET_STATUSES = {
            "Active",
            "Coming Soon",
            "Active Under Contract",
            "Pending",
        }

        if standard_status in MARKET_STATUSES:

            current_price = current_listing.get(
                "list_price"
            )

            projection_start_date = date.today()

            price_basis = "list_price"

        elif standard_status == "Closed":

            current_price = current_listing.get(
                "close_price"
            )

            projection_start_date = current_listing.get(
                "close_date"
            )

            price_basis = "close_price"

        elif standard_status in {
            "Expired",
            "Withdrawn",
            "Canceled",
        }:

            return {
                "projection_available": False,
                "property_identity_id": property_identity_id,

                "current": {
                    "listing_key": current_listing[
                        "listing_key_numeric"
                    ],
                    "standard_status": standard_status,
                    "price_basis": None,
                },

                "message": "listing not on market",
            }

        else:

            return {
                "projection_available": False,
                "property_identity_id": property_identity_id,

                "current": {
                    "listing_key": current_listing[
                        "listing_key_numeric"
                    ],
                    "standard_status": standard_status,
                    "price_basis": None,
                },

                "message": "Unsupported listing status",
            }

        # --------------------------------------------------
        # 3. Lease listing check
        # --------------------------------------------------

        if current_listing[
            "is_lease_listing"
        ]:

            return {
                "projection_available": False,

                "property_identity_id":
                    property_identity_id,

                "property": {
                    "address":
                        property_identity[
                            "normalized_address"
                        ],
                    "postal_code":
                        property_identity[
                            "postal_code"
                        ],
                    "city":
                        property_identity[
                            "city"
                        ],
                    "state":
                        property_identity[
                            "state_or_province"
                        ],
                },

                "listing": {
                    "type": "lease",
                    "monthly_rent":
                        current_listing[
                            "list_price"
                        ],
                    "listing_key":
                        current_listing[
                            "listing_key_numeric"
                        ],
                    "event_date": projection_start_date,
                },

                "message": (
                    "Property is currently listed "
                    "for lease. Property value "
                    "projection is not available "
                    "from the current lease listing."
                ),
            }

        # --------------------------------------------------
        # 4. Validate projection starting price/date
        # --------------------------------------------------

        if current_price is None:

            return {
                "projection_available": False,
                "property_identity_id":
                    property_identity_id,
                "message":
                    "Projection starting price is unavailable",
            }
        if projection_start_date is None:
            return {
                "projection_available": False,
                "property_identity_id": property_identity_id,
                "message": (
                    "Projection start date is unavailable"
                ),
            }

        postal_code = (
            property_identity["postal_code"]
        )

        # --------------------------------------------------
        # 5. Property-specific repeat sales
        # --------------------------------------------------

        property_sales = (
            self.sales_repository
            .get_property_sales(
                property_identity_id
            )
        )

        property_repeat_sales = (
            calculate_repeat_sale_growth(
                property_sales
            )
        )

        property_repeat_sales = (
            remove_growth_outliers(
                property_repeat_sales
            )
        )

        property_stats = (
            calculate_growth_percentiles(
                property_repeat_sales
            )
        )

        property_count = (
            property_stats["count"]
        )

        # --------------------------------------------------
        # 6. ZIP-level repeat sales
        # --------------------------------------------------

        zip_sales = (
            self.zip_sales_repository
            .get_zip_sales(
                postal_code
            )
        )

        zip_repeat_sales = (
            calculate_zip_repeat_sale_growth(
                zip_sales
            )
        )

        zip_repeat_sales = (
            remove_growth_outliers(
                zip_repeat_sales
            )
        )

        zip_stats = (
            calculate_growth_percentiles(
                zip_repeat_sales
            )
        )

        zip_count = zip_stats["count"]

        # --------------------------------------------------
        # 7. Determine growth model
        # --------------------------------------------------

        annual_growth_rate = None
        low_growth_rate = None
        high_growth_rate = None
        projection_method = None
        range_available = False

        # ----------------------------------------------
        # CASE A:
        # 5+ property repeat-sale observations
        # ----------------------------------------------

        if property_count >= PROPERTY_RANGE_SAMPLE_SIZE:

            annual_growth_rate = (
                property_stats["median"]
            )

            low_growth_rate = (
                property_stats["p25"]
            )

            high_growth_rate = (
                property_stats["p75"]
            )

            projection_method = (
                "property_repeat_sales"
            )

            range_available = True

        # ----------------------------------------------
        # CASE B:
        # 2-4 property observations
        #
        # Property median = mid
        # ZIP P25/P75 = range
        # ----------------------------------------------

        elif property_count >= MIN_PROPERTY_REPEAT_SALES:

            annual_growth_rate = (
                property_stats["median"]
            )

            if zip_count >= MIN_ZIP_REPEAT_SALES:

                low_growth_rate = (
                    zip_stats["p25"]
                )

                high_growth_rate = (
                    zip_stats["p75"]
                )

                range_available = True

            else:

                low_growth_rate = (
                    annual_growth_rate
                )

                high_growth_rate = (
                    annual_growth_rate
                )

            projection_method = (
                "property_repeat_sales"
            )

        # ----------------------------------------------
        # CASE C:
        # Less than 2 property observations
        #
        # ZIP median = mid
        # ZIP P25/P75 = range
        # ----------------------------------------------

        elif zip_count >= MIN_ZIP_REPEAT_SALES:

            annual_growth_rate = (
                zip_stats["median"]
            )

            low_growth_rate = (
                zip_stats["p25"]
            )

            high_growth_rate = (
                zip_stats["p75"]
            )

            projection_method = (
                "zip_repeat_sales"
            )

            range_available = True

        # ----------------------------------------------
        # CASE D:
        # No reliable model
        # ----------------------------------------------

        else:

            return {
                "projection_available": False,

                "property_identity_id":
                    property_identity_id,

                "property": {
                    "address":
                        property_identity[
                            "normalized_address"
                        ],
                    "postal_code":
                        postal_code,
                    "city":
                        property_identity[
                            "city"
                        ],
                    "state":
                        property_identity[
                            "state_or_province"
                        ],
                },

                "current": {
                    "price": current_price,
                    "listing_key":
                        current_listing[
                            "listing_key_numeric"
                        ],
                    "event_date": projection_start_date,
                    "standard_status": standard_status,
                    "price_basis": price_basis,
                },

                "model": {
                    "method": None,
                    "range_available": False,

                    "property_usable_repeat_sale_count":
                        property_count,

                    "zip_usable_repeat_sale_count":
                        zip_count,
                },

                "message": (
                    "Insufficient historical sales "
                    "data for projection"
                ),
            }

        # --------------------------------------------------
        # 8. Generate 5-year projection
        # --------------------------------------------------

        projections = (
            calculate_five_year_projection(
                current_price=current_price,
                annual_growth_rate=
                    annual_growth_rate,
                low_growth_rate=
                    low_growth_rate,
                high_growth_rate=
                    high_growth_rate,
            )
        )

        # --------------------------------------------------
        # 9. Return response
        # --------------------------------------------------

        return {

            "projection_available": True,

            "property_identity_id":
                property_identity_id,

            "property": {
                "address":
                    property_identity[
                        "normalized_address"
                    ],
                "postal_code":
                    postal_code,
                "city":
                    property_identity[
                        "city"
                    ],
                "state":
                    property_identity[
                        "state_or_province"
                    ],
            },

            "current": {
                "price": current_price,
                "listing_key": current_listing[
                    "listing_key_numeric"
                ],
                "event_date": projection_start_date,
                "standard_status": standard_status,
                "price_basis": price_basis,
            },

            "model": {

                "method":
                    projection_method,

                "annual_growth_rate":
                    annual_growth_rate,

                "annual_growth_percent":
                    round(
                        annual_growth_rate * 100,
                        2,
                    ),

                "growth_rates": {

                    "low":
                        low_growth_rate,

                    "mid":
                        annual_growth_rate,

                    "high":
                        high_growth_rate,
                },

                "growth_percent": {

                    "low":
                        round(
                            low_growth_rate * 100,
                            2,
                        ),

                    "mid":
                        round(
                            annual_growth_rate * 100,
                            2,
                        ),

                    "high":
                        round(
                            high_growth_rate * 100,
                            2,
                        ),
                },

                "percentiles": {
                    "low": 25,
                    "high": 75,
                },

                "range_available":
                    range_available,

                "property_usable_repeat_sale_count":
                    property_count,

                "zip_usable_repeat_sale_count":
                    zip_count,
            },

            "projections":
                projections,
        }