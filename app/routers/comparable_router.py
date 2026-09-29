# app/routers/comparable_router.py

from fastapi import APIRouter, HTTPException, Query

from app.config import (
    COMPARABLE_RADIUS_MILES,
    COMPARABLE_LIMIT,
    COMPARABLE_MATCH_PROPERTY_CLASS,
)

from app.models.comparable_models import ComparableResponse

from app.services.comparable_service import (
    ComparableService,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Comparable Properties"],
)

service = ComparableService()


@router.get(
    "/properties/{property_id}/comparables",
    response_model=ComparableResponse,
)
def get_comparable_properties(
    property_id: str,

    radius_miles: float = Query(
        default=COMPARABLE_RADIUS_MILES,
        gt=0,
        description="Search radius in miles",
    ),

    limit: int = Query(
        default=COMPARABLE_LIMIT,
        gt=0,
        le=50,
        description="Maximum number of comparable properties",
    ),

    match_property_class: bool = Query(
        default=COMPARABLE_MATCH_PROPERTY_CLASS,
        description="Only compare matching property classes",
    ),
):

    try:

        return service.get_comparables(
            property_id=property_id,
            radius_miles=radius_miles,
            limit=limit,
            match_property_class=match_property_class,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Comparable properties failed: {str(exc)}",
        )