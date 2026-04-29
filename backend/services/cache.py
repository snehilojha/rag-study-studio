"""Caching helpers."""

from diskcache import Cache
from config import settings

cache = Cache(settings.CACHE_DIR)

def get_cache(key):
    """Get a cached value."""
    return cache.get(key)

def set_cache(key, value):
    """Set a cached value."""
    cache.set(key, value, expire=settings.CACHE_EXPIRATION)


