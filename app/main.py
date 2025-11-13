from fastapi import FastAPI
# from app.api import routes
# from app.api.routes import admin_router, user_router
from app.api.public_routes import router
from app.api.admin_routes import admin_router
from app.api.protected_routes import user_router
from app.api.chat_routes import chat_router
from app.database import engine, Base
from app.models import models
from fastapi.middleware.cors import CORSMiddleware
# from config import settings
from app.core.redis_client import get_redis_client
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import json
from app.core.admin_logger import AdminLoggerMiddleware

load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

Base.metadata.create_all(bind=engine)

# ✅ Create a global Redis client instance
redis_client = get_redis_client()

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = get_redis_client()
    await redis_client.connect()
    print("✅ Redis connected successfully")

    yield

    await redis_client.close()
    print("🛑 Redis connection closed")

app = FastAPI(
    title="Auroraa API",
    description="Backend for the Auroraa art marketplace",
    version="1.2.1",
    lifespan=lifespan
)

allowed_origins = json.loads(os.getenv("ALLOWED_ORIGIN", "[]"))

app.add_middleware(
    CORSMiddleware,
    # allow_origins= os.getenv("ALLOWED_ORIGIN"),
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add the admin logger middleware
app.add_middleware(AdminLoggerMiddleware)

@app.get("/")
def root():
    return {"message": "Welcome to the Auroraa API!"}

@app.get("/health/redis")
async def redis_health():
    try:
        if not redis_client.redis:
            await redis_client.connect()  # Ensure connection before pinging

        pong = await redis_client.redis.ping()
        return {"status": "ok", "ping": pong}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# app.include_router(routes.router, prefix="/api", tags=["public"])
app.include_router(router, prefix="/api", tags=["public"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(user_router, prefix="/api/auth", tags=["authorized"])
app.include_router(chat_router, prefix="/api/auth/chat", tags=["Chat"])

print(os.getenv("ALLOWED_ORIGIN"))