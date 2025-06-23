from fastapi import FastAPI
from app.api import routes
from app.database import engine, Base
from app.models import models  # Needed to register models before Base.metadata.create_all()

# Create tables if they don’t exist
Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI(
    title="ARTMART API",
    description="Backend for the ARTMART art marketplace",
    version="1.0.0"
)

# Register routes
app.include_router(routes.router)
