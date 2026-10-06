from collections import defaultdict
from statistics import median
from typing import Optional


MIN_ZIP_REPEAT_SALES = 5

OUTLIER_MIN_GROWTH = -0.30
OUTLIER_MAX_GROWTH = 0.30


def calculate_zip_repeat_sale_growth(
    sales: list[dict],
) -> list[dict]:
    """
    Calculate repeat-sale growth rates for properties
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
                x.get("observed_at"),
            )
        )

        if len(property_sales) < 2:
            continue

        for previous, current in zip(
            property_sales,
            property_sales[1:],
        ):

            previous_date = previous["event_date"].date()
            current_date = current["event_date"].date()

            days_between = (
                current_date - previous_date
            ).days

            years_between = days_between / 365.25

            if years_between < 1:
                growth_rate = None

            elif (
                previous["price"] is None
                or current["price"] is None
                or previous["price"] <= 0
                or current["price"] <= 0
            ):
                growth_rate = None

            else:
                growth_rate = (
                    (current["price"] / previous["price"])
                    ** (1 / years_between)
                ) - 1

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
                    "used_for_projection": (
                        growth_rate is not None
                    ),
                }
            )

    return repeat_sales


def remove_growth_outliers(
    repeat_sales: list[dict],
) -> list[dict]:
    """
    Remove annual growth observations outside
    the allowed ±30% range.
    """

    filtered = []

    for item in repeat_sales:

        growth = item.get("annual_growth_rate")

        if growth is None:
            continue

        if (
            OUTLIER_MIN_GROWTH
            <= growth
            <= OUTLIER_MAX_GROWTH
        ):
            filtered.append(item)

    return filtered


def get_usable_growth_rates(
    repeat_sales: list[dict],
) -> list[float]:

    return [
        item["annual_growth_rate"]
        for item in repeat_sales
        if item.get("annual_growth_rate") is not None
    ]


def calculate_growth_percentiles(
    repeat_sales: list[dict],
) -> dict:
    """
    Calculate P25, median and P75 growth.

    Uses linear interpolation between observations.
    """

    growth_rates = sorted(
        get_usable_growth_rates(repeat_sales)
    )

    if not growth_rates:
        return {
            "p25": None,
            "median": None,
            "p75": None,
            "count": 0,
        }

    def percentile(values, percentile):
        if len(values) == 1:
            return values[0]

        position = (
            percentile / 100
        ) * (len(values) - 1)

        lower_index = int(position)
        upper_index = min(
            lower_index + 1,
            len(values) - 1,
        )

        weight = position - lower_index

        return (
            values[lower_index]
            + (
                values[upper_index]
                - values[lower_index]
            )
            * weight
        )

    return {
        "p25": percentile(growth_rates, 25),
        "median": percentile(growth_rates, 50),
        "p75": percentile(growth_rates, 75),
        "count": len(growth_rates),
    }


def calculate_zip_median_growth(
    repeat_sales: list[dict],
) -> Optional[float]:
    """
    Calculate median annual growth from usable
    ZIP-level repeat sales after outlier filtering.
    """

    filtered = remove_growth_outliers(
        repeat_sales
    )

    growth_rates = get_usable_growth_rates(
        filtered
    )

    if not growth_rates:
        return None

    return median(growth_rates)


def calculate_zip_growth_range(
    repeat_sales: list[dict],
) -> dict:
    """
    Calculate ZIP-level P25 / median / P75 growth.
    """

    filtered = remove_growth_outliers(
        repeat_sales
    )

    return calculate_growth_percentiles(
        filtered
    )


def has_enough_zip_data(
    repeat_sales: list[dict],
) -> bool:

    stats = calculate_zip_growth_range(
        repeat_sales
    )

    return stats["count"] >= MIN_ZIP_REPEAT_SALES