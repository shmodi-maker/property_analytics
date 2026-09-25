from typing import Optional


def calculate_projected_price(
    current_price: float,
    annual_growth_rate: float,
    years: int,
) -> Optional[float]:
    """
    Calculate projected property price after a given number of years.
    """

    if current_price <= 0:
        return None

    if years < 0:
        return None

    return current_price * ((1 + annual_growth_rate) ** years)


def calculate_five_year_projection(
    current_price: float,
    annual_growth_rate: float,
) -> list[dict]:
    """
    Generate annual property price projections for years 1 through 5.
    """

    projections = []

    for year in range(1, 6):
        projected_price = calculate_projected_price(
            current_price=current_price,
            annual_growth_rate=annual_growth_rate,
            years=year,
        )

        projections.append(
            {
                "year": year,
                "projected_price": round(projected_price, 2),
            }
        )

    return projections