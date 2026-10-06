import os
import secrets

from fastapi import Header, HTTPException, status


PROJECTION_API_KEY = os.getenv(
    "PROJECTION_API_KEY"
)


def verify_projection_api_key(
    x_api_key: str = Header(...)
):
    """
    Validate the API key supplied in the X-API-Key header.
    """

    if not PROJECTION_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Projection API key is not configured",
        )

    if not secrets.compare_digest(
        x_api_key,
        PROJECTION_API_KEY,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True