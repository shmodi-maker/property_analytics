def calculate_projected_price(
    current_price: float,
    annual_growth_rate: float,
    years: int,
) -> float:
    """
    Calculate future property value.
    """

    return current_price * (
        (1 + annual_growth_rate) ** years
    )


def calculate_five_year_projection(
    current_price: float,
    annual_growth_rate: float,
    low_growth_rate: float | None = None,
    high_growth_rate: float | None = None,
) -> list[dict]:
    """
    Generate 5-year property projection.

    Mid = median growth
    Low = P25 growth
    High = P75 growth
    """

    if current_price is None:
        return []

    if annual_growth_rate is None:
        return []

    if low_growth_rate is None:
        low_growth_rate = annual_growth_rate

    if high_growth_rate is None:
        high_growth_rate = annual_growth_rate

    # Guarantee logical ordering.
    low_growth_rate = min(
        low_growth_rate,
        annual_growth_rate,
        high_growth_rate,
    )

    high_growth_rate = max(
        low_growth_rate,
        annual_growth_rate,
        high_growth_rate,
    )

    projections = []

    for year in range(1, 6):

        low_price = calculate_projected_price(
            current_price=current_price,
            annual_growth_rate=low_growth_rate,
            years=year,
        )

        mid_price = calculate_projected_price(
            current_price=current_price,
            annual_growth_rate=annual_growth_rate,
            years=year,
        )

        high_price = calculate_projected_price(
            current_price=current_price,
            annual_growth_rate=high_growth_rate,
            years=year,
        )

        projections.append(
            {
                "year": year,
                "projected_price": round(
                    mid_price,
                    2,
                ),
                "low": round(
                    low_price,
                    2,
                ),
                "mid": round(
                    mid_price,
                    2,
                ),
                "high": round(
                    high_price,
                    2,
                ),
            }
        )

    return projections