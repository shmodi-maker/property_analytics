# app/models/comparable_models.py

from typing import List, Optional

from pydantic import BaseModel


class ComparableProperty(BaseModel):
    listing_id: str

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

    list_price: Optional[float] = None

    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    living_area: Optional[float] = None

    property_class: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    distance_miles: float

    price_per_sqft: Optional[float] = None

    comparability_score: float


class SubjectProperty(BaseModel):
    listing_id: str

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

    list_price: Optional[float] = None

    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    living_area: Optional[float] = None

    property_class: Optional[str] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Valuation(BaseModel):
    estimated_low: Optional[float] = None
    estimated_mid: Optional[float] = None
    estimated_high: Optional[float] = None

    weighted_price_per_sqft: Optional[float] = None


class AskingPriceComparison(BaseModel):
    asking_price: Optional[float] = None

    position: Optional[str] = None

    difference_from_mid: Optional[float] = None
    difference_percent: Optional[float] = None


class ComparableSearchParameters(BaseModel):
    radius_miles: float
    limit: int
    match_property_class: bool


class ComparableResponse(BaseModel):
    property_id: str

    subject_property: SubjectProperty

    search_parameters: ComparableSearchParameters

    valuation: Valuation

    asking_price_comparison: AskingPriceComparison

    comparables: List[ComparableProperty]

    comparable_count: int