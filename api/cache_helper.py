# ===========================================================================
# Cache Helper - Simple in-memory caching
# ===========================================================================

from functools import wraps
from datetime import datetime, timedelta

_cache = {}

def cached(ttl_seconds=300):
    """
    Simple in-memory cache decorator
    
    Usage:
        @cached(ttl_seconds=600)
        def expensive_function():
            return heavy_computation()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            now = datetime.now()
            
            # Check if cached and not expired
            if key in _cache:
                data, expires = _cache[key]
                if now < expires:
                    return data
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[key] = (result, now + timedelta(seconds=ttl_seconds))
            
            # Cleanup old entries (keep cache size manageable)
            if len(_cache) > 100:
                expired_keys = [k for k, (_, exp) in _cache.items() if now >= exp]
                for k in expired_keys:
                    del _cache[k]
            
            return result
        return wrapper
    return decorator


def clear_cache():
    """Clear all cached data"""
    global _cache
    _cache = {}
