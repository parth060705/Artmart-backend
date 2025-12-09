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

from app.schemas.user_schema import UserCreate, UserRead, UserSearch, Token, ResetPasswordWithOTPSchema, UserAuthResponse
from app.schemas.artworks_schemas import ArtworkRead, ArtworkCategory, ArtworkArtist
from app.schemas.review_schemas import ReviewRead
from app.schemas.likes_schemas import LikeCountResponse
from app.schemas.comment_schemas import CommentRead
from app.schemas.artistreview_schemas import ArtistReviewRead, ArtistRatingSummary
from app.schemas.saved_schemas import SavedRead
from app.schemas.error_response_schemas import standard_responses

from app.core.smtp_otp import send_otp_email
from fastapi import BackgroundTasks
from app.crud import user_crud, search_crud, artworks_crud, recmmendation_crud,review_crud, likes_crud, comment_crud, artistreview_crud, googleauth_crud, saved_crud, community_crud
from passlib.context import CryptContext
from app.util import util
from app.core.redis_client import get_redis_client
import json
from app.util import util_cache

from app.schemas.community_schemas import (
    CommunityCreate,
    CommunityResponse,
    CommunityUpdate,
    CommunitySearchResponse,
    CommunitySearch
)
from app.schemas.community_artwork_schemas import CommunityArtworkCreate, CommunityArtworkResponse
from app.crud import community_artwork_crud

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


router = APIRouter(
    tags=["public"]
)

# -------------------------
# AUTH ROUTES
# -------------------------

# @router.post("/login", response_model=Token)
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = user_crud.get_user_by_username(db, form_data.username)
#     if not user or not auth.verify_password(form_data.password, user.passwordHash):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

#     access_token = auth.create_token(
#         data={"sub": user.username}, expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     refresh_token = auth.create_token(
#         data={"sub": user.username}, expires_delta=timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
#     )
#     return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# @router.post("/refresh", response_model=Token)
# def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
#     username = auth.decode_access_token(refresh_token)
#     if username is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

#     user = user_crud.get_user_by_username(db, username)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     new_access_token = auth.create_token(
#         data={"sub": user.username}, expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     return {"access_token": new_access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = user_crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.passwordHash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token = auth.create_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth.create_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    decoded = auth.decode_access_token(refresh_token)
    if not decoded or not decoded.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = decoded["user_id"]
    username = decoded.get("username")

    # Try to find user by ID first
    user = db.query(models.User).filter(models.User.id == user_id).first()

    # Fallback to username (for backward compatibility)
    if not user and username:
        user = user_crud.get_user_by_username(db, username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Create a fresh access token with both id + username
    new_access_token = auth.create_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# -------------------------
# USER (Public)
# -------------------------

# google register and login
@router.post(
    "/google",
    response_model=UserAuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Sign in or register using Google OAuth",
)
def google_auth(id_token: str = Form(...), db: Session = Depends(get_db)):
    result = googleauth_crud.authenticate_with_google(db, id_token)
    return {
        "tokens": {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
        },
    }

    
#---------------------------------------------------------------------------------------------------------------------

@router.post("/register", response_model=UserRead,  responses=standard_responses)
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
    
     # Validate required fields
    missing_fields = []
    if not name:
        missing_fields.append("name")
    if not username:
        missing_fields.append("username")
    if not password:
        missing_fields.append("password")
    if not email:
        missing_fields.append("email")

    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )

    if email and user_crud.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if username and user_crud.get_user_by_username(db, username):
        suggestions = util.suggest_usernames(db, username)
        raise HTTPException(status_code=400, detail={"message": "Username taken", "suggestions": suggestions})

    user_data = UserCreate(
        name=name, email=email, username=username, password=password,
        location=location, gender=gender, bio=bio, age=age, phone=phone,
        pincode=pincode, isAgreedtoTC=isAgreedtoTC
    )
    return user_crud.create_user(db=db, user=user_data)

@router.get("/user/{user_id}", response_model=UserSearch)
def read_user(
    user_id: str,  # can be UUID or username
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    # Try to interpret `user_id` as UUID
    from uuid import UUID

    user = None
    try:
        user_uuid = UUID(user_id)
        user = user_crud.get_user(db, user_uuid, current_user)
    except ValueError:
        # If not a UUID, search by username
        user_obj = db.query(models.User).filter(models.User.username == user_id).first()
        if user_obj:
            user = user_crud.get_user(db, user_obj.id, current_user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.post("/forgotpassword")
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


@router.post("/resetpassword")
def reset_password(data: ResetPasswordWithOTPSchema, db: Session = Depends(get_db)):
    user_crud.reset_password(db, email=data.email, otp=data.otp, new_password=data.new_password)
    return {"message": "Password updated successfully"}

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
# ARTWORK (Public)
# -------------------------

# @router.get("/artworks", response_model=List[ArtworkRead])
# def list_artworks_route(db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):

#     artworks = db.query(models.Artwork).options(
#         subqueryload(models.Artwork.artist),
#         subqueryload(models.Artwork.likes),
#         subqueryload(models.Artwork.images)
#     ).all()
#     # only artworks that is for sale
#     # artworks_for_sale = [a for a in artworks if a.forSale]

#     cart_ids = None
#     saved_ids = None
#     liked_ids = None

#     if current_user:
#         cart_items = db.query(models.Cart.artworkId).filter_by(userId=str(current_user.id)).all()
#         cart_ids = {item.artworkId for item in cart_items}

#         saved_items = db.query(models.Saved.artworkId).filter_by(userId=str(current_user.id)).all()
#         saved_ids = {item.artworkId for item in saved_items}

#         liked_items = db.query(models.ArtworkLike.artworkId).filter_by(userId=str(current_user.id)).all()
#         liked_ids = {item.artworkId for item in liked_items}

#     result = []
#     # for art in artworks_for_sale:
#     for art in artworks:
#         like_count = len(art.likes) if art.likes else 0
#         is_in_cart = str(art.id) in cart_ids if cart_ids else None
#         is_saved = str(art.id) in saved_ids if saved_ids else None
#         is_like = art.id in liked_ids if liked_ids else None

#         result.append(
#             ArtworkRead(
#                 id=art.id,
#                 title=art.title,
#                 description=art.description,
#                 category=art.category,
#                 price=art.price,
#                 tags=art.tags,
#                 quantity=art.quantity,
#                 isSold=art.isSold,
#                 images=art.images,
#                 createdAt=art.createdAt,
#                 artistId=art.artistId,
#                 how_many_like={"like_count": like_count},
#                 forSale=art.forSale,
#                 artist=ArtworkArtist(
#                     id=art.artist.id,
#                     username=art.artist.username,
#                     profileImage=art.artist.profileImage
#                 ),
#                 isInCart=is_in_cart,
#                 isSaved=is_saved,
#                 isLike=is_like
#             )
#         )
#     return result

@router.get("/artworks", response_model=List[ArtworkRead])
def list_artworks_route(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):

    artworks = (
        db.query(models.Artwork)
        .options(
            subqueryload(models.Artwork.artist),
            subqueryload(models.Artwork.likes),
            subqueryload(models.Artwork.images)
        )
        .order_by(models.Artwork.createdAt.desc())  # ⬅️ most recent first
        .all()
    )

    result = []
    for art in artworks:
        result.append(
            ArtworkRead(
                id=art.id,
                title=art.title,
                description=art.description,
                category=art.category,
                price=art.price,
                tags=art.tags,
                quantity=art.quantity,
                isSold=art.isSold,
                images=art.images,
                createdAt=art.createdAt,
                artistId=art.artistId,
                forSale=art.forSale,
                status=art.status,
                artist=ArtworkArtist(
                    id=art.artist.id,
                    username=art.artist.username,
                    profileImage=art.artist.profileImage
                ),
            )
        )
    return result


# @router.get("/artworks", response_model=List[ArtworkRead])
# def get_recommendations(
#     db: Session = Depends(get_db),
#     current_user=Depends(get_current_user_optional)
# ):
#     artworks = recmmendation_crud.list_recommendations(db, current_user)

#     result = []
#     for art in artworks:
#         result.append(
#             ArtworkRead(
#                 id=art.id,
#                 title=art.title,
#                 description=art.description,
#                 category=art.category,
#                 price=art.price,
#                 tags=art.tags,
#                 quantity=art.quantity,
#                 isSold=art.isSold,
#                 images=art.images,
#                 createdAt=art.createdAt,
#                 artistId=art.artistId,
#                 forSale=art.forSale,
#                 artist=ArtworkArtist(
#                     id=art.artist.id,
#                     username=art.artist.username,
#                     profileImage=art.artist.profileImage
#                 ),
#             )
#         )

#     return result


#______________________________________________________________________________________

@router.get("/artworks/{artwork_id}", response_model=ArtworkRead)
def get_artwork_route(artwork_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    db_artwork = artworks_crud.get_artwork(db, artwork_id)
    if not db_artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    like_count = len(db_artwork.likes) if db_artwork.likes else 0
    is_in_cart: Optional[bool] = None
    is_saved: Optional[bool] = None
    is_like: Optional[bool] = None

    if user:
        # Check if in cart
        cart_item = db.query(models.Cart).filter(
            models.Cart.userId == user.id, models.Cart.artworkId == db_artwork.id
        ).first()
        is_in_cart = bool(cart_item)

        # Check if saved
        saved_item = db.query(models.Saved).filter(
            models.Saved.userId == user.id, models.Saved.artworkId == db_artwork.id
        ).first()
        is_saved = bool(saved_item)

        # ✅ Check if liked
        liked_item = db.query(models.ArtworkLike).filter(
            models.ArtworkLike.userId == user.id, models.ArtworkLike.artworkId == db_artwork.id
        ).first()
        is_like = bool(liked_item)

    return ArtworkRead(
        id=db_artwork.id,
        title=db_artwork.title,
        description=db_artwork.description,
        category=db_artwork.category,
        price=db_artwork.price,
        tags=db_artwork.tags,
        quantity=db_artwork.quantity,
        isSold=db_artwork.isSold,
        images=db_artwork.images,
        createdAt=db_artwork.createdAt,
        artistId=db_artwork.artistId,
        artist=ArtworkArtist(
            id=db_artwork.artist.id,
            username=db_artwork.artist.username,
            profileImage=db_artwork.artist.profileImage
        ),
        how_many_like={"like_count": like_count},
        isInCart=is_in_cart,
        isSaved=is_saved,
        isLike=is_like,
        forSale=db_artwork.forSale,
        status=db_artwork.status
    )


@router.get("/{user_id}/artworks", response_model=List[ArtworkRead])
def get_user_artworks(user_id: UUID, db: Session = Depends(get_db)):
    return artworks_crud.get_artworks_by_user(db, user_id=user_id)

# -------------------------
# REVIEWS (Public)
# -------------------------

@router.get("/reviews/artwork/{artwork_id}", response_model=List[ReviewRead])
def get_reviews_for_artwork(artwork_id: UUID, db: Session = Depends(get_db)):
    return review_crud.list_reviews_for_artwork(db, artwork_id)

# -------------------------
# ARTIST REVIEWS
# -------------------------

# @router.get("/artists/top", response_model=list[ArtistRatingSummary])
# def get_top_artists(db: Session = Depends(get_db)):
#     """
#     Get all reviews for a specific artist,
#     sorted from highest rating to lowest.
#     """
#     return artistreview_crud.list_artists_by_rating(db)

@router.get("/artists/top", response_model=list[ArtistRatingSummary])
async def get_top_artists(db: Session = Depends(get_db)):
    """
    Get all artists sorted by rating.
    Cached in Redis until midnight.
    """
    cache_key = "artists:top"

    # 1️⃣ Try Redis cache first
    cached_data = await util_cache.get_cache(cache_key)
    if cached_data:
        print("🎯 Cache hit for artists:top")
        return cached_data

    # 2️⃣ Cache miss — query database
    print("💾 Cache miss for artists:top — querying DB")
    data = artistreview_crud.list_artists_by_rating(db)

    # 3️⃣ Convert ORM objects → dicts (for JSON serialization)
    serialized = [
        d.dict() if hasattr(d, "dict") else
        d.__dict__ if hasattr(d, "__dict__") else dict(d)
        for d in data
    ]

    # 4️⃣ Cache until midnight
    await util_cache.set_cache_until_midnight(cache_key, serialized)
    print("✅ Cached artists:top until midnight")

    return serialized

# -------------------------
# RECOMMENDATION
# -------------------------

@router.get("/{artwork_id}/recommendations", response_model=List[ArtworkRead])
def get_artwork_recommendations(
    artwork_id: UUID,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recommended artworks based on the title, category, and tags of the given artwork ID.
    Always returns up to 'limit' artworks.
    """
    recommended = recmmendation_crud.recommend_artworks(db, artwork_id, limit=limit)
    # Convert to Pydantic models
    return [ArtworkRead.model_validate(art) for art in recommended]

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

# -------------------------
# SAVED ENDPOINTS
# -------------------------

@router.get("/saved/{user_id}", response_model=List[SavedRead])
def get_saved_public(user_id: UUID, db: Session = Depends(get_db)):
    return saved_crud.get_user_Saved(db, user_id=user_id)

# -------------------------
# SAVED ENDPOINTS
# -------------------------

@router.get("/moderation/pending")
def get_pending_moderation(db: Session = Depends(get_db)):
    items = db.query(models.ModerationQueue).filter_by(checked=False).all()
    return items

# -----------------------------
# COMMUNITIES
# -----------------------------
# GET
@router.get("/community", response_model=list[CommunitySearchResponse])
def list_communities(
    db: Session = Depends(get_db)
):
    return community_crud.get_communities(db) 

# GET SPECIFIC COMMUNITY
@router.get("/community/{community_id}", response_model=CommunityResponse)
def get_community_detail(
    community_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)  # Optional login
):
    community = community_crud.get_community(db, community_id)
    if not community:
        raise HTTPException(404, "Community not found")

    # Enforce privacy
    if community.type == models.CommunityType.private:
        # If no user logged in
        if not current_user:
            raise HTTPException(403, "Private community. Login required.")

        # Check if user is a member OR owner
        member = db.query(models.CommunityMember).filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == current_user.id
        ).first()

        if not member and current_user.id != community.owner_id:
            raise HTTPException(403, "Private community. Access denied.")

    return community

# SEARCH COMMUNITY
@router.get("/communities/search", response_model=List[CommunitySearch])
def search_communities_route(
    query: Optional[str] = None,
    db: Session = Depends(get_db),
):
    communities = community_crud.search_communities(
        db=db,
        query=query,
    )
    return communities

# -----------------------------
# COMMUNITY ARTWORK
# -----------------------------

# Get all posts in a community
@router.get("/community/{community_id}/artworks",response_model=list[CommunityArtworkResponse])
def list_community_artworks(
    community_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else None

    posts = community_artwork_crud.get_community_artworks(
        db=db,
        community_id=community_id,
        user_id=user_id
    )
    return posts


# Get single post
# @router.get("/artworks/{artwork_post_id}", response_model=CommunityArtworkResponse)
# def get_community_artwork(artwork_post_id: str, db: Session = Depends(get_db)):
#     return community_artwork_crud.get_community_artwork(db, artwork_post_id)