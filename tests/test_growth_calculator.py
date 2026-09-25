from datetime import datetime

from app.calculations.growth_calculator import (
    calculate_repeat_sale_growth,
    calculate_median_growth,
)


def test_property_20649_growth():

    sales = [
        {
            "property_identity_id": 20649,
            "event_date": datetime(2023, 8, 15),
            "price": 359000,
        },
        {
            "property_identity_id": 20649,
            "event_date": datetime(2023, 11, 6),
            "price": 205000,
        },
        {
            "property_identity_id": 20649,
            "event_date": datetime(2024, 12, 31),
            "price": 220000,
        },
    ]

    repeat_sales = calculate_repeat_sale_growth(sales)

    assert len(repeat_sales) == 2

    # First pair is less than one year apart.
    assert repeat_sales[0]["used_for_projection"] is False

    # Second pair is the usable 6.32% pair.
    assert repeat_sales[1]["used_for_projection"] is True

    growth = calculate_median_growth(repeat_sales)

    assert growth is not None

    # Approximately 6.32%
    assert round(growth * 100, 2) == 6.32