from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session  
from typing import List
from app.core.auth import get_current_user
from app.database import get_db
from app.models.models import User
from app.crud import crud
from fastapi import APIRouter, Depends

from app.schemas.schemas import (
    CommentCreate,
    CommentRead
)

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# -------------------------
# COMMENTS ENDPOINTS
# -------------------------

@user_router.post("/comments/{artwork_id}", status_code=status.HTTP_201_CREATED)
def post_comment(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_comment(db=db, user_id=current_user.id, comment_data=comment_data)

@router.get("/artworks/{artwork_id}/comments", response_model=List[CommentRead])
def get_comments(artwork_id: str, db: Session = Depends(get_db)):
    return crud.get_comments_by_artwork(db, artwork_id)

