from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
import os
import shutil

from app.core.auth import get_current_user
from app.database import get_db, SessionLocal
from app.models.models import User
from app.core import auth
from app.crud import crud
from app.schemas.schemas import (
    UserCreate, UserRead, ProfileImageResponse, Token,
    ArtworkCreate, ArtworkRead,
    OrderCreate, OrderRead,
    ReviewCreate, ReviewRead,
    WishlistCreate, WishlistRead,
    CartCreate, CartRead,
    LikeCountResponse, HasLikedResponse,
    ArtworkLikeRequest, LikeBase, ArtworkLike,
    CommentCreate, WishlistCreatePublic,
    CartCreatePublic
)

router = APIRouter()

# -------------------------
# DB DEPENDENCY
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# AUTH & USER ENDPOINTS
# -------------------------

@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.passwordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.patch("/users/image", response_model=ProfileImageResponse)
def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.update_user_profile_image(db, current_user.id, file)

# -------------------------
# ARTWORK ENDPOINTS
# -------------------------

@router.post("/artworks", response_model=ArtworkRead)
def create_artwork(artwork: ArtworkCreate, db: Session = Depends(get_db)):
    return crud.create_artwork(db, artwork)

@router.get("/artworks", response_model=List[ArtworkRead])
def list_artworks(db: Session = Depends(get_db)):
    return crud.list_artworks(db)

@router.get("/artworks/{artwork_id}", response_model=ArtworkRead)
def get_artwork(artwork_id: UUID, db: Session = Depends(get_db)):
    artwork = crud.get_artwork(db, artwork_id)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return artwork

# -------------------------
# LIKES ENDPOINTS
# -------------------------

@router.post("/likes/{artwork_id}", response_model=LikeCountResponse)
def like_artwork(artwork_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    crud.like_artwork(db, current_user.id, artwork_id)
    count = crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}

@router.delete("/likes/{artwork_id}", response_model=LikeCountResponse)
def unlike_artwork(artwork_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    crud.unlike_artwork(db, current_user.id, artwork_id)
    count = crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}

@router.get("/likes/{artwork_id}/count", response_model=LikeCountResponse)
def get_like_count(artwork_id: UUID, db: Session = Depends(get_db)):
    count = crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}

@router.get("/likes/{artwork_id}/status", response_model=HasLikedResponse)
def check_like_status(artwork_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    has_liked = crud.has_user_liked_artwork(db, current_user.id, artwork_id)
    return {
        "artwork_id": artwork_id,
        "user_id": current_user.id,
        "has_liked": has_liked
    }

# -------------------------
# COMMENTS ENDPOINTS
# -------------------------

@router.post("/comments/{artwork_id}", status_code=status.HTTP_201_CREATED)
def post_comment(
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_comment(db=db, user_id=current_user.id, comment_data=comment_data)

@router.get("/artwork/{artwork_id}")
def get_comments(
    artwork_id: UUID,
    db: Session = Depends(get_db),
):
    return crud.get_comments_for_artwork(db=db, artwork_id=artwork_id)

# -------------------------
# ORDER ENDPOINTS
# -------------------------

@router.post("/orders", response_model=OrderRead)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.create_order(db, order_data, user_id=current_user.id)


@router.get("/orders/my", response_model=List[OrderRead])
def get_my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.list_orders_for_user(db, user_id=current_user.id)

@router.get("/orders", response_model=List[OrderRead])
def get_all_orders(db: Session = Depends(get_db)):
    return crud.list_all_orders(db)

# -------------------------
# REVIEW ENDPOINTS
# -------------------------

@router.post("/reviews", response_model=ReviewRead)
def create_review(review: ReviewCreate, db: Session = Depends(get_db)):
    return crud.create_review(db, review)

@router.get("/reviews/artist/{artist_id}", response_model=List[ReviewRead])
def get_reviews_for_artist(artist_id: UUID, db: Session = Depends(get_db)):
    return crud.list_reviews_for_artist(db, artist_id)

# -------------------------
# WISHLIST ENDPOINTS
# -------------------------

@router.post("/wishlist", response_model=WishlistRead)
def add_to_wishlist(
    item: WishlistCreatePublic,  # ✅ only expects artworkId from client
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    internal_item = WishlistCreate(userId=current_user.id, artworkId=item.artworkId)
    return crud.add_to_wishlist(db, internal_item, user_id=current_user.id)

@router.get("/wishlist", response_model=List[WishlistRead])
def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_user_wishlist(db, current_user.id)

@router.delete("/wishlist/artwork/{artwork_id}")
def remove_from_wishlist(
    artwork_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.remove_wishlist_item(db, user_id=current_user.id, artwork_id=artwork_id)

# -------------------------
# CART ENDPOINTS
# -------------------------

@router.post("/cart", response_model=CartCreatePublic)
def add_to_cart(
    item: CartCreatePublic,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    internal_item = CartCreatePublic(userId=current_user.id, artworkId=item.artworkId)
    return crud.add_to_cart(db, internal_item, user_id=current_user.id)


@router.get("/cart", response_model=List[CartRead])
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_user_cart(db, current_user.id)

@router.delete("/cart/artwork/{artwork_id}")
def remove_from_cart(
    artwork_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.remove_cart_item(db, user_id=current_user.id, artwork_id=artwork_id)
