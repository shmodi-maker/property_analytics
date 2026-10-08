# app/config.py

import os


DATABASE_URL = os.getenv("DATABASE_URL")

LISTING_TOUR_API_BASE_URL_1 = os.getenv(
    "LISTING_TOUR_API_BASE_URL_1"
)

LISTING_TOUR_API_BASE_URL_2 = os.getenv(
    "LISTING_TOUR_API_BASE_URL_2"
)

PROJECTION_API_KEY = os.getenv(
    "PROJECTION_API_KEY"
)

JAINAM_API_TOKEN = os.getenv(
    "JAINAM_API_TOKEN"
)

AWS_REGION = os.getenv(
    "AWS_REGION",
    "us-east-1"
)

BEDROCK_MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "amazon.nova-micro-v1:0"
)

COMPARABLE_RADIUS_MILES = float(
    os.getenv("COMPARABLE_RADIUS_MILES", "5")
)

COMPARABLE_LIMIT = int(
    os.getenv("COMPARABLE_LIMIT", "5")
)

# Require comparable properties to have the same property class
COMPARABLE_MATCH_PROPERTY_CLASS = os.getenv(
    "COMPARABLE_MATCH_PROPERTY_CLASS",
    "true"
).lower() == "true"


COMPARABLE_WEIGHT_DISTANCE = float(
    os.getenv("COMPARABLE_WEIGHT_DISTANCE", "0.30")
)

COMPARABLE_WEIGHT_LIVING_AREA = float(
    os.getenv("COMPARABLE_WEIGHT_LIVING_AREA", "0.35")
)

COMPARABLE_WEIGHT_BEDROOMS = float(
    os.getenv("COMPARABLE_WEIGHT_BEDROOMS", "0.15")
)

COMPARABLE_WEIGHT_BATHROOMS = float(
    os.getenv("COMPARABLE_WEIGHT_BATHROOMS", "0.10")
)

COMPARABLE_WEIGHT_PROPERTY_CLASS = float(
    os.getenv("COMPARABLE_WEIGHT_PROPERTY_CLASS", "0.10")
)


COMPARABLE_WEIGHTS = {
    "distance": COMPARABLE_WEIGHT_DISTANCE,
    "living_area": COMPARABLE_WEIGHT_LIVING_AREA,
    "bedrooms": COMPARABLE_WEIGHT_BEDROOMS,
    "bathrooms": COMPARABLE_WEIGHT_BATHROOMS,
    "property_class": COMPARABLE_WEIGHT_PROPERTY_CLASS,
}


def validate_comparable_weights():
    total = sum(COMPARABLE_WEIGHTS.values())

    if abs(total - 1.0) > 0.001:
        raise ValueError(
            f"Comparable weights must total 1.0. "
            f"Current total: {total}"
        )