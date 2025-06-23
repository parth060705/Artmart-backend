from fastapi import FastAPI
from app.api import routes
from app.database import engine, Base
from app.models import models
# from config import settings

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

# ---------------------------------------------------------------------
# to check and start the app

# http://127.0.0.1:8000/docs     swagger ui
#  uvicorn app.main:app --reload 


