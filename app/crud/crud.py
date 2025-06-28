from sqlalchemy.orm import Session
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
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "svg"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/svg+xml"}

def update_user_profile_image(db: Session, user_id: UUID, file: UploadFile):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    # ✅ FIXED query
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    user.profileImage = file_path
    db.commit()
    db.refresh(user)

    return {"message": "Profile image uploaded", "profileImage": user.profileImage}


# -------------------------
# ARTWORK OPERATIONS
# -------------------------

def create_artwork(db: Session, item: schemas.ArtworkCreate, user_id: UUID):
    db_artwork = models.Artwork(
        title=item.title,
        description=item.description,
        image=str(item.image) if item.image else None,
        price=item.price,
        category=item.category,
        artistId=str(user_id)
    )
    db.add(db_artwork)
    db.commit()
    db.refresh(db_artwork)
    return db_artwork

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
        id=str(uuid4()),  # Generate a new UUID and store as string
        user_id=user_id,
        artwork_id=artwork_id,
        content=comment_data.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {"message": "Comment added successfully.", "comment": new_comment}


def get_comments_for_artwork(db: Session, artwork_id: UUID):
    artwork_id = str(artwork_id)  # Convert UUID to string

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
