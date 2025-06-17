from app.database import Base, engine
from app import models
from fastapi import FastAPI
from app.routers import users, artworks, orders  # add others as needed

app = FastAPI()
app.include_router(users.router)
app.include_router(artworks.router)
app.include_router(orders.router)


def create_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()

