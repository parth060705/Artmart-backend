from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from fastapi import UploadFile
import os
import shutil
from uuid import UUID
from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import schemas
from passlib.context import CryptContext
import cloudinary.uploader
import cloudinary


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# USER OPERATIONS
# -------------------------

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        username=user.username,
        passwordHash=hashed_password,
        role=RoleEnum.user,
        profileImage=str(user.profileImage) if user.profileImage else None,
        location=user.location,
        gender=user.gender,
        age=user.age,
        phone=str(user.phone) if user.phone else None,
        pincode=str(user.pincode) if user.pincode else None 
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_details(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")
    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.username is not None:
        db_user.username = user_update.username
    if user_update.password is not None:
        db_user.passwordHash = pwd_context.hash(user_update.password)
    if user_update.location is not None:
        db_user.location = user_update.location
    if user_update.gender is not None:
        db_user.gender = user_update.gender
    if user_update.age is not None:
        db_user.age = user_update.age
    if user_update.pincode is not None:
        db_user.pincode = str(user_update.pincode)
    if user_update.phone is not None:
        db_user.phone = str(user_update.phone)

    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "svg"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/svg+xml"}
def update_user_profile_image(db: Session, user_id: UUID, file: UploadFile):
    print("[DEBUG] User ID:", user_id)
    print("[DEBUG] File type:", file.content_type)
    print("[DEBUG] Cloudinary API key:", cloudinary.config().api_key)  # See if it's None
    print("[DEBUG] Cloudinary Cloud name:", cloudinary.config().cloud_name)

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = file.file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    file.file.seek(0)

    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        result = cloudinary.uploader.upload(file.file, folder="user_profiles")
        print("[DEBUG] Upload result:", result)
    except Exception as e:
        print("[ERROR] Cloudinary upload failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

    user.profileImage = result["secure_url"]
    db.commit()
    db.refresh(user)

    return {
        "message": "Profile image uploaded successfully",
        "profileImage": user.profileImage
    }

# -------------------------
# ARTWORK OPERATIONS
# -------------------------

def create_artwork(db: Session, artwork: schemas.ArtworkCreate, user_id: UUID):
    db_artwork = models.Artwork(**artwork.dict(), artistId=str(user_id), images=[])
    db.add(db_artwork)
    db.commit()
    db.refresh(db_artwork)
    return db_artwork

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "svg","webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/svg+xml", "image/webp"}
def upload_artwork_image(db: Session, user_id: UUID, file: UploadFile, artwork_id: UUID):
    print("[DEBUG] User ID:", user_id)
    print("[DEBUG] Artwork ID:", artwork_id)
    print("[DEBUG] File type:", file.content_type)
    print("[DEBUG] Cloudinary API key:", cloudinary.config().api_key)
    print("[DEBUG] Cloudinary Cloud name:", cloudinary.config().cloud_name)

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = file.file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    file.file.seek(0)
    
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    artwork = db.query(models.Artwork).filter(
        models.Artwork.id == str(artwork_id),
        models.Artwork.artistId == str(user_id)).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    try:
        result = cloudinary.uploader.upload(file.file, folder="artworks")
        print("[DEBUG] Upload result:", result)
    except Exception as e:
        print("[ERROR] Cloudinary upload failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")
    if not artwork.images:
        artwork.images = []
    artwork.images.append(result["secure_url"])
    db.commit()
    db.refresh(artwork)
    return {
        "message": "Artwork image uploaded successfully",
        "artworkImage": result["secure_url"]
    }

def delete_artwork(db: Session, artwork_id: UUID, user_id: UUID):
    artwork = db.query(models.Artwork).filter(
        models.Artwork.id == str(artwork_id),
        models.Artwork.artistId == str(user_id)).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found or unauthorized")
    db.delete(artwork)
    db.commit()
    return {"message": "Artwork deleted successfully", "artwork_id": artwork_id}

def list_artworks(db: Session):
    return db.query(models.Artwork).all()

def get_artwork(db: Session, artwork_id: UUID):
    return db.query(models.Artwork).filter(models.Artwork.id == str(artwork_id)).first()

# -------------------------
# LIKES OPERATIONS
# -------------------------

def like_artwork(db, user_id, artwork_id):
    user_id = str(user_id)
    artwork_id = str(artwork_id)

    existing_like = db.query(models.ArtworkLike).filter_by(userId=user_id, artworkId=artwork_id).first()
    if existing_like:
        return {"message": "Artwork already liked."}

    new_like = models.ArtworkLike(userId=user_id, artworkId=artwork_id)
    db.add(new_like)
    db.commit()
    return {"message": "Artwork liked successfully."}


def unlike_artwork(db, user_id, artwork_id):
    user_id = str(user_id)
    artwork_id = str(artwork_id)

    like = db.query(models.ArtworkLike).filter_by(userId=user_id, artworkId=artwork_id).first()
    if not like:
        return {"message": "Artwork not liked yet."}

    db.delete(like)
    db.commit()
    return {"message": "Artwork unliked successfully."}


def get_like_count(db, artwork_id):
    artwork_id = str(artwork_id)
    return db.query(models.ArtworkLike).filter_by(artworkId=artwork_id).count()


def has_user_liked_artwork(db, user_id, artwork_id):
    user_id = str(user_id)
    artwork_id = str(artwork_id)
    return db.query(models.ArtworkLike).filter_by(userId=user_id, artworkId=artwork_id).first() is not None

# -------------------------
# COMMENTS OPERATIONS
# -------------------------
def create_comment(db: Session, user_id: UUID, comment_data: models.Comment):
    # Convert UUIDs to strings before querying
    artwork_id = str(comment_data.artwork_id)
    user_id = str(user_id)

    artwork = db.query(models.Artwork).filter_by(id=artwork_id).first()
    if not artwork:
        return {"message": "Artwork not found."}

    new_comment = models.Comment(
        id=str(uuid4()),
        user_id=user_id,
        artwork_id=artwork_id,
        content=comment_data.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {"message": "Comment added successfully.", "comment": new_comment}


def get_comments_for_artwork(db: Session, artwork_id: UUID):
    artwork_id = str(artwork_id)

    comments = (
        db.query(models.Comment)
        .filter(models.Comment.artwork_id == artwork_id)
        .order_by(models.Comment.created_at.desc())
        .all()
    )

    return {
        "message": f"{len(comments)} comment(s) retrieved.",
        "comments": comments
    }

#--------------------------
# ORDER OPERATIONS
# -------------------------

def create_order(db: Session, order_data: schemas.OrderCreate, user_id: UUID):
    db_order = models.Order(
        artworkId=str(order_data.artworkId),
        totalAmount=order_data.totalAmount,
        paymentStatus=order_data.paymentStatus,
        buyerId=str(user_id)
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def list_all_orders(db: Session):
    return db.query(models.Order).all()

def get_order(db: Session, order_id: UUID):
    order_id = str(order_id)
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def list_orders_for_user(db: Session, user_id: UUID):
    user_id = str(user_id)
    return db.query(models.Order).filter(models.Order.buyerId == user_id).all()

# -------------------------
# REVIEW OPERATIONS
# -------------------------

def create_review(db: Session, item: schemas.ReviewCreate, user_id: UUID):
    db_review = models.Review(
        reviewerId=str(user_id),
        artistId=str(item.artistId),
        artworkId=str(item.artworkId),
        rating=item.rating,
        comment=item.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def list_reviews_for_artist(db: Session, artist_id: UUID):
    return db.query(models.Review).filter(models.Review.artistId == str(artist_id)).all()

# -------------------------
# WISHLIST OPERATIONS
# -------------------------

def add_to_wishlist(db: Session, item: schemas.WishlistCreate, user_id: UUID):
    db_wishlist = models.Wishlist(
        userId=str(user_id),
        artworkId=str(item.artworkId)
    )
    db.add(db_wishlist)
    db.commit()
    db.refresh(db_wishlist)
    return db_wishlist

def get_user_wishlist(db: Session, user_id: UUID):
    user_id = str(user_id)
    return db.query(models.Wishlist).filter(models.Wishlist.userId == user_id).all()

def remove_wishlist_item(db: Session, user_id: UUID, artwork_id: UUID):
    item = db.query(models.Wishlist).filter_by(userId=str(user_id), artworkId=str(artwork_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Item removed from wishlist"}

# -------------------------
# CART OPERATIONS
# -------------------------

def add_to_cart(db: Session, item: schemas.CartCreate, user_id: UUID):
    db_cart = models.Cart(
        userId=str(user_id),
        artworkId=str(item.artworkId)
    )
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)
    return db_cart


def get_user_cart(db: Session, user_id: UUID):
    user_id = str(user_id)
    return db.query(models.Cart).filter(models.Cart.userId == user_id).all()

def remove_cart_item(db: Session, user_id: UUID, artwork_id: UUID):
    item = db.query(models.Cart).filter_by(userId=str(user_id), artworkId=str(artwork_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Item removed from cart"}

# -------------------------
# FOLLOW OPERATIONS
# -------------------------

def serialize_user(user: models.User) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "profileImageUrl": user.profileImage,
    }


def follow_user(db: Session, follower_id: str, followed_id: str):
    if follower_id == followed_id:
        raise ValueError("User cannot follow themselves.")

    follower = db.get(models.User, follower_id)
    followed = db.get(models.User, followed_id)

    if not follower or not followed:
        raise ValueError("User not found.")

    if follower.is_following(followed):
        return {"status": "already_following"}

    follower.follow(followed)
    db.commit()
    return {"status": "followed"}


def unfollow_user(db: Session, follower_id: str, followed_id: str):
    follower = db.get(models.User, follower_id)
    followed = db.get(models.User, followed_id)

    if not follower or not followed:
        raise ValueError("User not found.")

    if not follower.is_following(followed):
        return {"status": "not_following"}

    follower.unfollow(followed)
    db.commit()
    return {"status": "unfollowed"}


def get_followers(db: Session, user_id: str):
    user = db.get(models.User, user_id)
    if not user:
        raise ValueError("User not found.")
    return user.followers


def get_following(db: Session, user_id: str):
    user = db.get(models.User, user_id)
    if not user:
        raise ValueError("User not found.")
    return user.following

# -------------------------
# SEARCH OPERATIONS
# -------------------------

def search_artworks(db: Session, query: str):  # ilike is use for searh in MYSQL
    return db.query(models.Artwork).filter(
        or_(
            models.Artwork.title.ilike(f"%{query}%"),
            models.Artwork.category.ilike(f"%{query}%")
            )).all()

def search_users(db: Session, query: str):
    return db.query(models.User).filter(
        or_(
            models.User.username.ilike(f"%{query}%"),
            models.User.name.ilike(f"%{query}%")
        )
    ).all()