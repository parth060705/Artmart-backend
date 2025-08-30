from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session  
from fastapi import Form
from uuid import UUID
from typing import List, Optional
from app.core.auth import get_current_admin
from app.database import get_db
from app.crud import crud
from app.crud.crud import get_artworks_with_artist_filters, get_users_filters
from fastapi import APIRouter, Depends
from app.schemas.schemas import (
    UserCreate, UserRead,
    ArtworkRead, ArtworkDelete,
    ArtworkUpdate,UserBaseAdmin, ArtworkAdmin,
    OrderRead, OrderDelete,
    FollowFollowers, DeleteMessageUser, UserUpdateAdmin
)

# FOR ADMIN LEVEL ROUTES
admin_router = APIRouter(
    tags=["admin"],
    dependencies=[Depends(get_current_admin)]
)

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
    quantity: Optional[int] = Form(None),
    tags: Optional [list[str]] = Form(None),
    isSold: Optional[bool] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    # Filter out invalid files
    valid_files = [
        f for f in (files or [])
        if isinstance(f, UploadFile) and f.filename and f.content_type != "application/octet-stream"
    ]

    # Build schema object with fields that were sent
    artwork_update = ArtworkUpdate(
        title=title,
        description=description,
        category=category,
        price=price,
        quantity=quantity,
        tags=tags,
        isSold=isSold
    )

    # Call update logic
    return crud.update_artwork(
        db=db,
        artwork_id=str(artwork_id),
        artwork_update=artwork_update,
        files=valid_files  # Will be [] if no valid files sent
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

