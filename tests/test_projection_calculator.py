from app.calculations.projection_calculator import (
    calculate_projected_price,
    calculate_five_year_projection,
)


def test_single_projection():
    price = calculate_projected_price(
        current_price=269000,
        annual_growth_rate=0.0241,
        years=1,
    )

    assert round(price, 2) == 275482.90


def test_five_year_projection():
    projections = calculate_five_year_projection(
        current_price=269000,
        annual_growth_rate=0.0241,
    )

    assert len(projections) == 5

    assert projections[0]["year"] == 1
    assert projections[4]["year"] == 5

    assert projections[0]["projected_price"] > 269000
    assert projections[4]["projected_price"] > projections[0]["projected_price"]