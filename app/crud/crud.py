from sqlalchemy.orm import Session
from uuid import UUID
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
    db_artwork = models.Artwork(**data)
    db.add(db_artwork)
    db.commit()
    db.refresh(db_artwork)
    return db_artwork

def get_artwork(db: Session, artwork_id: UUID):
    return db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

def list_artworks(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.Artwork).offset(skip).limit(limit).all()

# -------------------------
# LIKES OPERATIONS
# -------------------------

def like_artwork(db, user_id, artwork_id):
    existing_like = db.query(models.ArtworkLike).filter_by(user_id=user_id, artwork_id=artwork_id).first()
    if existing_like:
        return {"message": "Artwork already liked."}

    new_like = models.ArtworkLike(user_id=user_id, artwork_id=artwork_id)
    db.add(new_like)
    db.commit()
    return {"message": "Artwork liked successfully."}

def unlike_artwork(db, user_id, artwork_id):
    like = db.query(models.ArtworkLike).filter_by(user_id=user_id, artwork_id=artwork_id).first()
    if not like:
        return {"message": "Artwork not liked yet."}

    db.delete(like)
    db.commit()
    return {"message": "Artwork unliked successfully."}

def get_like_count(db, artwork_id):
    return db.query(models.ArtworkLike).filter_by(artwork_id=artwork_id).count()

def has_user_liked_artwork(db, user_id, artwork_id): # check if user likes artwork
    return db.query(models.ArtworkLike).filter_by(user_id=user_id, artwork_id=artwork_id).first() is not None

# -------------------------
# COMMENTS OPERATIONS
# -------------------------
def create_comment(db: Session, user_id: UUID, comment_data: models.Comment):
    # Check if the artwork exists
    artwork = db.query(models.Artwork).filter_by(id=comment_data.artwork_id).first()
    if not artwork:
        return {"message": "Artwork not found."}

    # Create the comment
    new_comment = models.Comment(
        id=UUID.uuid4(),  # ✅ use the standard uuid module
        user_id=user_id,
        artwork_id=comment_data.artwork_id,
        content=comment_data.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {"message": "Comment added successfully.", "comment": new_comment}


def get_comments_for_artwork(db: Session, artwork_id: UUID):
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
    db_order = models.Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_order(db: Session, order_id: UUID):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def list_orders_for_user(db: Session, user_id: UUID):
    return db.query(models.Order).filter(models.Order.buyerId == user_id).all()

# -------------------------
# REVIEW OPERATIONS
# -------------------------

def create_review(db: Session, review: schemas.ReviewCreate):
    db_review = models.Review(**review.dict())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def list_reviews_for_artist(db: Session, artist_id: UUID):
    return db.query(models.Review).filter(models.Review.artistId == artist_id).all()

# -------------------------
# WISHLIST OPERATIONS
# -------------------------

def add_to_wishlist(db: Session, item: schemas.WishlistCreate):
    db_item = models.Wishlist(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_user_wishlist(db: Session, user_id: UUID):
    return db.query(models.Wishlist).filter(models.Wishlist.userId == user_id).all()

# -------------------------
# CART OPERATIONS
# -------------------------

def add_to_cart(db: Session, item: schemas.CartCreate):
    db_item = models.Cart(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_user_cart(db: Session, user_id: UUID):
    return db.query(models.Cart).filter(models.Cart.userId == user_id).all()
