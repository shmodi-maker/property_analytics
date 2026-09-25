from datetime import datetime

from app.calculations.zip_growth_calculator import (
    calculate_zip_repeat_sale_growth,
    calculate_zip_median_growth,
    has_enough_zip_data,
)


def test_sales_are_grouped_by_property():
    sales = [
        {
            "property_identity_id": 1,
            "event_date": datetime(2020, 1, 1),
            "observed_at": datetime(2026, 1, 1),
            "price": 100000,
        },
        {
            "property_identity_id": 2,
            "event_date": datetime(2020, 1, 1),
            "observed_at": datetime(2026, 1, 1),
            "price": 500000,
        },
    ]

    repeat_sales = calculate_zip_repeat_sale_growth(sales)

    # Different properties must NOT be compared.
    assert repeat_sales == []


def test_repeat_sales_within_same_property():

    sales = [
        {
            "property_identity_id": 1,
            "event_date": datetime(2020, 1, 1),
            "observed_at": datetime(2026, 1, 1),
            "price": 100000,
        },
        {
            "property_identity_id": 1,
            "event_date": datetime(2022, 1, 1),
            "observed_at": datetime(2026, 1, 1),
            "price": 110000,
        },
    ]

    repeat_sales = calculate_zip_repeat_sale_growth(sales)

    assert len(repeat_sales) == 1
    assert repeat_sales[0]["property_identity_id"] == 1
    assert repeat_sales[0]["used_for_projection"] is True


def test_zip_median_growth():

    repeat_sales = [
        {
            "annual_growth_rate": 0.02,
        },
        {
            "annual_growth_rate": 0.04,
        },
        {
            "annual_growth_rate": 0.06,
        },
    ]

    growth = calculate_zip_median_growth(repeat_sales)

    assert growth == 0.04


def test_zip_data_threshold():

    repeat_sales = [
        {"annual_growth_rate": 0.02}
        for _ in range(10)
    ]

    assert has_enough_zip_data(repeat_sales) is True