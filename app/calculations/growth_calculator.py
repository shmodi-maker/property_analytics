from datetime import date
from typing import Optional
from statistics import median


MIN_YEARS_BETWEEN_SALES = 1.0


def calculate_annual_growth(
    previous_price: float,
    current_price: float,
    previous_date: date,
    current_date: date,
) -> Optional[float]:
    """
    Calculate annualized growth between two property sale prices.

    Returns:
        Growth rate as a decimal.
        Example: 0.0632 = 6.32%

    Returns None if the sale interval is less than one year
    or the input data is invalid.
    """

    if previous_price <= 0 or current_price <= 0:
        return None

    days_between = (current_date - previous_date).days

    if days_between <= 0:
        return None

    years_between = days_between / 365.25

    if years_between < MIN_YEARS_BETWEEN_SALES:
        return None

    growth_rate = (
        (current_price / previous_price)
        ** (1 / years_between)
    ) - 1

    return growth_rate

def calculate_repeat_sale_growth(sales: list[dict]) -> list[dict]:
    """
    Calculate annualized growth for consecutive property sales.

    Sales must be ordered chronologically.
    """

    if len(sales) < 2:
        return []

    repeat_sales = []

    for previous, current in zip(sales, sales[1:]):

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

        repeat_sales.append({
            "property_identity_id": current["property_identity_id"],
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
        })

    return repeat_sales

def calculate_median_growth(
    repeat_sales: list[dict],
) -> Optional[float]:
    """
    Calculate the median annual growth rate from
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