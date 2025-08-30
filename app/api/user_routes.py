from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session  
from uuid import UUID
from typing import List, Dict
from app.core.auth import get_current_user
from app.database import get_db
from app.models.models import User
from app.crud import crud
from fastapi import WebSocket, APIRouter, Depends
from app.schemas.schemas import (
    UserCreate, UserRead, ProfileImageResponse, UserUpdate, UserSearch, ArtworkMe,
)

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# FOR CHAT LEVEL ROUTES
chat_router = APIRouter(
    tags=["Chat"],
    dependencies=[Depends(get_current_user)]
)
active_connections: Dict[str, WebSocket] = {}


# -------------------------
# USER ENDPOINTS
# -------------------------

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

# @router.post("/upload-image")
# def upload_image(file: UploadFile = File(...)):
#     return upload_image_to_cloudinary(file)

@user_router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/user/{user_id}", response_model=UserSearch)
def read_user(user_id: UUID, db: Session = Depends(get_db)):
    user = crud.get_user(db, str(user_id)) 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@user_router.patch("/update/users/me", response_model=UserRead)  
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated_user = crud.update_user_details(
        db=db,
        user_id=current_user.id,
        user_update=user_update
    )
    return updated_user

@user_router.patch("/update/users/image", response_model=ProfileImageResponse)
def update_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.update_user_profile_image(db, current_user.id, file)

@user_router.get("/artworks/me", response_model=List[ArtworkMe])
def read_my_artworks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.get_artworks_by_user(db, user_id=current_user.id)