from fastapi import APIRouter

from app.repositories.property_repository import PropertyRepository
from app.repositories.sales_repository import SalesRepository
from app.repositories.zip_sales_repository import ZipSalesRepository
from app.services.projection_service import ProjectionService

router = APIRouter(
    prefix="/api/v1/projection",
    tags=["Price Projection"]
)

repository = PropertyRepository()
sales_repository = SalesRepository()
zip_sales_repository = ZipSalesRepository()
projection_service = ProjectionService()

@router.get("/{property_identity_id}/current")
def get_current_property(property_identity_id: int):

    property_data = repository.get_active_listing(
        property_identity_id
    )

    if not property_data:
        return {
            "found": False,
            "message": "No active listing found"
        }

    return {
        "found": True,
        "property": property_data
    }

@router.get("/{property_identity_id}/sales")
def get_property_sales(property_identity_id: int):

    sales = sales_repository.get_property_sales(
        property_identity_id
    )

    return {
        "property_identity_id": property_identity_id,
        "sales_count": len(sales),
        "sales": sales
    }

@router.get("/zip/{postal_code}/sales")
def get_zip_sales(postal_code: str):
    sales = zip_sales_repository.get_zip_sales(postal_code)

    return {
        "postal_code": postal_code,
        "sales_count": len(sales),
        "sales": sales,
    }
@router.get("/{property_identity_id}")
def get_property_projection(property_identity_id: int):

    return projection_service.get_projection(
        property_identity_id
    )