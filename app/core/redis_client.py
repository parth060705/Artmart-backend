import os
import redis.asyncio as redis
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_SSL = os.getenv("REDIS_SSL", "false").lower() == "true"

# --- Function to create Redis client ---
def get_redis_client():
    class RedisClient:
        def __init__(self):
            self.client = None

        async def connect(self):
            try:
                # Use SSL=True if REDIS_SSL=true
                self.client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    username=REDIS_USERNAME,
                    password=REDIS_PASSWORD,
                    ssl=REDIS_SSL,
                    decode_responses=True
                )
                # Test connection
                pong = await self.client.ping()
                print("✅ Redis convvnected successfully:", pong)
            except Exception as e:
                print("❌ Redis connection failed:", e)

        async def close(self):
            if self.client:
                await self.client.close()

        async def get(self, key):
            return await self.client.get(key)

        async def set(self, key, value, ttl=None):
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)

    return RedisClient()
