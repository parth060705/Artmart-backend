from datetime import datetime, timedelta
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
            return data
    return None


async def set_cache(key: str, value, ttl: int = 300):
    """Store a Python object in Redis as JSON, with optional TTL (seconds)."""
    if not redis_client.redis:
        await redis_client.connect()

    await redis_client.redis.setex(key, ttl, json.dumps(value))


def seconds_until_midnight() -> int:
    """Calculate seconds remaining until next midnight (local time)."""
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((tomorrow - now).total_seconds())


async def set_cache_until_midnight(key: str, value):
    """Store cache that automatically expires at midnight."""
    ttl = seconds_until_midnight()
    await set_cache(key, value, ttl)
