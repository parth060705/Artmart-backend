from sqlalchemy.orm import Session  
from uuid import UUID
from typing import List
from app.core.auth import get_current_user
from app.database import get_db
from app.models.models import User
from app.crud import crud
from fastapi import APIRouter, Depends
from app.schemas.schemas import (   
    ReviewCreate, ReviewRead
)

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# -------------------------
# REVIEW ENDPOINTS
# -------------------------

@user_router.post("/reviews", response_model=ReviewRead)
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.create_review(db, review, user_id=current_user.id)

@router.get("/reviews/artwork/{artwork_id}", response_model=List[ReviewRead])
def get_reviews_for_artwork(artwork_id: UUID, db: Session = Depends(get_db)):
    return crud.list_reviews_for_artwork(db, artwork_id)

