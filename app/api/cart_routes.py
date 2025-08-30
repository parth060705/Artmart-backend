from sqlalchemy.orm import Session  
from uuid import UUID
from typing import List
from app.core.auth import get_current_user
from app.database import get_db
from app.models.models import User
from app.crud import crud
from app.models import models

# FOR MEASSAGING
from fastapi import APIRouter, Depends

from app.schemas.schemas import (
    CartCreate, CartRead, CartCreatePublic
)

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)


# -------------------------
# CART ENDPOINTS
# -------------------------

@user_router.post("/cart", response_model=CartRead)
def add_to_cart(
    item: CartCreatePublic,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    internal_item = CartCreate(
        userId=current_user.id,
        artworkId=item.artworkId,
        purchase_quantity=item.purchase_quantity
    )
    return crud.add_to_cart(db, internal_item)


@user_router.get("/cart", response_model=List[CartRead])
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_user_cart(db, current_user.id)

@user_router.delete("/cart/artwork/{artwork_id}")
def remove_from_cart(artwork_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.remove_cart_item(db, user_id=current_user.id, artwork_id=artwork_id)
