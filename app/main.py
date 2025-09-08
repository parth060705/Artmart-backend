from fastapi import FastAPI
from app.api import routes
from app.api.routes import admin_router, user_router, chat_router
from app.database import engine, Base
from app.models import models
from fastapi.middleware.cors import CORSMiddleware
# from config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ARTMART API",
    description="Backend for the ARTMART art marketplace",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                    "https://art-mart-sigma.vercel.app",
                    "https://art-mart-git-admin-parth-gharats-projects.vercel.app",  
                    "https://websocketking.com",
                    'https://art-mart-git-tryouts-parth-gharats-projects.vercel.app'],    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to the ARTMART API!"}

app.include_router(routes.router, prefix="/api", tags=["public"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(user_router, prefix="/api/auth", tags=["authorized"])
app.include_router(chat_router, prefix="/api/auth/chat", tags=["Chat"])

# ---------------------------------------------------------------------
# to check and start the app

# http://127.0.0.1:8000/docs     swagger ui
#  uvicorn app.main:app --reload 