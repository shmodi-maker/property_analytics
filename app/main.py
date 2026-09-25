from fastapi import FastAPI

from app.database import get_connection
from app.routers.projection_router import router as projection_router
from app.routers.property_router import router as property_router


app = FastAPI(
    title="Property Analytics API",
    version="1.0.0",
)


app.include_router(projection_router)
app.include_router(property_router)


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