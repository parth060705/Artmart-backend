from fastapi import FastAPI
from app.api import routes
from app.database import engine, Base
from app.models import models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ARTMART API",
    description="Backend for the ARTMART art marketplace",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Welcome to the ARTMART API!"}

app.include_router(routes.router)
