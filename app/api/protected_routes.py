from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.schemas.user_schema import UserRead, UserUpdate, ProfileImageResponse, ChangePasswordSchema
from app.schemas.artworks_schemas import ArtworkMe, ArtworkCreateResponse, ArtworkRead, ArtworkDelete, ArtworkCreate, ArtworkUpdate
from app.schemas.likes_schemas import LikeCountResponse, HasLikedResponse
from app.schemas.comment_schemas import CommentCreate
from app.schemas.order_schemas import OrderCreate, OrderRead
from app.schemas.saved_schemas import SavedCreatePublic, SavedRead, SavedCreate
from app.schemas.cart_schemas import CartCreatePublic, CartRead, CartCreate
from app.schemas.review_schemas import ReviewCreate, ReviewRead
from app.schemas.follow_schemas import FollowList, FollowStatus

from app.crud import (
    user_crud, artworks_crud, likes_crud, comment_crud,
    orders_crud, saved_crud, cart_crud, homefeed_crud,
    follow_crud, review_crud
)

user_router = APIRouter(
    tags=["authorized"],
    dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# -------------------------
# USER 
# -------------------------

@user_router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@user_router.patch("/update/users/me", response_model=UserRead)
def update_current_user(
    name: str = Form(None), location: str = Form(None), gender: str = Form(None),
    age: int = Form(None), bio: str = Form(None), pincode: str = Form(None),
    phone: str = Form(None), db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_update = UserUpdate(
        name=name, location=location, gender=gender, age=age,
        bio=bio, pincode=pincode, phone=phone
    )
    updated_user = user_crud.update_user_details(db, user_id=current_user.id, user_update=user_update)
    return {
        "id": updated_user.id,
        "name": updated_user.name,
        "email": updated_user.email,
        "username": updated_user.username,
        "profileImage": updated_user.profileImage,
        "location": updated_user.location,
        "gender": updated_user.gender,
        "age": updated_user.age,
        "bio": updated_user.bio,
        "pincode": updated_user.pincode,
        "phone": updated_user.phone,
        "profile_completion": updated_user.profile_completion,
        "createdAt": updated_user.createdAt,
        "updatedAt": updated_user.updatedAt
    }


@user_router.patch("/update/users/image", response_model=ProfileImageResponse)
def update_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return user_crud.update_user_profile_image(db, current_user.id, file)


@user_router.get("/artworks/me", response_model=List[ArtworkMe])
def read_my_artworks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return artworks_crud.get_artworks_by_user(db, user_id=current_user.id)

@user_router.post("/change-password")
def change_password(
    data: ChangePasswordSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = user_crud.change_user_password(db, current_user, data.old_password, data.new_password)
    
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["detail"])
    
    return {"message": result["detail"]}

# -------------------------
# ARTWORKS
# -------------------------

@user_router.post("/artworks", response_model=ArtworkCreateResponse)
def create_artwork(
    title: str = Form(...), price: float = Form(None), quantity: int = Form(None),
    category: str = Form(...), description: str = Form(None), tags: str = Form(""),
    forSale: bool = Form(False), files: List[UploadFile] = File(...),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    if forSale:
        if price is None or quantity is None:
            raise HTTPException(status_code=400, detail="Price and quantity required if for sale")
    else:
        price = None
        quantity = None

    artwork_data = ArtworkCreate(
        title=title, description=description, price=price,
        quantity=quantity, category=category, tags=tags_list, forSale=forSale
    )
    return artworks_crud.create_artwork(db=db, artwork_data=artwork_data, user_id=current_user.id, files=files)


@user_router.patch("/update/artworks/{artwork_id}", response_model=ArtworkRead)
def update_artwork(
    artwork_id: UUID, title: Optional[str] = Form(None), description: Optional[str] = Form(None),
    category: Optional[str] = Form(None), price: Optional[float] = Form(None),
    tags: Optional[list[str]] = Form(None), quantity: Optional[int] = Form(None),
    isSold: Optional[bool] = Form(None), db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artwork_update = ArtworkUpdate(
        title=title, description=description, category=category,
        price=price, tags=tags, quantity=quantity, isSold=isSold
    )
    return artworks_crud.update_artwork(db, artwork_id=str(artwork_id), user_id=str(current_user.id), artwork_update=artwork_update)


@user_router.post("/artworks/{artwork_id}/images", response_model=ArtworkRead)
def add_artwork_images(artwork_id: UUID, files: List[UploadFile] = File(...),
                       db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return artworks_crud.add_artwork_images(db, str(artwork_id), str(current_user.id), files)


@user_router.patch("/artworks/{artwork_id}/images", response_model=ArtworkRead)
def update_artwork_image(artwork_id: UUID, old_public_id: str = Form(...),
                         new_file: UploadFile = File(...),
                         db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return artworks_crud.update_artwork_image(db, str(artwork_id), str(current_user.id), old_public_id, new_file)


@user_router.delete("/artworks/{artwork_id}/images", response_model=ArtworkRead)
def delete_artwork_image(artwork_id: UUID, public_id: str = Form(...),
                         db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return artworks_crud.delete_artwork_image(db, str(artwork_id), str(current_user.id), public_id)


@user_router.delete("/artworks/{artwork_id}", response_model=ArtworkDelete)
def delete_artwork(artwork_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return artworks_crud.delete_artwork(db, artwork_id=artwork_id, user_id=current_user.id)

# -------------------------
# LIKES
# -------------------------

@user_router.post("/likes/{artwork_id}", response_model=LikeCountResponse)
def like_artwork(artwork_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    likes_crud.like_artwork(db, current_user.id, artwork_id)
    count = likes_crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}


@user_router.delete("/likes/{artwork_id}", response_model=LikeCountResponse)
def unlike_artwork(artwork_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    likes_crud.unlike_artwork(db, current_user.id, artwork_id)
    count = likes_crud.get_like_count(db, artwork_id)
    return {"artwork_id": artwork_id, "like_count": count}


@user_router.get("/likes/{artwork_id}/status", response_model=HasLikedResponse)
def check_like_status(artwork_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    has_liked = likes_crud.has_user_liked_artwork(db, current_user.id, artwork_id)
    return {"artwork_id": artwork_id, "user_id": current_user.id, "has_liked": has_liked}

# -------------------------
# COMMENTS
# -------------------------

@user_router.post("/comments/{artwork_id}", status_code=status.HTTP_201_CREATED)
def post_comment(comment_data: CommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return comment_crud.create_comment(db=db, user_id=current_user.id, comment_data=comment_data)

# -------------------------
# ORDERS
# -------------------------

@user_router.post("/orders", response_model=OrderRead)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return orders_crud.create_order(db, order_data, user_id=current_user.id)


@user_router.get("/orders/my", response_model=List[OrderRead])
def get_my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return orders_crud.list_orders_for_user(db, user_id=current_user.id)

# -------------------------
# REVIEWS
# -------------------------

@user_router.post("/reviews", response_model=ReviewRead)
def create_review(review: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return review_crud.create_review(db, review, user_id=current_user.id)

# -------------------------
# SAVED
# -------------------------

@user_router.post("/Saved", response_model=SavedRead)
def add_to_Saved(item: SavedCreatePublic, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    internal_item = SavedCreate(userId=current_user.id, artworkId=item.artworkId)
    return saved_crud.add_to_Saved(db, internal_item, user_id=current_user.id)


@user_router.get("/Saved", response_model=List[SavedRead])
def get_Saved(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return saved_crud.get_user_Saved(db, current_user.id)


@user_router.delete("/Saved/artwork/{artwork_id}")
def remove_from_Saved(artwork_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return saved_crud.remove_Saved_item(db, user_id=current_user.id, artwork_id=artwork_id)

# -------------------------
# CART
# -------------------------

@user_router.post("/cart", response_model=CartCreate)
def add_to_cart(item: CartCreatePublic, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    internal_item = CartCreate(userId=current_user.id, artworkId=item.artworkId, purchase_quantity=item.purchase_quantity)
    return cart_crud.add_to_cart(db, internal_item)


@user_router.get("/cart", response_model=List[CartRead])
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cart_crud.get_user_cart(db, current_user.id)


@user_router.delete("/cart/artwork/{artwork_id}")
def remove_from_cart(artwork_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cart_crud.remove_cart_item(db, user_id=current_user.id, artwork_id=artwork_id)

# -------------------------
# FOLLOW
# -------------------------

@user_router.post("/{user_id}/follow")
def follow_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself.")
    result = follow_crud.follow_user(db, current_user.id, user_id)
    if result.get("status") == "already_following":
        raise HTTPException(status_code=400, detail="Already following.")
    return {"msg": "Followed successfully"}


@user_router.delete("/{user_id}/unfollow")
def unfollow_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = follow_crud.unfollow_user(db, current_user.id, user_id)
    if result.get("status") == "not_following":
        raise HTTPException(status_code=400, detail="Not following.")
    return {"msg": "Unfollowed successfully"}


@user_router.get("/me/followers", response_model=FollowList)
def get_my_followers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    followers = follow_crud.get_followers(db, current_user.id)
    return {"users": [follow_crud.serialize_user(user) for user in followers], "count": len(followers)}


@user_router.get("/me/following", response_model=FollowList)
def get_my_following(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    following = follow_crud.get_following(db, current_user.id)
    return {"users": [follow_crud.serialize_user(user) for user in following], "count": len(following)}


@user_router.get("/{user_id}/follow", response_model=FollowStatus)
def is_following_check(user_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    following = follow_crud.is_user_following(db, current_user.id, user_id)
    return FollowStatus(is_following=following)

# -------------------------
# HOMEFEED
# -------------------------

@user_router.get("/homefeed", response_model=List[ArtworkRead])
def home_feed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return homefeed_crud.get_home_feed(db, current_user)
