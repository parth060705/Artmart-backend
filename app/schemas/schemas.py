from pydantic import BaseModel, EmailStr, HttpUrl, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal, List

# ENUM TYPES
RoleType = Literal["user", "admin"]
PaymentStatus = Literal["pending", "paid", "failed"]

# -------------------------------
# TOKENS
# -------------------------------

class Token(BaseModel):
    access_token: str
    refresh_token: str
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
    profileImage: Optional[HttpUrl] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')

class UserRead(UserBase):
    id: UUID
    createdAt: datetime

    class Config:
        from_attributes = True  

class ProfileImageResponse(BaseModel):
    message: str
    profileImage: str

class UserSearch(BaseModel):
    name: str
    email: EmailStr
    username: str
    profileImage: Optional[HttpUrl] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')

    class Config:
        from_attributes = True

# -------------------------------
# ARTWORK SCHEMAS
# -------------------------------

class ArtworkBase(BaseModel):
    title: str
    description: Optional[str] = None
    images: Optional[List[HttpUrl]] = None
    price: float
    category: str


class ArtworkCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str


class ArtworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    isSold: Optional[bool] = None
    images: Optional[List[HttpUrl]] = None


class ArtworkRead(ArtworkBase):
    id: UUID
    isSold: bool
    createdAt: datetime
    artistId: UUID

    class Config:
        from_attributes = True


class ArtworkCreateResponse(BaseModel):
    message: str
    artwork: ArtworkRead
    artworkImage: Optional[HttpUrl] = None


class ArtworkDelete(BaseModel):
    message: str
    artwork_id: UUID


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

class LikeCountResponse(BaseModel): 
    artwork_id: UUID
    like_count: int

class HasLikedResponse(BaseModel):
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

# -------------------------------
# FOLLOW SCHEMAS
# -------------------------------

class UserShort(BaseModel):
    id: str
    username: str
    name: str
    profileImage: Optional[str] = Field(alias="profileImageUrl")

class FollowList(BaseModel):
    users: List[UserShort]
    count: int

class FollowFollowers(BaseModel):
    follower_id: UUID
    followed_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True 
