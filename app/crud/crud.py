from sqlalchemy.orm import Session
from uuid import UUID
from app import models
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
        passwordHash=hashed_password,
        role=user.role or "user",
        profileImage=user.profileImage,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# -------------------------
# ARTWORK OPERATIONS
# -------------------------

def create_artwork(db: Session, artwork: schemas.ArtworkCreate):
    db_artwork = models.Artwork(**artwork.dict())
    db.add(db_artwork)
    db.commit()
    db.refresh(db_artwork)
    return db_artwork

def get_artwork(db: Session, artwork_id: UUID):
    return db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

def list_artworks(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.Artwork).offset(skip).limit(limit).all()

# -------------------------
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
