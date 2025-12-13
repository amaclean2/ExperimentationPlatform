from cachetools import TTLCache
from functools import wraps
from typing import Callable, Any
import hashlib
import json

experiment_cache = TTLCache(maxsize=1000, ttl=300)
segment_cache = TTLCache(maxsize=1000, ttl=60)
variant_assignment_cache = TTLCache(maxsize=10000, ttl=86400)


def make_cache_key(*args, **kwargs) -> str:
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(cache: TTLCache):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{make_cache_key(*args, **kwargs)}"

            if cache_key in cache:
                return cache[cache_key]

            result = await func(*args, **kwargs)
            cache[cache_key] = result
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{make_cache_key(*args, **kwargs)}"

            if cache_key in cache:
                return cache[cache_key]

            result = func(*args, **kwargs)
            cache[cache_key] = result
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def invalidate_experiment_cache(experiment_id: int):
    keys_to_remove = [key for key in experiment_cache.keys() if str(experiment_id) in key]
    for key in keys_to_remove:
        experiment_cache.pop(key, None)


def invalidate_segment_cache(segment_id: int):
    keys_to_remove = [key for key in segment_cache.keys() if str(segment_id) in key]
    for key in keys_to_remove:
        segment_cache.pop(key, None)


def invalidate_variant_assignment(user_id: str, experiment_id: int):
    keys_to_remove = [
        key for key in variant_assignment_cache.keys()
        if str(user_id) in key and str(experiment_id) in key
    ]
    for key in keys_to_remove:
        variant_assignment_cache.pop(key, None)


def clear_all_caches():
    experiment_cache.clear()
    segment_cache.clear()
    variant_assignment_cache.clear()
