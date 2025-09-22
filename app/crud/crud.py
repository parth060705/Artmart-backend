from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text
from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID
from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import schemas
from passlib.context import CryptContext
import cloudinary.uploader
import cloudinary
from typing import List, Optional, Dict
from fastapi import UploadFile, HTTPException
import cloudinary.uploader
import random, string
import re
from sqlalchemy.exc import SQLAlchemyError


# FOR MESSAGING
# from app.models.models import Message
# from app.schemas.schemas import MessageCreate
# from datetime import datetime


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# USER OPERATIONS
# -------------------------

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: UUID):
    return db.query(models.User).filter(models.User.id == str(user_id)).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

#---------------------------------------HELPER CLASS FOR USER REGISTER------------------------------------------------------

# HELPER CLASS FOR validation for strong password
def validate_password_strength(password: str):
    password = password.strip()  # remove leading/trailing spaces/newlines

    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must be at least 8 characters long"}
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must contain an uppercase letter"}
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must contain a lowercase letter"}
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must contain a number"}
        )
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must contain a special character"}
        )

# HELPER CLASS FOR for suggesting unique username
def suggest_usernames(db: Session, base_username: str, max_suggestions: int = 5):
    base = base_username.lower().replace(" ", "").replace(".", "").replace("_", "")
    suggestions = []

    while len(suggestions) < max_suggestions:
        suffix = ''.join(random.choices(string.digits, k=3))
        candidate = f"{base}{suffix}"
        if not db.query(models.User).filter_by(username=candidate).first():
            suggestions.append(candidate)
    return suggestions

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)

    db_user = models.User(
        name=user.name,
        email=user.email,
        username=user.username,
        passwordHash=hashed_password,
        role=models.RoleEnum.user,
        profileImage=str(user.profileImage) if user.profileImage else None,
        location=user.location,
        gender=user.gender,
        bio=user.bio,
        age=user.age,
        phone=str(user.phone) if user.phone else None,
        pincode=str(user.pincode) if user.pincode else None,
        isAgreedtoTC=user.isAgreedtoTC
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/svg+xml"}
def upload_image_to_cloudinary(file: UploadFile):
    print("[DEBUG] File type:", file.content_type)
    print("[DEBUG] Cloudinary API key:", cloudinary.config().api_key)
    print("[DEBUG] Cloudinary Cloud name:", cloudinary.config().cloud_name)

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Validate file size (max 5MB)
    contents = file.file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    file.file.seek(0)

    # Upload to Cloudinary
    try:
        result = cloudinary.uploader.upload(file.file, folder="user_profiles")
        print("[DEBUG] Upload result:", result)
    except Exception as e:
        print("[ERROR] Cloudinary upload failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

    return {
        "message": "Image uploaded successfully",
        "url": result["secure_url"]
    }

def update_user_details(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")
    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.location is not None:
        db_user.location = user_update.location
    if user_update.gender is not None:
        db_user.gender = user_update.gender
    if user_update.age is not None:
        db_user.age = user_update.age
    if user_update.bio is not None:
        db_user.bio = user_update.bio    
    if user_update.pincode is not None:
        db_user.pincode = str(user_update.pincode)
    if user_update.phone is not None:
        db_user.phone = str(user_update.phone)
    db.commit()
    db.refresh(db_user)
    return db_user

#----------------------------------------------------------------------------------

#################### FOR REPLACING PROFILE PHOTOS FROM CLOUDINARY AFTER UPDATING
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "svg"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/svg+xml"}

def update_user_profile_image(db: Session, user_id: UUID, file: UploadFile):
    print("[DEBUG] User ID:", user_id)
    print("[DEBUG] File type:", file.content_type)
    print("[DEBUG] Cloudinary API key:", cloudinary.config().api_key)  
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

    # Delete previous image if present
    if user.profileImagePublicId:
        try:
            deletion_result = cloudinary.uploader.destroy(user.profileImagePublicId)
            print("[DEBUG] Deleted old image:", deletion_result)
        except Exception as e:
            print("[ERROR] Could not delete old image:", str(e))

    # Upload new image
    try:
        result = cloudinary.uploader.upload(file.file, folder="user_profiles")
        print("[DEBUG] Upload result:", result)
    except Exception as e:
        print("[ERROR] Cloudinary upload failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

    # Save new image URL and public_id
    user.profileImage = result["secure_url"]
    user.profileImagePublicId = result["public_id"]
    db.commit()
    db.refresh(user)

    return {
        "message": "Profile image uploaded successfully",
        "profileImage": user.profileImage
    }


# -------------------------
# ARTWORK OPERATIONS
# -------------------------
                                              # CREATE ARTWORK #
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "svg"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/pjpeg",     
    "image/png",
    "image/svg+xml"
}
MAX_FILE_SIZE_MB = 20

def create_artwork(
    db: Session,
    artwork_data: schemas.ArtworkCreate,
    user_id: UUID,
    files: List[UploadFile],
):
    # 1️⃣ Check user exists
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2️⃣ Enforce forSale logic
    if artwork_data.forSale:   # <-- changed from isSale to forSale
        if artwork_data.price is None:
            raise HTTPException(status_code=400, detail="Price is required for sale artwork")
        if artwork_data.quantity is None:
            raise HTTPException(status_code=400, detail="Quantity is required for sale artwork")
    else:
        # If not for sale, nullify price/quantity to avoid accidental DB insert
        artwork_data.price = None
        artwork_data.quantity = None

    try:
        # 3️⃣ Create artwork record
        db_artwork = models.Artwork(
            **artwork_data.dict(exclude={"images"}),  # exclude images from schema
            artistId=str(user_id),
        )
        db.add(db_artwork)
        db.flush()  # flush to get artwork ID before images

        # 4️⃣ Upload images to Cloudinary
        for file in files:
            if file.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=400, detail=f"Unsupported file type: {file.content_type}"
                )

            contents = file.file.read()
            if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=400, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)"
                )
            file.file.seek(0)

            result = cloudinary.uploader.upload(file.file, folder="artworks")
            secure_url = result.get("secure_url")
            public_id = result.get("public_id")
            if not secure_url or not public_id:
                raise HTTPException(status_code=500, detail="Cloudinary upload failed")

            # 5️⃣ Create ArtworkImage record
            db_image = models.ArtworkImage(
                artwork_id=db_artwork.id,
                url=secure_url,
                public_id=public_id,
            )
            db.add(db_image)

        db.commit()
        db.refresh(db_artwork)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return {
        "message": "Artwork created successfully",
        "artwork": db_artwork,
    }



#------------------------------------------------------------------------------------------------------
                                            # UPDATE ARTWORK #
def update_artwork(
    db: Session,
    artwork_id: str,
    user_id: str,
    artwork_update: schemas.ArtworkUpdate,
     files: Optional[List[UploadFile]] = None  
):
    db_artwork = db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

    if not db_artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    if db_artwork.artistId != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this artwork")

    # Update provided fields
    update_data = artwork_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_artwork, key, value)

    # Upload additional images if provided
    if files:
        new_image_urls = []

        for f in files:
            if f.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {f.content_type}")

            contents = f.file.read()
            if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)")
            f.file.seek(0)

            try:
                result = cloudinary.uploader.upload(f.file, folder="artworks")
                secure_url = result.get("secure_url")
                if secure_url:
                    new_image_urls.append(secure_url)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

        # Append new images to existing ones
        db_artwork.images = (db_artwork.images or []) + new_image_urls

    db.commit()
    db.refresh(db_artwork)
    return db_artwork

# --------------------
# ADD IMAGE
# --------------------
def add_artwork_images(db, artwork_id: str, user_id: str, files: list):
    artwork = (
        db.query(models.Artwork)
        .filter_by(id=artwork_id, artistId=user_id)
        .first()
    )
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    new_images = []
    for file in files:
        upload_result = cloudinary.uploader.upload(file.file, folder="artworks")

        # create SQLAlchemy model, not dict
        db_image = models.ArtworkImage(
            artwork_id=artwork.id,
            url=upload_result["secure_url"],
            public_id=upload_result["public_id"],
        )
        db.add(db_image)
        new_images.append(db_image)

    artwork.images.extend(new_images)

    db.commit()
    db.refresh(artwork)
    return artwork

# --------------------
# REPLACE IMAGE
# --------------------
def update_artwork_image(db, artwork_id: str, user_id: str, old_public_id: str, file):
    artwork = (
        db.query(models.Artwork)
        .filter_by(id=artwork_id, artistId=user_id)
        .first()
    )
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    # checking image in db
    db_image = (
        db.query(models.ArtworkImage)
        .filter_by(artwork_id=artwork.id, public_id=old_public_id)
        .first()
    )
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # destroy image from db
    cloudinary.uploader.destroy(old_public_id)
    
    # update the image
    upload_result = cloudinary.uploader.upload(file.file, folder="artworks")
    db_image.url = upload_result["secure_url"]
    db_image.public_id = upload_result["public_id"]

    db.commit()
    db.refresh(artwork)
    return artwork

# --------------------
# DELETE IMAGE
# --------------------
def delete_artwork_image(db, artwork_id: str, user_id: str, public_id: str):
    artwork = (
        db.query(models.Artwork)
        .filter_by(id=artwork_id, artistId=user_id)
        .first()
    )
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    # Find the image record
    db_image = (
        db.query(models.ArtworkImage)
        .filter_by(artwork_id=artwork.id, public_id=public_id)
        .first()
    )
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete from Cloudinary
    cloudinary.uploader.destroy(public_id)

    # Remove from DB
    db.delete(db_image)
    db.commit()
    db.refresh(artwork)

    return artwork
#------------------------------------------------------------------------------------------------------------

                                          # DELETE ARTWORK
def delete_artwork(db: Session, artwork_id: UUID, user_id: UUID):
    artwork = db.query(models.Artwork).filter(
        models.Artwork.id == str(artwork_id),
        models.Artwork.artistId == str(user_id)).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found or unauthorized")
    db.delete(artwork)
    db.commit()
    return {"message": "Artwork deleted successfully", "artwork_id": artwork_id}

                                        # GET ARTWORK                                  
def list_artworks(db: Session) -> List[models.Artwork]:
    artworks = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.artist), joinedload(models.Artwork.likes))
        .order_by(func.random())  # PostgreSQL; use func.rand() for MySQL
        .all()
    )
    return artworks

                                           # GET SPECIFIC ARTWORK
def get_artwork(db: Session, artwork_id: UUID):
    return (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.artist), joinedload(models.Artwork.likes))
        .filter(models.Artwork.id == str(artwork_id))
        .first()
    )

                                          # GET MY ARTWORK
def get_artworks_by_user(db: Session, user_id: str):
    return db.query(models.Artwork).filter(models.Artwork.artistId == user_id).all()

                                          # GET USER ARTWORK
def get_artworks_by_user(db: Session, user_id: str):
    artworks = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.likes))
        .filter(models.Artwork.artistId == str(user_id))
        .all()
    )

    for artwork in artworks:
        artwork.how_many_like = {"like_count": len(artwork.likes)}  

    return artworks

#--------------------------
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

def get_comments_by_artwork(db: Session, artwork_id: str):
    return (
        db.query(models.Comment)
        .options(joinedload(models.Comment.user))
        .filter(models.Comment.artwork_id == artwork_id)
        .all()
    )

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
        artistId=str(item.artistId) if item.artistId else None,
        artworkId=str(item.artworkId),
        rating=item.rating,
        comment=item.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def list_reviews_for_artwork(db: Session, artwork_id: UUID):
    return (
        db.query(models.Review)
        .options(joinedload(models.Review.reviewer))
        .filter(models.Review.artworkId == str(artwork_id))
        .all()
    )

# -------------------------
# Saved OPERATIONS
# -------------------------

def add_to_Saved(db: Session, item: schemas.SavedCreate, user_id: UUID):
    db_Saved = models.Saved(
        userId=str(user_id),
        artworkId=str(item.artworkId)
    )
    db.add(db_Saved)
    db.commit()
    db.refresh(db_Saved)
    return db_Saved

def get_user_Saved(db: Session, user_id: UUID):
    return (
        db.query(models.Saved)
        .options(joinedload(models.Saved.artwork))
        .filter(models.Saved.userId == str(user_id))
        .filter(models.Saved.artworkId.isnot(None))  # exclude Saved rows with no artwork
        .all()
    )

def remove_Saved_item(db: Session, user_id: UUID, artwork_id: UUID):
    item = db.query(models.Saved).filter_by(userId=str(user_id), artworkId=str(artwork_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Saved item not found")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Item removed from Saved"}

# -------------------------
# CART OPERATIONS
# -------------------------

def add_to_cart(db: Session, cart_data: schemas.CartCreate):
    artwork = db.query(models.Artwork).filter(models.Artwork.id == str(cart_data.artworkId)).first()
    if not artwork:
        raise ValueError("Artwork not found")

    if cart_data.purchase_quantity is None:
        cart_data.purchase_quantity = 1

    # Check stock availability
    if artwork.quantity < cart_data.purchase_quantity:
        raise ValueError("Not enough stock available")

    # Check if item already exists in cart
    existing_cart_item = db.query(models.Cart).filter(
        models.Cart.userId == str(cart_data.userId),
        models.Cart.artworkId == str(cart_data.artworkId)
    ).first()

    if existing_cart_item:
        # Update quantity
        new_quantity = existing_cart_item.purchase_quantity + cart_data.purchase_quantity
        if new_quantity > artwork.quantity:
            raise ValueError("Not enough stock available")
        existing_cart_item.purchase_quantity = new_quantity
        db.commit()
        db.refresh(existing_cart_item)
        return existing_cart_item
    else:
        cart_item = models.Cart(
            userId=str(cart_data.userId),
            artworkId=str(cart_data.artworkId),
            purchase_quantity=cart_data.purchase_quantity
        )
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)
        return cart_item

#--------------------------------------------------------

def get_user_cart(db: Session, user_id: UUID):
    user_id = str(user_id)
    return (
        db.query(models.Cart)
        .options(
            joinedload(models.Cart.artwork).joinedload(models.Artwork.images)
        )
        .filter(models.Cart.userId == user_id)
        .all()
    )

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

def serialize_user(user: models.User):
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "profileImage": user.profileImage,
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

def is_user_following(db: Session, follower_id: str, following_id: str) -> bool:
    follower = db.query(models.User).filter(models.User.id == follower_id).first()
    following = db.query(models.User).filter(models.User.id == following_id).first()

    if not follower or not following:
        return False

    return following in follower.following

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

def get_artworks_by_category(db: Session, category: str):
    return db.query(models.Artwork).filter(
        models.Artwork.category.ilike(f"%{category.strip()}%")
    ).all()

                # SEARCH ARTWORK BY SPECIFICATION OF TITLE, PRICE, CATEGORY, ARTIST NAME, LOCATION
def get_artworks_with_artist_filters(
    db: Session,
    artwork_id: Optional[str] = None,
    title: Optional[str] = None,
    price: Optional[float] = None,
    category: Optional[str] = None,
    artist_name: Optional[str] = None,
    location: Optional[str] = None,
    tags: Optional[str] = None,                                     #
    user_id: Optional[str] = None,
):
    query = db.query(models.Artwork).join(models.Artwork.artist)
    filters = []
    if artwork_id:
        filters.append(models.Artwork.id == artwork_id)
    if title:
        filters.append(models.Artwork.title.ilike(f"%{title}%"))
    if price:
        filters.append(models.Artwork.price == price)
    if category:
        filters.append(models.Artwork.category.ilike(f"%{category}%"))
    if artist_name:
        filters.append(models.User.name.ilike(f"%{artist_name}%"))
    if location:
        filters.append(models.User.location.ilike(f"%{location}%"))
    if tags:                                                                   #
        filters.append(models.Artwork.tags.ilike(f"%{tags}%"))    
    if user_id:
        filters.append(models.User.id == user_id)

    if filters:
        query = query.filter(and_(*filters))
    return query.options(joinedload(models.Artwork.artist)).all()

# -------------------------
# HOME FEED OPERATIONS
# -------------------------

def get_home_feed(db: Session, current_user, limit: int = 20):
    following_ids = [u.id for u in current_user.following]

    # 1️⃣ Artworks from following
    feed_artworks = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.artist), 
                 joinedload(models.Artwork.likes),
                 joinedload(models.Artwork.images))
        .filter(models.Artwork.artistId.in_(following_ids))
        .order_by(func.random())
        .limit(limit)
        .all()
    )

    # 2️⃣ Preferred tags from liked artworks
    liked_tags = (
        db.query(models.Artwork.tags)
        .join(models.ArtworkLike, models.ArtworkLike.artworkId == models.Artwork.id)
        .filter(models.ArtworkLike.userId == current_user.id)
        .all()
    )

    preferred_tags = set()
    for tags_tuple in liked_tags:
        if isinstance(tags_tuple[0], list):
            preferred_tags.update(tags_tuple[0])
        elif isinstance(tags_tuple[0], str):
            preferred_tags.update([t.strip() for t in tags_tuple[0].split(",") if t.strip()])

    # 3️⃣ Recommended artworks (not from self or following)
    recommended_query = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.artist), 
                 joinedload(models.Artwork.likes),
                 joinedload(models.Artwork.images))
        .filter(
            models.Artwork.artistId != current_user.id,
            ~models.Artwork.artistId.in_(following_ids)
        )
        .order_by(func.random())
    )

    if preferred_tags:
        tag_conditions = [
            func.json_contains(models.Artwork.tags, f'"{tag}"') for tag in preferred_tags
        ]
        recommended_query = recommended_query.filter(or_(*tag_conditions))

    recommended_artworks = recommended_query.limit(limit).all()

    # 4️⃣ Combine and slice to final limit if needed
    combined_feed = feed_artworks + recommended_artworks
    combined_feed = combined_feed[:limit]

    return combined_feed

# -------------------------
#  RECOMMENDATION ENDPOINTS
# -------------------------

def get_recommendation(db: Session, artwork_id: UUID, limit: int = 10) -> List[schemas.ArtworkRead]:
    target_artwork = db.query(models.Artwork)\
    .options(joinedload(models.Artwork.artist),
             joinedload(models.Artwork.likes),
             joinedload(models.Artwork.images))\
    .filter(models.Artwork.id == artwork_id, models.Artwork.isDeleted == False)\
    .first()


    if not target_artwork:
        print("❌ No target artwork found")
        return []

    filters = []

    # Title filter
    if target_artwork.title:
        words = [w.strip() for w in target_artwork.title.split() if w.strip()]
        if words:
            filters.append(or_(*[models.Artwork.title.ilike(f"%{w}%") for w in words]))

    # Category filter
    if target_artwork.category:
        filters.append(models.Artwork.category.ilike(target_artwork.category))

    # Tags filter
    preferred_tags = set()
    if target_artwork.tags:
        if isinstance(target_artwork.tags, list):
            for entry in target_artwork.tags:
                preferred_tags.update([t.strip() for t in entry.split(",") if t.strip()])
        elif isinstance(target_artwork.tags, str):
            preferred_tags.update([t.strip() for t in target_artwork.tags.split(",") if t.strip()])

    if preferred_tags:
        tag_filters = [models.Artwork.tags.ilike(f"%{tag}%") for tag in preferred_tags]
        filters.append(or_(*tag_filters))

    # Query other artworks excluding the target
    query = db.query(models.Artwork).filter(models.Artwork.id != artwork_id)
    if filters:
        query = query.filter(or_(*filters))

    results = query.order_by(func.random()).limit(limit).all()

    # Convert to Pydantic schemas
    return [schemas.ArtworkRead.model_validate(art) for art in results]



# ------------------------------------------------------------------------------------------------------------------
#                                        ADMIN & SUPER-ADMIN ENDPOINTS
# -------------------------------------------------------------------------------------------------------------------

                                                 # USERS
def list_all_users(db: Session):
    return db.query(models.User).all()

def delete_user(db: Session, user_id):  # no UUID typing
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

def update_user_details_admin(db: Session, user_id: str, update_data: dict):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

def get_users_filters(
    db: Session,
    user_id: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    gender: Optional[str] = None,
    role: Optional[str] = None,
    location: Optional[str] = None,
):
    query = db.query(models.User)
    filters = []
    if user_id:
        filters.append(models.User.id == user_id)
    if name:
        filters.append(models.User.name.ilike(f"%{name}%"))
    if email:
        filters.append(models.User.email == email)
    if username:
        filters.append(models.User.username == username)
    if gender:
        filters.append(models.User.gender.ilike(f"%{gender}%"))
    if role:
        filters.append(models.User.role.ilike(f"%{role}%"))
    if location:
        filters.append(models.User.location.ilike(f"%{location}%"))

    if filters:
        query = query.filter(and_(*filters))
    return query.all()

                                               # ARTWORKS
def list_artworks_admin(db: Session):
    return db.query(models.Artwork).all()

def update_artwork(
    db: Session,
    artwork_id: str,
    artwork_update: schemas.ArtworkUpdate,
    files: Optional[List[UploadFile]] = None
):
    db_artwork = db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

    if not db_artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    update_data = artwork_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_artwork, key, value)

    if files:
        new_image_urls = []

        for f in files:
            if f.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {f.content_type}")

            contents = f.file.read()
            if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)")
            f.file.seek(0)

            try:
                result = cloudinary.uploader.upload(f.file, folder="artworks")
                secure_url = result.get("secure_url")
                if secure_url:
                    new_image_urls.append(secure_url)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

        db_artwork.images = (db_artwork.images or []) + new_image_urls

    db.commit()
    db.refresh(db_artwork)
    return db_artwork

def delete_artwork_admin(db: Session, artwork_id: str):
    # ✅ Load artwork with its related images in one query
    artwork = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.images))  # eager load images
        .filter(models.Artwork.id == artwork_id)
        .first()
    )

    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    # ✅ Delete all images from Cloudinary
    for img in artwork.images:   # ArtworkImage objects
        try:
            cloudinary.uploader.destroy(img.public_id)
        except Exception as e:
            print(f"⚠️ Cloudinary cleanup failed for {img.public_id}: {e}")

    db.delete(artwork)
    db.commit()

    return {
        "message": "Artwork deleted successfully",
        "artwork_id": artwork_id
    }
                                              # ORDERS
def list_all_orders(db: Session):
    return db.query(models.Order)\
        .options(
            joinedload(models.Order.buyer),
            joinedload(models.Order.artwork)
        )\
        .all()

def delete_order(db: Session, order_id: UUID):
    order = db.query(models.Order).filter(models.Order.id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {
        "message": "Order deleted successfully",
        "order_id": order_id }

                                              # FOLLOW & FOLLOWERS
def list_follow_followers(db: Session):
    return (
        db.query(
            models.User.username,
            models.User.profileImage,
            models.followers_association.c.follower_id,
            models.followers_association.c.followed_id,
            models.followers_association.c.created_at
        )
        .join(models.User, models.User.id == models.followers_association.c.follower_id)
        .all()
    )
