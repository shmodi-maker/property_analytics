from fastapi import APIRouter

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
):

    return (
        projection_service
        .get_projection(
            property_identity_id
        )
    )


# ==========================================================
# Projection by listing key
# ==========================================================

@router.get(
    "/listing/{listing_key}"
)
def get_listing_projection(
    listing_key: str,
):

    property_identity = (
        property_repository
        .get_property_identity_by_listing_key(
            listing_key
        )
    )

    if not property_identity:
        return {
            "projection_available": False,
            "message": "Listing not found",
        }

    return (
        projection_service
        .get_projection(
            property_identity["id"]
        )
    )