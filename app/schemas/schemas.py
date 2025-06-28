from pydantic import BaseModel, EmailStr, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

# ENUM TYPES
RoleType = Literal["user", "admin"]
PaymentStatus = Literal["pending", "paid", "failed"]

# -------------------------------
# TOKENS
# -------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# -------------------------------
# USER SCHEMAS
# -------------------------------

class UserBase(BaseModel):
    name: str
    email: EmailStr
    username: str
    profileImage: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None

class UserCreate(UserBase):
    password: str

# Schema for reading user info (e.g. /me or user list)
class UserRead(UserBase):
    id: UUID
    createdAt: datetime

    class Config:
        from_attributes = True  

class ProfileImageResponse(BaseModel):
    message: str
    profileImage: str

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
    pass

class ArtworkRead(ArtworkBase):
    id: UUID
    isSold: bool
    createdAt: datetime
    artistId: UUID

    class Config:
        from_attributes = True

# -------------------------------
# LIKES SCHEMAS
# -------------------------------

class LikeBase(BaseModel):
    user_id: UUID
    artwork_id: UUID
    liked_at: datetime

    class Config:
       from_attributes = True

class ArtworkLikeRequest(BaseModel): # Request schema (optional if using path params in routes)
    artwork_id: UUID

# class LikeResponse(BaseModel): # Response message for like/unlike actions
#     message: str

class LikeCountResponse(BaseModel): # Response schema for like count
    artwork_id: UUID
    like_count: int

class HasLikedResponse(BaseModel): # Boolean response: whether user liked an artwork
    artwork_id: UUID
    user_id: UUID
    has_liked: bool

class ArtworkLike(LikeBase): # Optional: full detailed record (like LikeBase but explicitly named for clarity)
    pass

# -------------------------------
# COMMENTS SCHEMAS
# -------------------------------

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    artwork_id: UUID

class CommentRead(CommentBase):
    id: UUID
    user_id: UUID
    artwork_id: UUID
    created_at: datetime

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
    pass

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

class WishlistCreatePublic(BaseModel):
    artworkId: UUID

class WishlistCreate(BaseModel):
    userId: UUID
    artworkId: UUID

class WishlistRead(WishlistCreate):
    id: UUID
    createdAt: datetime

    class Config:
        from_attributes = True

class WishlistRemove(WishlistCreate):
    id: UUID

    class Config:
        from_attributes = True


# -------------------------------
# CART SCHEMAS
# -------------------------------

class CartCreatePublic(BaseModel):
    artworkId: UUID

class CartCreate(BaseModel):
    userId: UUID
    artworkId: UUID

class CartRead(CartCreate):
    id: UUID
    createdAt: datetime

class CartRemove(CartCreate):
    id: UUID

    class Config:
        from_attributes = True
