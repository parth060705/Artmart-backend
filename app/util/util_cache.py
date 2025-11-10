# app/utils/cache.py
import json
from app.core.redis_client import get_redis_client

redis_client = get_redis_client()  # shared singleton instance


async def get_cache(key: str):
    """Retrieve a cached value from Redis (as a Python object)."""
    if not redis_client.redis:
        await redis_client.connect()

    data = await redis_client.redis.get(key)
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data  # return raw string if not JSON
    return None


async def set_cache(key: str, value, ttl: int = 300):
    """Store a Python object in Redis as JSON, with optional TTL (seconds)."""
    if not redis_client.redis:
        await redis_client.connect()

    await redis_client.redis.setex(key, ttl, json.dumps(value))
