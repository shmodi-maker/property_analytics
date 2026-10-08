"""
Security utilities for API authentication and rate limiting.

This module provides:
1. API-key validation for the Projection API.
2. API-key validation for ListingTour endpoints.
3. A simple in-memory rate limiter for ListingTour requests.
"""

import os
import secrets
import time
from collections import defaultdict

from fastapi import Header, HTTPException, status


# ============================================================
# PROJECTION API AUTHENTICATION
# ============================================================

PROJECTION_API_KEY = os.getenv("PROJECTION_API_KEY")


def verify_projection_api_key(
    x_api_key: str = Header(...)
):
    """
    Validate the API key supplied in the X-API-Key header.

    This dependency protects the Projection API.
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


# ============================================================
# LISTING TOUR API AUTHENTICATION
# ============================================================

LISTING_TOUR_API_KEY = os.getenv("LISTING_TOUR_API_KEY")


def verify_listing_tour_api_key(
    x_api_key: str = Header(...)
):
    """
    Validate the API key supplied in the X-API-Key header.

    This dependency protects the ListingTour summary endpoints.
    """

    if not LISTING_TOUR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ListingTour API key is not configured",
        )

    if not secrets.compare_digest(
        x_api_key,
        LISTING_TOUR_API_KEY,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return True


# ============================================================
# LISTING TOUR RATE LIMITING
# ============================================================

RATE_LIMIT_PER_MINUTE = int(
    os.getenv("RATE_LIMIT_PER_MINUTE", "30")
)

# Stores timestamps for each API key.
# Example:
# {
#     "key:abc123": [timestamp1, timestamp2, ...]
# }
_request_log = defaultdict(list)


def check_listing_tour_rate_limit(
    x_api_key: str = Header(...)
):
    """
    Apply a simple per-API-key rate limit.

    The default limit is 30 requests per minute.

    Raises:
        HTTPException: 429 when the rate limit is exceeded.
    """

    now = time.time()
    window_start = now - 60

    client_key = f"key:{x_api_key}"

    # Remove requests older than one minute.
    _request_log[client_key] = [
        timestamp
        for timestamp in _request_log[client_key]
        if timestamp > window_start
    ]

    if len(_request_log[client_key]) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    _request_log[client_key].append(now)

    return True