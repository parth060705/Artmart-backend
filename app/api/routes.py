from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session  
from fastapi import Query, Form
from uuid import UUID
from typing import List, Optional
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import get_current_user
from app.core.auth import get_current_admin
from app.database import get_db
from app.models.models import User
from datetime import timedelta
from app.core import auth
from app.crud import crud
from app.crud.crud import get_artworks_with_artist_filters, get_users_filters
from app.crud.crud import serialize_user
from app.models import models
from sqlalchemy.orm import joinedload


from app.schemas.schemas import (
    UserCreate, UserRead, ProfileImageResponse, UserUpdate, UserSearch, ArtworkMe,
    Token, ArtworkCreate, ArtworkRead, ArtworkCreateResponse, ArtworkDelete,
    ArtworkUpdate, ArtworkCategory, UserBaseAdmin, ArtworkAdmin, ArtworkArtist,
    OrderCreate, OrderRead, OrderDelete, ReviewCreate, ReviewRead,WishlistCreate,
    WishlistRead, WishlistCreatePublic, CartCreate, CartRead, CartCreatePublic,
    LikeCountResponse, HasLikedResponse, CommentCreate, CommentRead, FollowList,
    FollowFollowers, DeleteMessageUser, UserUpdateAdmin
)

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# FOR ADMIN LEVEL ROUTES
admin_router = APIRouter(
    tags=["admin"],
    dependencies=[Depends(get_current_admin)]
)

# ------------------------------------------
# AUTHORIZATION & AUTHENTICATION ENDPOINTS
# ------------------------------------------

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
        )

    access_token = auth.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    username = auth.decode_access_token(refresh_token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access_token = auth.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# -------------------------
# USER ENDPOINTS
# -------------------------

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

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

# -------------------------
# SEARCH ENDPOINTS
# -------------------------

@router.get("/artworks/search", response_model=List[ArtworkRead])
def search_artworks(
    query: str = Query(..., min_length=2, description="Search artworks"),
    db: Session = Depends(get_db)
):
    return crud.search_artworks(db, query)

@router.get("/search/user", response_model=List[UserSearch])
def search_users(
    query: str = Query(..., min_length=2, description="Search artist"),
    db: Session = Depends(get_db)
):
    return crud.search_users(db, query)

@router.get("/artworks/category/{category}", response_model=List[ArtworkCategory])
def read_artworks_by_category(category: str, db: Session = Depends(get_db)):
    return crud.get_artworks_by_category(db, category)

@router.get("/artworks/filter", response_model=List[ArtworkRead])
def get_artworks_with_filters(
    title: Optional[str] = None,
    price: Optional[float] = None,
    category: Optional[str] = None,
    artist_name: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return get_artworks_with_artist_filters(
        db,
        title=title,
        price=price,
        category=category,
        artist_name=artist_name,
        location=location
    )

# -------------------------
# ARTWORK ENDPOINTS
# -------------------------

@user_router.post("/artworks", response_model=ArtworkCreateResponse)
def create_artwork(
    title: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    files: List[UploadFile] = File(...),  # MULTIPLE files now
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artwork_data = ArtworkCreate(
        title=title,
        description=description,
        price=price,
        category=category,
    )
    return crud.create_artwork(
        db=db,
        artwork_data=artwork_data,
        user_id=current_user.id,
        files=files,  # <-- List of UploadFile
    )

@user_router.patch("/update/artworks/{artwork_id}", response_model=ArtworkRead)
def update_artwork(
    artwork_id: UUID,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    isSold: Optional[bool] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_files = [
        f for f in (files or [])
        if isinstance(f, UploadFile) and f.filename and f.content_type != "application/octet-stream"
    ]

    artwork_update = ArtworkUpdate(
        title=title,
        description=description,
        category=category,
        price=price,
        isSold=isSold
    )

    return crud.update_artwork(
        db=db,
        artwork_id=str(artwork_id),
        user_id=str(current_user.id),
        artwork_update=artwork_update,
        files=valid_files  # pass only real files
    )

@user_router.delete("/artworks/{artwork_id}", response_model=ArtworkDelete)
def delete_artwork(
    artwork_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    return crud.delete_artwork(db, artwork_id=artwork_id, user_id=current_user.id)

@router.get("/artworks", response_model=List[ArtworkRead])
def list_artworks_route(db: Session = Depends(get_db)):
    artworks = crud.list_artworks(db)
    result = []
    for art in artworks:
        like_count = len(art.likes) if art.likes else 0
        result.append(
            ArtworkRead(
                id=art.id,
                title=art.title,
                description=art.description,
                category=art.category,
                price=art.price,
                isSold=art.isSold,
                images=art.images,
                createdAt=art.createdAt,
                artistId=art.artistId,
                how_many_like={"like_count": like_count},
                artist=ArtworkArtist(
                    username=art.artist.username,
                    profileImage=art.artist.profileImage
                ),
            )
        )
    return result

@router.get("/artworks/{artwork_id}", response_model=ArtworkRead)
def get_artwork(artwork_id: UUID, db: Session = Depends(get_db)):
    db_artwork = db.query(models.Artwork).options(joinedload(models.Artwork.artist)).filter(models.Artwork.id == str(artwork_id)).first()
    if not db_artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    like_count = len(db_artwork.likes) if db_artwork.likes else 0
    return ArtworkRead(
        id=db_artwork.id,
        title=db_artwork.title,
        description=db_artwork.description,
        category=db_artwork.category,
        price=db_artwork.price,
        isSold=db_artwork.isSold,
        images=db_artwork.images,
        createdAt=db_artwork.createdAt,
        artistId=db_artwork.artistId,
        artist=ArtworkArtist(
            username=db_artwork.artist.username,
            profileImage=db_artwork.artist.profileImage
        ),
        how_many_like={"like_count": like_count}
    )

# -------------------------
# LIKES ENDPOINTS
# -------------------------

@user_router.post("/likes/{artwork_id}", response_model=LikeCountResponse)
def like_artwork(artwork_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    crud.like_artwork(db, current_user.id, artwork_id)
    count = crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}

@user_router.delete("/likes/{artwork_id}", response_model=LikeCountResponse)
def unlike_artwork(artwork_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    crud.unlike_artwork(db, current_user.id, artwork_id)
    count = crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}

@router.get("/likes/{artwork_id}/count", response_model=LikeCountResponse)
def get_like_count(artwork_id: UUID, db: Session = Depends(get_db)):
    count = crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}

@user_router.get("/likes/{artwork_id}/status", response_model=HasLikedResponse)
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

@user_router.post("/comments/{artwork_id}", status_code=status.HTTP_201_CREATED)
def post_comment(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_comment(db=db, user_id=current_user.id, comment_data=comment_data)

@router.get("/artworks/{artwork_id}/comments", response_model=List[CommentRead])
def get_comments(artwork_id: str, db: Session = Depends(get_db)):
    return crud.get_comments_by_artwork(db, artwork_id)

# -------------------------
# ORDER ENDPOINTS
# -------------------------

@user_router.post("/orders", response_model=OrderRead)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_order(db, order_data, user_id=current_user.id)

@user_router.get("/orders/my", response_model=List[OrderRead])
def get_my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.list_orders_for_user(db, user_id=current_user.id)

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

# -------------------------
# CART ENDPOINTS
# -------------------------

@user_router.post("/cart", response_model=CartCreatePublic)
def add_to_cart(item: CartCreatePublic, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    internal_item = CartCreate(userId=current_user.id, artworkId=item.artworkId)
    return crud.add_to_cart(db, internal_item, user_id=current_user.id)

@user_router.get("/cart", response_model=List[CartRead])
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.get_user_cart(db, current_user.id)

@user_router.delete("/cart/artwork/{artwork_id}")
def remove_from_cart(artwork_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.remove_cart_item(db, user_id=current_user.id, artwork_id=artwork_id)

# -------------------------
# FOLLOW & FOLLOWER ENDPOINTS
# -------------------------

@user_router.post("/{user_id}/follow")
def follow_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself.")
    
    result = crud.follow_user(db, current_user.id, user_id)
    
    if result.get("status") == "already_following":
        raise HTTPException(status_code=400, detail="Already following.")
    
    return {"msg": "Followed successfully"}

@user_router.delete("/{user_id}/unfollow")
def unfollow_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = crud.unfollow_user(db, current_user.id, user_id)
    
    if result.get("status") == "not_following":
        raise HTTPException(status_code=400, detail="Not following.")
    
    return {"msg": "Unfollowed successfully"}

@user_router.get("/me/followers", response_model=FollowList)
def get_my_followers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    followers = crud.get_followers(db, current_user.id)
    return {
        "users": [serialize_user(user) for user in followers],
        "count": len(followers)
    }

@user_router.get("/me/following", response_model=FollowList)
def get_my_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    following = crud.get_following(db, current_user.id)
    return {
        "users": [serialize_user(user) for user in following],
        "count": len(following)
    }

# ------------------------------------------------------------------------------------------------------------------
#                                        ADMIN & SUPER-ADMIN ENDPOINTS
# -------------------------------------------------------------------------------------------------------------------

                                           # USERS
@admin_router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)
                                           
@admin_router.get("/users", response_model=List[UserBaseAdmin])
def get_all_users(db: Session = Depends(get_db)):
    return crud.list_all_users(db)

@admin_router.delete("/users/{user_id}", response_model=DeleteMessageUser)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    success = crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@admin_router.patch("/update/users/{user_id}", response_model=UserBaseAdmin)
def admin_update_user(
    user_id: str,
    user_update: UserUpdateAdmin,  
    db: Session = Depends(get_db),
):
    update_data = user_update.dict(exclude_unset=True, exclude={"id"})  
    updated_user = crud.update_user_details_admin(
        db=db,
        user_id=user_id,
        update_data=update_data
    )
    return updated_user

@admin_router.get("/user/filter", response_model=List[UserBaseAdmin])
def search_users_filters(
    user_id: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    gender: Optional[str] = None,
    role: Optional[str] = None,
    location: Optional[str] = None,
    
    db: Session = Depends(get_db)
):
    return get_users_filters(
        db,
        user_id=user_id,
        name=name,
        email=email,
        username=username,
        gender=gender,
        role=role,
        location=location
    )

                              # ARTWORKS
@admin_router.get("/artworks", response_model=List[ArtworkAdmin])
def list_artworks(db: Session = Depends(get_db)):
    return crud.list_artworks(db)

@admin_router.delete("/artworks/{artwork_id}", response_model=ArtworkDelete)
def delete_artwork_admin(
    artwork_id: UUID,
    db: Session = Depends(get_db)
):
    return crud.delete_artwork_admin(db=db, artwork_id=artwork_id)

@admin_router.patch("/update/artworks/{artwork_id}", response_model=ArtworkRead)
def update_artwork(
    artwork_id: UUID,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    isSold: Optional[bool] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    ):
    valid_files = [
        f for f in (files or [])
        if isinstance(f, UploadFile) and f.filename and f.content_type != "application/octet-stream"
    ]

    artwork_update = ArtworkUpdate(
        title=title,
        description=description,
        category=category,
        price=price,
        isSold=isSold
    )

    return crud.update_artwork(
        db=db,
        artwork_id=str(artwork_id),
        artwork_update=artwork_update,
        files=valid_files  
    )

@admin_router.get("/artworks/filter", response_model=List[ArtworkRead])
def search_artworks_with_filters(
    artwork_id: Optional[str] = None,
    title: Optional[str] = None,
    price: Optional[float] = None,
    category: Optional[str] = None,
    artist_name: Optional[str] = None,
    location: Optional[str] = None,
    user_id: Optional[str] = None,

    db: Session = Depends(get_db)
):
    return get_artworks_with_artist_filters(
        db,
        artwork_id=artwork_id,
        title=title,
        price=price,
        category=category,
        artist_name=artist_name,
        location=location,
        user_id=user_id
    )

                                    # ORDERS
@admin_router.get("/orders", response_model=List[OrderRead])
def get_all_orders(db: Session = Depends(get_db)):
    return crud.list_all_orders(db)

@admin_router.delete("/orders/{order_id}", response_model=OrderDelete)
def delete_order(order_id: UUID, db: Session = Depends(get_db)):
    return crud.delete_order(db, order_id)


                                    # FOLLOW
@admin_router.get("/follows", response_model=List[FollowFollowers])
def list_follow_followers(db: Session = Depends(get_db)):
    followers = crud.list_follow_followers(db)
    return [
        {
            "username": row.username,
            "profileImage": row.profileImage,
            "follower_id": row.follower_id,
            "followed_id": row.followed_id,
            "created_at": row.created_at
        }
        for row in followers
    ]



#-------------------------------------------------------------------------------------------------------------
__all__ = ["router","user_router","admin_router"]
