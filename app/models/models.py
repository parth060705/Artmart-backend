from sqlalchemy import Column, String, Float, Text, Enum, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from sqlalchemy import Enum as SqlEnum
from app.database import Base


# ENUM DEFINITIONS
class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"

class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


# USER MODEL
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    passwordHash = Column(String, nullable=False)
    role = Column(SqlEnum(RoleEnum, native_enum=False), nullable=False, default=RoleEnum.user)
    profileImage = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    location = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)

    # Relationships
    artworks = relationship("Artwork", back_populates="artist")
    orders = relationship("Order", back_populates="buyer")
    reviews = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewerId")
    wishlist_items = relationship("Wishlist", back_populates="user")
    cart_items = relationship("Cart", back_populates="user")
    liked_artworks = relationship("ArtworkLike", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")


# ARTWORK MODEL
class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    image = Column(String)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    artistId = Column(String, ForeignKey("users.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)
    isSold = Column(Boolean, default=False)

    # Relationships
    artist = relationship("User", back_populates="artworks")
    orders = relationship("Order", back_populates="artwork")
    reviews = relationship("Review", back_populates="artwork")
    wishlist_items = relationship("Wishlist", back_populates="artwork")
    cart_items = relationship("Cart", back_populates="artwork")
    likes = relationship("ArtworkLike", back_populates="artwork", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="artwork", cascade="all, delete-orphan")


# ARTWORK LIKES
class ArtworkLike(Base):
    __tablename__ = "artwork_likes"

    userId = Column(String, ForeignKey("users.id"), primary_key=True)
    artworkId = Column(String, ForeignKey("artworks.id"), primary_key=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    artwork = relationship("Artwork", back_populates="likes")
    user = relationship("User", back_populates="liked_artworks")


# COMMENT MODEL
class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    artwork_id = Column(String, ForeignKey("artworks.id"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="comments")
    artwork = relationship("Artwork", back_populates="comments")


# ORDER MODEL
class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    buyerId = Column(String, ForeignKey("users.id"))
    artworkId = Column(String, ForeignKey("artworks.id"))
    totalAmount = Column(Float, nullable=False)
    paymentStatus = Column(SqlEnum(PaymentStatusEnum, native_enum=False), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    buyer = relationship("User", back_populates="orders")
    artwork = relationship("Artwork", back_populates="orders")


# REVIEW MODEL
class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reviewerId = Column(String, ForeignKey("users.id"))
    artistId = Column(String, ForeignKey("users.id"))
    artworkId = Column(String, ForeignKey("artworks.id"), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    createdAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reviewer = relationship("User", back_populates="reviews", foreign_keys=[reviewerId])
    artwork = relationship("Artwork", back_populates="reviews")
    artist = relationship("User", foreign_keys=[artistId])


# WISHLIST MODEL
class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column(String, ForeignKey("users.id"))
    artworkId = Column(String, ForeignKey("artworks.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="wishlist_items")
    artwork = relationship("Artwork", back_populates="wishlist_items")


# CART MODEL
class Cart(Base):
    __tablename__ = "cart"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column(String, ForeignKey("users.id"))
    artworkId = Column(String, ForeignKey("artworks.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cart_items")
    artwork = relationship("Artwork", back_populates="cart_items")
