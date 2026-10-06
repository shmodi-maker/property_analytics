from fastapi import APIRouter, Response

from app.repositories.property_repository import (
    PropertyRepository,
)

from app.repositories.sales_repository import (
    SalesRepository,
)

from app.repositories.zip_sales_repository import (
    ZipSalesRepository,
)

from app.services.projection_service import (
    ProjectionService,
)

from app.cache import TTLCache


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/api/v1/projection",
    tags=["Price Projection"],
)


# ==========================================================
# Dependencies
# ==========================================================

property_repository = PropertyRepository()
sales_repository = SalesRepository()
zip_sales_repository = ZipSalesRepository()

projection_service = ProjectionService()
projection_cache = TTLCache(ttl_seconds=600)


# ==========================================================
# Current active listing
# ==========================================================

@router.get(
    "/{property_identity_id}/current"
)
def get_current_property(
    property_identity_id: int,
):

    property_data = (
        property_repository
        .get_active_listing(
            property_identity_id
        )
    )

    if not property_data:
        return {
            "found": False,
            "message": "No active listing found",
        }

    return {
        "found": True,
        "property": property_data,
    }


# ==========================================================
# Property historical sales
# ==========================================================

@router.get(
    "/{property_identity_id}/sales"
)
def get_property_sales(
    property_identity_id: int,
):

    sales = (
        sales_repository
        .get_property_sales(
            property_identity_id
        )
    )

    return {
        "property_identity_id": property_identity_id,
        "sales_count": len(sales),
        "sales": sales,
    }


# ==========================================================
# ZIP historical sales
# ==========================================================

@router.get(
    "/zip/{postal_code}/sales"
)
def get_zip_sales(
    postal_code: str,
):

    sales = (
        zip_sales_repository
        .get_zip_sales(
            postal_code
        )
    )

    return {
        "postal_code": postal_code,
        "sales_count": len(sales),
        "sales": sales,
    }


# ==========================================================
# Projection by property identity ID
# ==========================================================

@router.get(
    "/{property_identity_id}"
)
def get_property_projection(
    property_identity_id: int,
    response: Response,
):
    cache_key = f"projection:property:{property_identity_id}"

    cached_result = projection_cache.get(cache_key)

    if cached_result is not None:
        response.headers["X-Cache"] = "HIT"
        return cached_result
    
    result = (
        projection_service
        .get_projection(
            property_identity_id
        )
    )
    projection_cache.set(cache_key, result)
    response.headers["X-Cache"] = "MISS"
    return result


# ==========================================================
# Projection by listing key
# ==========================================================

@router.get(
    "/listing/{listing_key}"
)
def get_listing_projection(
    listing_key: str,
    response: Response,
):

    cache_key = f"projection:listing:{listing_key}"

    # Check if the projection is already cached
    cached_result = projection_cache.get(cache_key)
    if cached_result is not None:
        response.headers["X-Cache"] = "HIT"
        return cached_result

    property_identity = (
        property_repository
        .get_property_identity_by_listing_key(
            listing_key
        )
    )

    if not property_identity:
        response.headers["X-Cache"] = "MISS"
        return {
            "projection_available": False,
            "message": "Listing not found",
        }

    result = (
        projection_service
        .get_projection(
            property_identity["id"]
        )
    )
    projection_cache.set(cache_key, result)

    response.headers["X-Cache"] = "MISS"
    return result