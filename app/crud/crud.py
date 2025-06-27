from sqlalchemy.orm import Session
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


# -------------------------
# ARTWORK OPERATIONS
# -------------------------

def create_artwork(db: Session, artwork: schemas.ArtworkCreate):
    data = artwork.dict()
    if data.get("image"):
        data["image"] = str(data["image"])  # Convert HttpUrl to string
    data["artistId"] = str(data["artistId"])  # Convert UUID to string
    db_artwork = models.Artwork(**data)
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


# ORDER OPERATIONS
# -------------------------

def create_order(db: Session, order: schemas.OrderCreate):
    data = order.dict()
    data["buyerId"] = str(data["buyerId"])
    data["artworkId"] = str(data["artworkId"])
    db_order = models.Order(**data)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def list_all_orders(db: Session):
    return db.query(models.Order).all()

# def get_order(db: Session, order_id: UUID):
#     order_id = str(order_id)
#     return db.query(models.Order).filter(models.Order.id == order_id).first()


def list_orders_for_user(db: Session, user_id: UUID):
    user_id = str(user_id)
    return db.query(models.Order).filter(models.Order.buyerId == user_id).all()

# -------------------------
# REVIEW OPERATIONS
# -------------------------

def create_review(db: Session, review: schemas.ReviewCreate):
    data = review.dict()
    data["reviewerId"] = str(data["reviewerId"])
    if data.get("artistId"):
        data["artistId"] = str(data["artistId"])
    if data.get("artworkId"):
        data["artworkId"] = str(data["artworkId"])
    db_review = models.Review(**data)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def list_reviews_for_artist(db: Session, artist_id: UUID):
    artist_id = str(artist_id)  # Convert UUID to string
    return db.query(models.Review).filter(models.Review.artistId == artist_id).all()

# -------------------------
# WISHLIST OPERATIONS
# -------------------------

def add_to_wishlist(db: Session, item: schemas.WishlistCreate):
    data = item.dict()
    data["userId"] = str(data["userId"])
    data["artworkId"] = str(data["artworkId"])
    db_item = models.Wishlist(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_user_wishlist(db: Session, user_id: UUID):
    user_id = str(user_id)
    return db.query(models.Wishlist).filter(models.Wishlist.userId == user_id).all()

# -------------------------
# CART OPERATIONS
# -------------------------

def add_to_cart(db: Session, item: schemas.CartCreate):
    data = item.dict()
    data["userId"] = str(data["userId"])
    data["artworkId"] = str(data["artworkId"])
    db_item = models.Cart(**data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_user_cart(db: Session, user_id: UUID):
    user_id = str(user_id)
    return db.query(models.Cart).filter(models.Cart.userId == user_id).all()
