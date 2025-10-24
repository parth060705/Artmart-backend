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
import os
from dotenv import load_dotenv  

load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auroraa API",
    description="Backend for the Auroraa art marketplace",
    version="1.2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins= os.getenv("ALLOWED_ORIGIN"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to the Auroraa API!"}

# app.include_router(routes.router, prefix="/api", tags=["public"])
app.include_router(router, prefix="/api", tags=["public"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(user_router, prefix="/api/auth", tags=["authorized"])
app.include_router(chat_router, prefix="/api/auth/chat", tags=["Chat"])

print(os.getenv("ALLOWED_ORIGIN"))