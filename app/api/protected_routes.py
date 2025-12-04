from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models import models


from app.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, ArtistReview
from app.schemas.user_schema import UserRead, UserUpdate, ProfileImageResponse, ChangePasswordSchema
from app.schemas.artworks_schemas import ArtworkMe, ArtworkCreateResponse, ArtworkRead, ArtworkDelete, ArtworkCreate, ArtworkUpdate, ArtworkArtist, ArtworkMeResponse
from app.schemas.likes_schemas import LikeCountResponse, HasLikedResponse
from app.schemas.comment_schemas import CommentCreate
from app.schemas.order_schemas import OrderCreate, OrderRead
from app.schemas.saved_schemas import SavedCreatePublic, SavedRead, SavedCreate
from app.schemas.cart_schemas import CartCreatePublic, CartRead, CartCreate
from app.schemas.review_schemas import ReviewCreate, ReviewRead
from app.schemas.follow_schemas import FollowList, FollowStatus
from app.schemas.artistreview_schemas import ArtistReviewRead, ArtistReviewCreate
from app.util import util_artistrank

from app.crud import (
    user_crud, artworks_crud, likes_crud, comment_crud,
    orders_crud, saved_crud, cart_crud, homefeed_crud,
    follow_crud, review_crud, artistreview_crud, community_crud,
    community_members_crud
)

from app.schemas.community_schemas import (
    CommunityCreate,
    CommunityResponse,
    CommunityUpdate,
    CommunityMemberResponse,
    CommunitySearchResponse
)

user_router = APIRouter(
    tags=["authorized"],
    dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# -------------------------
# USER 
# -------------------------

# @user_router.get("/me", response_model=UserRead)
# def read_users_me(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     if not current_user:
#         raise HTTPException(status_code=404, detail="User not found")

#     rating_info = util_artistrank.get_user_rating_info(db, current_user.id)

#     # Build complete response
#     response_data = {
#         "id": current_user.id,
#         "name": current_user.name,
#         "email": current_user.email,
#         "username": current_user.username,
#         "profileImage": current_user.profileImage,
#         "location": current_user.location,
#         "gender": current_user.gender,
#         "age": current_user.age,
#         "bio": current_user.bio,
#         "pincode": current_user.pincode,
#         "phone": current_user.phone,
#         "createdAt": current_user.createdAt,
#         "updatedAt": current_user.updatedAt,
#         "profile_completion": current_user.profile_completion,
#         "avgRating": rating_info["avgRating"],
#         "weightedRating": rating_info["weightedRating"],
#         "reviewCount": rating_info["reviewCount"],
#         "rank": rating_info["rank"],
#         "role": current_user.role,

#     }

#     return response_data

@user_router.get("/me", response_model=UserRead)
def read_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")

    rating_info = util_artistrank.get_user_rating_info(db, current_user.id)

    # Followers & Following
    followers = follow_crud.get_followers(db, current_user.id)
    following = follow_crud.get_following(db, current_user.id)

    followers_data = {
        "users": [follow_crud.serialize_user(u) for u in followers],
        "count": len(followers)
    }

    following_data = {
        "users": [follow_crud.serialize_user(u) for u in following],
        "count": len(following)
    }

    # Build complete response
    response_data = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "username": current_user.username,
        "profileImage": current_user.profileImage,
        "location": current_user.location,
        "gender": current_user.gender,
        "age": current_user.age,
        "bio": current_user.bio,
        "pincode": current_user.pincode,
        "phone": current_user.phone,
        "createdAt": current_user.createdAt,
        "updatedAt": current_user.updatedAt,
        "profile_completion": current_user.profile_completion,
        "avgRating": rating_info["avgRating"],
        "weightedRating": rating_info["weightedRating"],
        "reviewCount": rating_info["reviewCount"],
        "rank": rating_info["rank"],
        "role": current_user.role,
        "followers": followers_data,
        "following": following_data
    }

    return response_data

# @user_router.get("/me", response_model=UserRead)
# def read_users_me(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     return user_crud.get_user_with_rating(db, current_user.id)


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
    return artworks_crud.get_artworks_by_me(db, user_id=current_user.id)

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
# ARTIST REVIEWS
# -------------------------

@user_router.post("/artistreview", response_model=ArtistReviewRead, status_code=status.HTTP_201_CREATED)
def post_artist_review(
    item: ArtistReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Prevent users from reviewing themselves
    if current_user.id == str(item.artistId):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot review yourself."
        )

    # Use CRUD function
    db_review = artistreview_crud.create_artist_review(db, item, current_user.id)
    return db_review

@user_router.get("/me/artistreview", response_model=list[ArtistReviewRead])
def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reviews = artistreview_crud.reviews_for_artist(db, current_user.id)
    return reviews

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

# @user_router.get("/homefeed", response_model=List[ArtworkRead])
# def home_feed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     return homefeed_crud.get_home_feed(db, current_user)

@user_router.get("/homefeed", response_model=List[ArtworkRead])
def home_feed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    cart_ids = None
    saved_ids = None
    liked_ids = None

    if current_user:
        cart_items = db.query(models.Cart.artworkId).filter_by(userId=str(current_user.id)).all()
        cart_ids = {str(item.artworkId) for item in cart_items}

        saved_items = db.query(models.Saved.artworkId).filter_by(userId=str(current_user.id)).all()
        saved_ids = {str(item.artworkId) for item in saved_items}

        liked_items = db.query(models.ArtworkLike.artworkId).filter_by(userId=str(current_user.id)).all()
        liked_ids = {str(item.artworkId) for item in liked_items}

    artworks = homefeed_crud.get_home_feed(db, current_user)

    result = []
    for art in artworks:
        like_count = len(art.likes) if art.likes else 0
        is_in_cart = str(art.id) in cart_ids if cart_ids else None
        is_saved = str(art.id) in saved_ids if saved_ids else None
        is_like = str(art.id) in liked_ids if liked_ids else None

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
                status=art.status,
                how_many_like={"like_count": like_count},
                forSale=art.forSale,
                artist=ArtworkArtist(
                    id=art.artist.id,
                    username=art.artist.username,
                    profileImage=art.artist.profileImage
                ),
                isInCart=is_in_cart,
                isSaved=is_saved,
                isLike=is_like
            )
        )
    return result

# -----------------------------
# COMMUNITY
# -----------------------------
# CREATE
@user_router.post("/community", response_model=CommunitySearchResponse)
def create_new_community(
    name: str = Form(...),
    description: str = Form(None),
    bannerImage: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    data = CommunityCreate(
        name=name,
        description=description,
        bannerImage=None  # replaced by cloudinary URL in CRUD
    )

    community = community_crud.create_community(
        db=db,
        owner_id=current_user.id,
        data=data,
        banner_file=bannerImage
    )

    return community

# UPDATE
# @user_router.patch("/{community_id}", response_model=CommunitySearchResponse)
# def update_community_route(
#     community_id: str,
#     name: Optional[str] = Form(None),
#     description: Optional[str] = Form(None),
#     bannerImage: Optional[UploadFile] = File(None),
#     db: Session = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     data = CommunityUpdate(
#         name=name,
#         description=description
#     )

#     updated = community_crud.update_community(
#         db=db,
#         community_id=community_id,
#         data=data,
#         banner_file=bannerImage
#     )

#     return updated

# DELETE COMMUNITY
@user_router.delete("/delete/community/{community_id}")
def delete_existing_community(
    community_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    community = community_crud.get_community(db, community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # Only owner can delete
    if community.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    community_crud.delete_community(db, community_id)
    return {"message": "Community deleted successfully"}

# -----------------------------
# COMMUNITY MEMBERS
# -----------------------------
# ADD ME
@user_router.post("/{community_id}/members", response_model=CommunityMemberResponse)
def add_me_to_community(
    community_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    member = community_members_crud.add_member(db, community_id, current_user.id)
    return member

# REMOVE ME
@user_router.delete("/{community_id}/members")
def remove_me_from_community(
    community_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    community_members_crud.remove_member(db, community_id, current_user.id)
    return {"message": "Member removed"}

# GET COMMUNITY MEMBERS LIST
@user_router.get("/{community_id}/members", response_model=list[CommunityMemberResponse])
def get_community_members(
    community_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user) 
):
    members = community_members_crud.list_members(db, community_id)
    return members

# REMOVE USER BY OWNER
@user_router.delete("/{community_id}/members/{user_id}")
def owner_remove_member(
    community_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Optional: check if current_user is the owner
    community = db.query(models.Community).filter(models.Community.id == community_id).first()
    if not community:
        raise HTTPException(404, "Community not found")
    if community.owner_id != current_user.id:
        raise HTTPException(403, "Only owner can remove members")

    community_members_crud.remove_member_by_owner(db, community_id, user_id)
    return {"message": "Member removed by owner successfully"}
