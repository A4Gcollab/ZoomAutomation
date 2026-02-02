from typing import Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("Cache")

class SimpleCache:
    """Simple in-memory cache with TTL"""
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if datetime.now() < self._expiry[key]:
                logger.debug(f"Cache HIT: {key}")
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._expiry[key]
                logger.debug(f"Cache EXPIRED: {key}")
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 60):
        self._cache[key] = value
        self._expiry[key] = datetime.now() + timedelta(seconds=ttl_seconds)
        logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
    
    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
            del self._expiry[key]
            logger.debug(f"Cache DELETE: {key}")
    
    def clear(self):
        self._cache.clear()
        self._expiry.clear()
        logger.info("Cache cleared")

cache = SimpleCache()
