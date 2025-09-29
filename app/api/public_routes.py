from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session, subqueryload
from typing import List, Optional
from uuid import UUID
from datetime import timedelta, datetime

from app.database import get_db
from app.core import auth
from app.core.auth import get_current_user_optional
from app.models import models
from app.models.models import User
from app.schemas.user_schema import UserCreate, UserRead, UserSearch, Token, ResetPasswordWithOTPSchema
from app.schemas.artworks_schemas import ArtworkRead, ArtworkCategory, ArtworkArtist
from app.schemas.review_schemas import ReviewRead
from app.schemas.likes_schemas import LikeCountResponse
from app.schemas.comment_schemas import CommentRead
from app.core.smtp_otp import send_otp_email
from fastapi import BackgroundTasks
from app.crud import user_crud, search_crud, artworks_crud, recmmendation_crud,review_crud, likes_crud, comment_crud
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


router = APIRouter(
    tags=["public"]
)

# -------------------------
# AUTH ROUTES
# -------------------------

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.passwordHash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token = auth.create_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth.create_token(
        data={"sub": user.username}, expires_delta=timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    username = auth.decode_access_token(refresh_token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = user_crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access_token = auth.create_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": new_access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# -------------------------
# USER (Public)
# -------------------------

@router.post("/register", response_model=UserRead)
def register_user(
    name: str = Form(None),
    email: str = Form(None),
    username: str = Form(None),
    password: str = Form(None),
    location: str = Form(None),
    gender: str = Form(None),
    bio: str = Form(None),
    age: int = Form(None),
    phone: str = Form(None),
    pincode: str = Form(None),
    isAgreedtoTC: bool = Form(False),
    db: Session = Depends(get_db),
):
    if email and user_crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if username and user_crud.get_user_by_username(db, username):
        suggestions = user_crud.suggest_usernames(db, username)
        raise HTTPException(status_code=400, detail={"message": "Username taken", "suggestions": suggestions})

    user_data = UserCreate(
        name=name, email=email, username=username, password=password,
        location=location, gender=gender, bio=bio, age=age, phone=phone,
        pincode=pincode, isAgreedtoTC=isAgreedtoTC
    )
    return user_crud.create_user(db=db, user=user_data)


@router.get("/user/{user_id}", response_model=UserSearch)
def read_user(user_id: UUID, db: Session = Depends(get_db)):
    user = user_crud.get_user(db, str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# @router.post("/forgot-password")
# def forgot_password(email: str, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None ):

#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         return {"message": "If this email exists, an OTP has been sent"}

#     otp = user_crud.generate_otp()
#     expires_at = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 min
#     user_crud.otp_store[email] = {"otp": otp, "expires_at": expires_at}

#     # TODO: Send OTP via email (SMTP/SendGrid/etc.)
#     print(f"[DEBUG] OTP for {email}: {otp}")
#     # Send OTP in background
#     background_tasks.add_task(send_otp_email, email, otp)

#     return {"message": "If this email exists, an OTP has been sent"}

# @router.post("/reset-password")
# def reset_password_with_otp(data: ResetPasswordWithOTPSchema, db: Session = Depends(get_db)):

#     # Check OTP existence and validity
#     record = user_crud.otp_store.get(data.email)
#     if not record:
#         raise HTTPException(status_code=400, detail="Invalid or expired OTP")
#     if record["otp"] != data.otp:
#         raise HTTPException(status_code=400, detail="Invalid OTP")
#     if record["expires_at"] < datetime.utcnow():
#         del user_crud.otp_store[data.email]
#         raise HTTPException(status_code=400, detail="OTP expired")

#     # Find user
#     user = db.query(User).filter(User.email == data.email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Validate password strength
#     user_crud.validate_password_strength(data.new_password)

#     # Update password
#     user.passwordHash = pwd_context.hash(data.new_password)
#     db.commit()
#     db.refresh(user)

#     # Remove OTP after successful use
#     del user_crud.otp_store[data.email]

#     return {"message": "Password updated successfully"}

@router.post("/forgot-password")
def forgot_password(
    email: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    otp = user_crud.forgot_password(db, email)
    if otp:
        # Print OTP for debug/testing
        print(f"[DEBUG] OTP for {email}: {otp}")
        if background_tasks:
            background_tasks.add_task(send_otp_email, email, otp)

    return {"message": "If this email exists, an OTP has been sent"}


@router.post("/reset-password")
def reset_password(data: ResetPasswordWithOTPSchema, db: Session = Depends(get_db)):
    user_crud.reset_password(db, email=data.email, otp=data.otp, new_password=data.new_password)
    return {"message": "Password updated successfully"}

# -------------------------
# ARTWORK (Public)
# -------------------------

@router.get("/artworks", response_model=List[ArtworkRead])
def list_artworks_route(db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    artworks = db.query(models.Artwork).options(
        subqueryload(models.Artwork.artist),
        subqueryload(models.Artwork.likes),
        subqueryload(models.Artwork.images)
    ).all()
    artworks_for_sale = [a for a in artworks if a.forSale]

    cart_ids = None
    if current_user:
        cart_items = db.query(models.Cart.artworkId).filter_by(userId=str(current_user.id)).all()
        cart_ids = {item.artworkId for item in cart_items}

    result = []
    for art in artworks_for_sale:
        like_count = len(art.likes) if art.likes else 0
        is_in_cart = str(art.id) in cart_ids if cart_ids else None
        result.append(
            ArtworkRead(
                id=art.id, title=art.title, description=art.description, category=art.category,
                price=art.price, tags=art.tags, quantity=art.quantity, isSold=art.isSold,
                images=art.images, createdAt=art.createdAt, artistId=art.artistId,
                how_many_like={"like_count": like_count}, forSale=art.forSale,
                artist=ArtworkArtist(id=art.artist.id, username=art.artist.username, profileImage=art.artist.profileImage),
                isInCart=is_in_cart
            )
        )
    return result


@router.get("/artworks/{artwork_id}", response_model=ArtworkRead)
def get_artwork_route(artwork_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    db_artwork = artworks_crud.get_artwork(db, artwork_id)
    if not db_artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    like_count = len(db_artwork.likes) if db_artwork.likes else 0
    is_in_cart: Optional[bool] = None
    if user:
        cart_item = db.query(models.Cart).filter(
            models.Cart.userId == user.id, models.Cart.artworkId == db_artwork.id
        ).first()
        is_in_cart = bool(cart_item)

    return ArtworkRead(
        id=db_artwork.id, title=db_artwork.title, description=db_artwork.description,
        category=db_artwork.category, price=db_artwork.price, tags=db_artwork.tags,
        quantity=db_artwork.quantity, isSold=db_artwork.isSold, images=db_artwork.images,
        createdAt=db_artwork.createdAt, artistId=db_artwork.artistId,
        artist=ArtworkArtist(id=db_artwork.artist.id, username=db_artwork.artist.username, profileImage=db_artwork.artist.profileImage),
        how_many_like={"like_count": like_count}, isInCart=is_in_cart, forSale=db_artwork.forSale
    )


@router.get("/{user_id}/artworks", response_model=List[ArtworkRead])
def get_user_artworks(user_id: UUID, db: Session = Depends(get_db)):
    return artworks_crud.get_artworks_by_user(db, user_id=user_id)

# -------------------------
# SEARCH
# -------------------------

@router.get("/search/artworks", response_model=List[ArtworkRead])
def search_artworks(query: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    return search_crud.search_artworks(db, query)


@router.get("/search/user", response_model=List[UserSearch])
def search_users(query: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    return search_crud.search_users(db, query)


@router.get("/artworks/category/{category}", response_model=List[ArtworkCategory])
def read_artworks_by_category(category: str, db: Session = Depends(get_db)):
    return search_crud.get_artworks_by_category(db, category)


@router.get("/artworks/filter", response_model=List[ArtworkRead])
def get_artworks_with_filters(
    title: Optional[str] = None, price: Optional[float] = None, category: Optional[str] = None,
    artist_name: Optional[str] = None, location: Optional[str] = None, tags: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return search_crud.get_artworks_with_artist_filters(db, title=title, price=price,
                                                        category=category, artist_name=artist_name,
                                                        location=location, tags=tags)

# -------------------------
# REVIEWS (Public)
# -------------------------

@router.get("/reviews/artwork/{artwork_id}", response_model=List[ReviewRead])
def get_reviews_for_artwork(artwork_id: UUID, db: Session = Depends(get_db)):
    return review_crud.list_reviews_for_artwork(db, artwork_id)

# -------------------------
# RECOMMENDATION
# -------------------------

@router.get("/recommend/{artwork_id}", response_model=List[ArtworkRead])
def recommendation_engine(artwork_id: UUID, db: Session = Depends(get_db)):
    return recmmendation_crud.get_recommendation(db, artwork_id=artwork_id)

# -------------------------
# LIKES ENDPOINTS
# -------------------------

@router.get("/likes/{artwork_id}/count", response_model=LikeCountResponse)
def get_like_count(artwork_id: UUID, db: Session = Depends(get_db)):
    count = likes_crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}

# -------------------------
# COMMENTS ENDPOINTS
# -------------------------

@router.get("/artworks/{artwork_id}/comments", response_model=List[CommentRead])
def get_comments(artwork_id: str, db: Session = Depends(get_db)):
    return comment_crud.get_comments_by_artwork(db, artwork_id)