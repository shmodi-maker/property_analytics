from fastapi import FastAPI

from app.database import get_connection
from app.routers.projection_router import router as projection_router
from app.routers.comparable_router import router as comparable_router
from app.routers.listing_tour_router import router as listing_tour_router


app = FastAPI(
    title="Property Analytics API",
    version="1.0.0",
)


app.include_router(projection_router)
app.include_router(comparable_router)
app.include_router(listing_tour_router)


@app.get("/health")
def health_check():

    try:
        conn = get_connection()

        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "result": result[0],
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }