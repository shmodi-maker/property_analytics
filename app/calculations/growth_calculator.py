from datetime import date
from statistics import median
from typing import Optional


MIN_YEARS_BETWEEN_SALES = 1.0


def calculate_annual_growth(
    previous_price: float,
    current_price: float,
    previous_date: date,
    current_date: date,
) -> Optional[float]:
    """
    Calculate annualized growth rate between two sales.

    Sales less than one year apart are ignored.
    """

    if previous_price is None or current_price is None:
        return None

    if previous_price <= 0 or current_price <= 0:
        return None

    if previous_date is None or current_date is None:
        return None

    if current_date <= previous_date:
        return None

    days_between = (current_date - previous_date).days
    years_between = days_between / 365.25

    if years_between < MIN_YEARS_BETWEEN_SALES:
        return None

    growth_rate = (
        (current_price / previous_price)
        ** (1 / years_between)
    ) - 1

    return growth_rate


def calculate_repeat_sale_growth(
    sales: list[dict],
) -> list[dict]:
    """
    Calculate annual growth for consecutive sales
    of the same property.
    """

    if not sales:
        return []

    sales = sorted(
        sales,
        key=lambda x: (
            x["event_date"],
            x.get("observed_at"),
        ),
    )

    repeat_sales = []

    for previous, current in zip(
        sales,
        sales[1:],
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
                "property_identity_id": current.get(
                    "property_identity_id"
                ),
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


def calculate_median_growth(
    repeat_sales: list[dict],
) -> Optional[float]:
    """
    Calculate median annual growth from usable
    repeat-sale observations.
    """

    growth_rates = [
        item["annual_growth_rate"]
        for item in repeat_sales
        if item.get("annual_growth_rate") is not None
    ]

    if not growth_rates:
        return None

    return median(growth_rates)