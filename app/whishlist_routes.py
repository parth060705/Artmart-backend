from sqlalchemy.orm import Session  
from uuid import UUID
from typing import List
from app.core.auth import get_current_user
from app.database import get_db
from app.models.models import User
from app.crud import crud
from fastapi import APIRouter, Depends
from app.schemas.schemas import (
    WishlistCreate,
    WishlistRead, WishlistCreatePublic, 
)

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# -------------------------
# WISHLIST ENDPOINTS
# -------------------------

@user_router.post("/wishlist", response_model=WishlistRead)
def add_to_wishlist(item: WishlistCreatePublic, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    internal_item = WishlistCreate(userId=current_user.id, artworkId=item.artworkId)
    return crud.add_to_wishlist(db, internal_item, user_id=current_user.id)

@user_router.get("/wishlist", response_model=List[WishlistRead])
def get_wishlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_user_wishlist(db, current_user.id)

@user_router.delete("/wishlist/artwork/{artwork_id}")
def remove_from_wishlist(artwork_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.remove_wishlist_item(db, user_id=current_user.id, artwork_id=artwork_id)
