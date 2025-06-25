from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import get_current_user


from app.database import SessionLocal
from app.database import get_db
from app.models.models import User
from app.core import auth
from app.crud import crud
from app.schemas.schemas import (
    UserCreate, UserRead,
    ArtworkCreate, ArtworkRead,
    OrderCreate, OrderRead,
    ReviewCreate, ReviewRead,
    WishlistCreate, WishlistRead,
    CartCreate, CartRead,
    UserProfileImageUpdate, Token
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
# USER ENDPOINTS
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

@router.patch("/users/{user_id}/image")
def update_profile_image(user_id: UUID, update: UserProfileImageUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update.profileImage is not None:
        user.profileImage = update.profileImage
        db.commit()
        db.refresh(user)

    return {"message": "Profile image updated", "profileImage": user.profileImage}

# -------------------------
# ARTWORK ENDPOINTS
# -------------------------

@router.post("/artworks", response_model=ArtworkRead)
def create_artwork(artwork: ArtworkCreate, db: Session = Depends(get_db)):
    return crud.create_artwork(db, artwork)

@router.get("/artworks", response_model=List[ArtworkRead])
def list_artworks(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return crud.list_artworks(db, skip=skip, limit=limit)

@router.get("/artworks/{artwork_id}", response_model=ArtworkRead)
def get_artwork(artwork_id: UUID, db: Session = Depends(get_db)):
    artwork = crud.get_artwork(db, artwork_id)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    return artwork

# -------------------------
# ORDER ENDPOINTS
# -------------------------

@router.post("/orders", response_model=OrderRead)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    return crud.create_order(db, order)

@router.get("/orders/user/{user_id}", response_model=List[OrderRead])
def list_user_orders(user_id: UUID, db: Session = Depends(get_db)):
    return crud.list_orders_for_user(db, user_id)

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
def add_to_wishlist(item: WishlistCreate, db: Session = Depends(get_db)):
    return crud.add_to_wishlist(db, item)

@router.get("/wishlist/user/{user_id}", response_model=List[WishlistRead])
def get_wishlist(user_id: UUID, db: Session = Depends(get_db)):
    return crud.get_user_wishlist(db, user_id)

# -------------------------
# CART ENDPOINTS
# -------------------------

@router.post("/cart", response_model=CartRead)
def add_to_cart(item: CartCreate, db: Session = Depends(get_db)):
    return crud.add_to_cart(db, item)

@router.get("/cart/user/{user_id}", response_model=List[CartRead])
def get_cart(user_id: UUID, db: Session = Depends(get_db)):
    return crud.get_user_cart(db, user_id)
