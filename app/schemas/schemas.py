from pydantic import BaseModel, EmailStr, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

# ENUM TYPES
RoleType = Literal["user", "admin"]
PaymentStatus = Literal["pending", "paid", "failed"]

# -------------------------------
# USER SCHEMAS
# -------------------------------

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: Optional[RoleType] = "user"
    profileImage: Optional[HttpUrl] = None

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: UUID
    createdAt: datetime

    class Config:
        from_attributes = True

# -------------------------------
# ARTWORK SCHEMAS
# -------------------------------

class ArtworkBase(BaseModel):
    title: str
    description: Optional[str] = None
    image: Optional[HttpUrl] = None
    price: float
    category: str

class ArtworkCreate(ArtworkBase):
    artistId: UUID

class ArtworkRead(ArtworkBase):
    id: UUID
    isSold: bool
    createdAt: datetime
    artistId: UUID

    class Config:
        from_attributes = True

# -------------------------------
# ORDER SCHEMAS
# -------------------------------

class OrderBase(BaseModel):
    artworkId: UUID
    totalAmount: float
    paymentStatus: PaymentStatus

class OrderCreate(OrderBase):
    buyerId: UUID

class OrderRead(OrderBase):
    id: UUID
    buyerId: UUID
    createdAt: datetime

    class Config:
        from_attributes = True

# -------------------------------
# REVIEW SCHEMAS
# -------------------------------

class ReviewBase(BaseModel):
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    reviewerId: UUID
    artistId: Optional[UUID] = None
    artworkId: Optional[UUID] = None

class ReviewRead(ReviewBase):
    id: UUID
    reviewerId: UUID
    artistId: Optional[UUID]
    artworkId: Optional[UUID]
    createdAt: datetime

    class Config:
        from_attributes = True

# -------------------------------
# WISHLIST SCHEMAS
# -------------------------------

class WishlistCreate(BaseModel):
    userId: UUID
    artworkId: UUID

class WishlistRead(WishlistCreate):
    id: UUID
    createdAt: datetime

    class Config:
        from_attributes = True

# -------------------------------
# CART SCHEMAS
# -------------------------------

class CartCreate(BaseModel):
    userId: UUID
    artworkId: UUID

class CartRead(CartCreate):
    id: UUID
    createdAt: datetime

    class Config:
        from_attributes = True
