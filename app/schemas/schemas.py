from pydantic import BaseModel, EmailStr, HttpUrl, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal, List

# ENUM TYPES
RoleType = Literal["user", "admin", "store"]
PaymentStatus = Literal["pending", "paid", "failed"]
PaymentMethodEnum = Literal["credit_card", "debit_card", "net_banking", "upi", "cod"]
MessageType = Literal["message", "typing", "read"]

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

class UserUpdateAdmin(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    # profileImage: Optional[HttpUrl] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    role: Optional[str] = None
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')

class UserBaseAdmin(BaseModel):
    id: str
    name: str
    email: EmailStr
    username: str
    profileImage: Optional[HttpUrl] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    role: str
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')

class UserBase(BaseModel):
    name: str
    email: EmailStr
    username: str
    profileImage: Optional[HttpUrl] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')


class UserCreate(BaseModel):
    password: str
    name: str
    email: EmailStr
    username: str
    profileImage: Optional[HttpUrl] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')


class UserUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')

class UserRead(UserBase):
    # id: UUID
    createdAt: datetime
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True  

class ProfileImageResponse(BaseModel):
    message: str
    profileImage: str

class DeleteMessageUser(BaseModel):  # ADMIN level
    message: str    

class UserSearch(BaseModel):
    name: str
    username: str
    profileImage: Optional[HttpUrl] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
   
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

class LikeCountResponse(BaseModel):
    artwork_id: UUID
    like_count: int

class HasLikedResponse(BaseModel): # MESSAGE IF YOU LIKED
    artwork_id: UUID
    user_id: UUID
    has_liked: bool

# -------------------------------
# ARTWORK SCHEMAS
# -------------------------------
class ArtworkImageRead(BaseModel):
    id: UUID
    url: str
    public_id: str

    class Config:
        from_attributes = True   # ✅ for Pydantic v2


class ArtworkArtist(BaseModel):
    username: str
    profileImage: Optional[str] = None

class likeArt(BaseModel): 
    like_count: int    

class ArtworkAdmin(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)
    price: float
    tags: Optional[list[str]] = None
    quantity: Optional[int] = None
    artistId: str
    createdAt: datetime
    category: str
    artist: ArtworkArtist
    isSold: bool   

class ArtworkBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)
    price: float
    tags: Optional[list[str]] = None
    quantity: Optional[int] = None
    isInCart: Optional[bool] = None # for isincart flag
    category: str
    artist: ArtworkArtist
    how_many_like: Optional[likeArt] = None 

class ArtworkWithLikes(ArtworkBase):
    how_many_like: likeArt

class ArtworkRead(ArtworkBase):
    id: UUID
    isSold: bool
    createdAt: datetime
    artistId: UUID

    class Config:
        from_attributes = True

class ArtworkCreate(BaseModel):
    title: str
    description: Optional[str] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)
    price: float
    tags: Optional[list[str]] = None
    quantity: Optional[int] = None
    category: str

class ArtworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    tags: Optional[list[str]] = None
    quantity: Optional[int] = None
    isSold: Optional[bool] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)

class ArtworkCreateResponse(BaseModel): # MESSAGE AFTER CREATION
    message: str
    artwork: ArtworkRead

class ArtworkDelete(BaseModel): # MESSAGE AFTER DELETION
    message: str
    artwork_id: UUID

class ArtworkCategory(ArtworkRead):
    category: str

    class Config:
        from_attributes = True

class ArtworkMe(BaseModel):
    id: str
    title: str
    description: Optional[str]
    price: float
    category: str
    images: List[ArtworkImageRead] = Field(default_factory=list)
    artistId: str
    createdAt: datetime
    isSold: bool

    class Config:
        from_attributes = True 

# -------------------------------
# COMMENTS SCHEMAS
# -------------------------------
class UserComment(BaseModel):
    username: str
    profileImage: Optional[str] = None

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    artwork_id: UUID

class CommentRead(CommentBase):
    id: UUID
    user_id: UUID
    artwork_id: UUID
    created_at: datetime
    user: UserComment

    class Config:
        from_attributes = True

# -------------------------------
# ORDER SCHEMAS
# -------------------------------
class UserDetail(BaseModel):
    username: str
    name: str
    location: Optional[str] = None

class ArtworkDetail(BaseModel):
    title: str
    price: float    

class OrderBase(BaseModel):
    artworkId: Optional[UUID]
    totalAmount: float
    paymentStatus: PaymentStatus

class OrderCreate(OrderBase):
    pass

class OrderRead(OrderBase):
    id: UUID
    buyerId: UUID
    createdAt: datetime
    buyer: UserDetail
    artwork: ArtworkDetail

    class Config:
        from_attributes = True

class OrderDelete(BaseModel):
    message: str
    order_id: UUID        

# -------------------------------
# REVIEW SCHEMAS
# -------------------------------
class UserReview(BaseModel):
    username: str
    profileImage: Optional[str] = None

class ReviewBase(BaseModel):
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    artistId: Optional[UUID] = None
    artworkId: UUID  

class ReviewRead(ReviewBase):
    id: UUID
    reviewerId: UUID
    artworkId: UUID
    createdAt: datetime
    reviewer: UserReview 

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
    purchase_quantity: int = 1  # Default to 1

class CartCreate(BaseModel):
    userId: UUID
    artworkId: UUID
    purchase_quantity: int = 1  # Match default from public schema

class CartRead(CartCreate):
    id: UUID
    createdAt: datetime

    class Config:
        from_attributes = True

class CartRemove(BaseModel):
    id: UUID

    class Config:
        from_attributes = True

# -------------------------------
# FOLLOW SCHEMAS
# -------------------------------
class FollowsUser(BaseModel):
    username: str

class UserShort(BaseModel):
    id: str
    username: str
    name: str
    profileImage: Optional[HttpUrl] = None

class FollowList(BaseModel):
    users: List[UserShort]
    count: int

class FollowFollowers(FollowsUser):
    follower_id: UUID
    followed_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True 

# -------------------------------
# CHAT SCHEMAS
# -------------------------------

class MessageBase(BaseModel):
    receiver_id: str
    content: Optional[str] = None
    action: Literal["message", "typing", "read"]

class MessageCreate(MessageBase):
    pass

class MessageOut(BaseModel):
    sender_id: str
    receiver_id: str
    content: str
    timestamp: datetime
    is_read: bool = False

    class Config:
        from_attributes = True


