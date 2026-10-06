# 10 minutes TTL cache implementation
# Applied caching to the get_listing_projection endpoint in projection_router.py: GET /api/v1/projection/listing/{listing_key}

import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        self._cache = {}

    def get(self, key: str) -> Any:
        item = self._cache.get(key)

        if item is None:
            return None

        value, created_at = item

        if time.time() - created_at > self.ttl_seconds:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any):
        self._cache[key] = (
            value,
            time.time(),
        )

    def delete(self, key: str):
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()