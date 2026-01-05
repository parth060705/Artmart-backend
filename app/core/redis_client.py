import os
from redis import asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

class RedisClient:
    """Async Redis client wrapper for Auroraa app"""

    def __init__(self):
        self.redis = None
        self.redis_url = os.getenv("REDIS_URL")

    async def connect(self):
        """Establish async Redis connection"""
        if not self.redis:
            self.redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # test connection
            try:
                await self.redis.ping()
                print("✅ Connected to Redis Cloud")
            except Exception as e:
                print("❌ Redis connection failed:", e)

    async def close(self):
        """Close the Redis connection"""
        if self.redis:
            await self.redis.close()
            print("🔌 Redis connection closed")

    async def get(self, key: str):
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expire: int = None):
        await self.redis.set(key, value, ex=expire)

    async def delete(self, key: str):
        await self.redis.delete(key)


# Factory function for FastAPI lifespan or DI
def get_redis_client() -> RedisClient:
    return RedisClient()

# print the redis url
print(os.getenv("REDIS_URL"))