from app.repositories.property_repository import PropertyRepository
from app.repositories.sales_repository import SalesRepository
from app.repositories.zip_sales_repository import ZipSalesRepository

from app.calculations.growth_calculator import (
    calculate_repeat_sale_growth,
    calculate_median_growth,
)

from app.calculations.zip_growth_calculator import (
    calculate_zip_repeat_sale_growth,
    calculate_zip_median_growth,
    has_enough_zip_data,
)

from app.calculations.projection_calculator import (
    calculate_five_year_projection,
)


MIN_PROPERTY_REPEAT_SALES = 2


class ProjectionService:

    def __init__(self):
        self.property_repository = PropertyRepository()
        self.sales_repository = SalesRepository()
        self.zip_sales_repository = ZipSalesRepository()

    def get_projection(self, property_identity_id: int):

        # --------------------------------------------------
        # 1. Get current property information
        # --------------------------------------------------

        property_identity = (
            self.property_repository
            .get_property_identity(property_identity_id)
        )

        if not property_identity:
            return {
                "projection_available": False,
                "message": "Property not found",
            }

        current_listing = (
            self.property_repository
            .get_active_listing(property_identity_id)
        )

        if not current_listing:
            return {
                "projection_available": False,
                "message": "No active listing found",
            }

        current_price = current_listing["price"]
        postal_code = property_identity["postal_code"]

        # --------------------------------------------------
        # 2. Calculate property-specific growth
        # --------------------------------------------------

        property_sales = (
            self.sales_repository
            .get_property_sales(property_identity_id)
        )

        property_repeat_sales = (
            calculate_repeat_sale_growth(property_sales)
        )

        usable_property_growth = [
            item
            for item in property_repeat_sales
            if item["annual_growth_rate"] is not None
        ]

        annual_growth_rate = None
        projection_method = None
        zip_repeat_sales = []

        if len(usable_property_growth) >= MIN_PROPERTY_REPEAT_SALES:

            annual_growth_rate = calculate_median_growth(
                property_repeat_sales
            )

            projection_method = "property_repeat_sales"

        # --------------------------------------------------
        # 3. ZIP-level fallback
        # --------------------------------------------------

        if annual_growth_rate is None:

            zip_sales = (
                self.zip_sales_repository
                .get_zip_sales(postal_code)
            )

            zip_repeat_sales = (
                calculate_zip_repeat_sale_growth(zip_sales)
            )
            print("\nZIP REPEAT SALES")
            print("----------------")

            for item in zip_repeat_sales:
                if item["annual_growth_rate"] is not None:
                    print(
                        f"Property: {item['property_identity_id']} | "
                        f"{item['previous_sale_price']:,.0f} -> "
                        f"{item['current_sale_price']:,.0f} | "
                        f"{item['years_between']:.2f} years | "
                        f"Growth: {item['annual_growth_percent']:.2f}%"
                    )

            zip_growth = calculate_zip_median_growth(zip_repeat_sales)

            print("----------------")
            print(
                f"ZIP median growth: "
                f"{zip_growth * 100:.2f}%"
                if zip_growth is not None
                else "ZIP median growth: None"
            )

            if has_enough_zip_data(zip_repeat_sales):

                annual_growth_rate = (
                    calculate_zip_median_growth(
                        zip_repeat_sales
                    )
                )

                projection_method = "zip_repeat_sales"

        # --------------------------------------------------
        # 4. No reliable projection available
        # --------------------------------------------------

        if annual_growth_rate is None:

            return {
                "projection_available": False,
                "property_identity_id": property_identity_id,
                "message": (
                    "Insufficient historical sales data "
                    "for projection"
                ),
            }

        # --------------------------------------------------
        # 5. Generate 5-year projection
        # --------------------------------------------------

        projections = calculate_five_year_projection(
            current_price=current_price,
            annual_growth_rate=annual_growth_rate,
        )

        # --------------------------------------------------
        # 6. Return result
        # --------------------------------------------------

        return {
            "projection_available": True,
            "property_identity_id": property_identity_id,
            "property": {
                "address": property_identity["normalized_address"],
                "postal_code": postal_code,
                "city": property_identity["city"],
                "state": property_identity["state_or_province"],
            },
            "current": {
                "price": current_price,
                "listing_key": current_listing[
                    "listing_key_numeric"
                ],
                "event_date": current_listing[
                    "event_date"
                ],
            },
            "model": {
                "method": projection_method,
                "annual_growth_rate": annual_growth_rate,
                "annual_growth_percent": round(
                    annual_growth_rate * 100,
                    2,
                ),
                "property_usable_repeat_sale_count": len(
                    usable_property_growth
                ),
                "zip_usable_repeat_sale_count": (
                    sum(
                        1
                        for item in zip_repeat_sales
                        if item["annual_growth_rate"] is not None
                    )
                    if projection_method == "zip_repeat_sales"
                    else None
                ),
            },
            "projections": projections,
        }