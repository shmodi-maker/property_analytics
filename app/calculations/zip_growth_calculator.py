from collections import defaultdict
from statistics import median
from typing import Optional

from app.calculations.growth_calculator import calculate_annual_growth


MIN_ZIP_REPEAT_SALES = 5


def calculate_zip_repeat_sale_growth(
    sales: list[dict],
) -> list[dict]:
    """
    Calculate repeat-sale growth rates for all properties
    within a ZIP code.

    Sales from different properties are never compared.
    """

    sales_by_property = defaultdict(list)

    for sale in sales:
        property_id = sale.get("property_identity_id")

        if property_id is not None:
            sales_by_property[property_id].append(sale)

    repeat_sales = []

    for property_id, property_sales in sales_by_property.items():

        property_sales.sort(
            key=lambda x: (
                x["event_date"],
                x["observed_at"],
            )
        )

        if len(property_sales) < 2:
            continue

        for previous, current in zip(
            property_sales,
            property_sales[1:]
        ):
            growth_rate = calculate_annual_growth(
                previous_price=previous["price"],
                current_price=current["price"],
                previous_date=previous["event_date"].date(),
                current_date=current["event_date"].date(),
            )

            days_between = (
                current["event_date"].date()
                - previous["event_date"].date()
            ).days

            years_between = days_between / 365.25

            repeat_sales.append(
                {
                    "property_identity_id": property_id,
                    "previous_sale_date": previous["event_date"],
                    "current_sale_date": current["event_date"],
                    "previous_sale_price": previous["price"],
                    "current_sale_price": current["price"],
                    "years_between": years_between,
                    "annual_growth_rate": growth_rate,
                    "annual_growth_percent": (
                        growth_rate * 100
                        if growth_rate is not None
                        else None
                    ),
                    "used_for_projection": growth_rate is not None,
                }
            )

    return repeat_sales


def calculate_zip_median_growth(
    repeat_sales: list[dict],
) -> Optional[float]:
    """
    Calculate the median annual growth rate across
    usable repeat-sale pairs.
    """

    usable_growth_rates = [
        item["annual_growth_rate"]
        for item in repeat_sales
        if item["annual_growth_rate"] is not None
    ]

    if not usable_growth_rates:
        return None

    return median(usable_growth_rates)


def has_enough_zip_data(
    repeat_sales: list[dict],
) -> bool:
    """
    Determine whether the ZIP has enough usable
    repeat-sale observations for the MVP model.
    """

    usable_count = sum(
        1
        for item in repeat_sales
        if item["annual_growth_rate"] is not None
    )

    return usable_count >= MIN_ZIP_REPEAT_SALES