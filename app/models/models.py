from sqlalchemy import Column, String, Float, Text, Enum, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    passwordHash = Column(String, nullable=False)
    role = Column(SqlEnum(RoleEnum, native_enum=False), nullable=False, default=RoleEnum.user)
    profileImage = Column(String, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)

    artworks = relationship("Artwork", back_populates="artist")
    orders = relationship("Order", back_populates="buyer")
    reviews = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewerId")
    wishlist_items = relationship("Wishlist", back_populates="user")
    cart_items = relationship("Cart", back_populates="user")


# ARTWORK MODEL
class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    image = Column(String)
    price = Column(Float, nullable=False)
    category = Column(String)
    artistId = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)
    isSold = Column(Boolean, default=False)

    artist = relationship("User", back_populates="artworks")
    orders = relationship("Order", back_populates="artwork")
    reviews = relationship("Review", back_populates="artwork")
    wishlist_items = relationship("Wishlist", back_populates="artwork")
    cart_items = relationship("Cart", back_populates="artwork")


# ORDER MODEL
class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyerId = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    artworkId = Column(UUID(as_uuid=True), ForeignKey("artworks.id"))
    totalAmount = Column(Float, nullable=False)
    paymentStatus = Column(Enum(PaymentStatusEnum), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    buyer = relationship("User", back_populates="orders")
    artwork = relationship("Artwork", back_populates="orders")


# REVIEW MODEL
class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reviewerId = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    artistId = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    artworkId = Column(UUID(as_uuid=True), ForeignKey("artworks.id"), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    createdAt = Column(DateTime, default=datetime.utcnow)

    reviewer = relationship("User", back_populates="reviews", foreign_keys=[reviewerId])
    artwork = relationship("Artwork", back_populates="reviews")
    artist = relationship("User", foreign_keys=[artistId])


# WISHLIST MODEL
class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    artworkId = Column(UUID(as_uuid=True), ForeignKey("artworks.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wishlist_items")
    artwork = relationship("Artwork", back_populates="wishlist_items")


# CART MODEL
class Cart(Base):
    __tablename__ = "cart"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    userId = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    artworkId = Column(UUID(as_uuid=True), ForeignKey("artworks.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cart_items")
    artwork = relationship("Artwork", back_populates="cart_items")
