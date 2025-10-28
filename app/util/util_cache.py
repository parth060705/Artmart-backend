import json
from app.core.redis_client import get_redis_client

redis_client = get_redis_client()  # one shared client instance

async def get_cache(key: str):
    data = await redis_client.client.get(key)
    if data:
        return json.loads(data)
    return None

async def set_cache(key: str, value, ttl: int = 300):
    await redis_client.client.setex(key, ttl, json.dumps(value))
