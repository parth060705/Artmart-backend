from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator, model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal, List
from app.schemas.follow_schemas import FollowList

# ENUM TYPES
RoleType = Literal["user", "admin", "store"]

# # -------------------------------
# # TOKENS
# # -------------------------------

# class Token(BaseModel):
#     access_token: str
#     refresh_token: str
#     token_type: str

# class TokenData(BaseModel):
#     username: str | None = None

# class UserAuthResponse(BaseModel):
#     user: UserRead
#     tokens: Token    

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

class ErrorResponse(BaseModel):
    message: str
    suggestions: Optional[List[str]] = None
    
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
    isAgreedtoTC: bool
    profile_completion: Optional[int] = 0      #

    @field_validator("pincode", "phone", mode="before")
    def empty_or_invalid_to_none(cls, v):
        if v in (None, "", "string"):  # treat invalid input as None
            return None
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    pincode: Optional[str] = Field(default=None, pattern=r'^\d{6}$')
    phone: Optional[str] = Field(default=None, pattern=r'^(\+91)?\d{10}$')

    @field_validator("age","pincode", "phone", mode="before")
    def empty_or_invalid_to_none(cls, v):
        if v in (None, "", "string"):  # treat invalid input as None
            return None
        return v

class UserRead(UserBase):
    id: UUID
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    profile_completion: Optional[int] = None      #
    avgRating: Optional[float] = None
    weightedRating: Optional[float] = None
    reviewCount: Optional[int] = None
    rank: Optional[int] = None
    role: Optional[str] = None
    followers: Optional[FollowList] = None     
    following: Optional[FollowList] = None
    # is_reviewed: Optional[bool] = None


    class Config:
        from_attributes = True  

class ProfileImageResponse(BaseModel):
    message: str
    profileImage: str

class DeleteMessageUser(BaseModel):  # ADMIN level
    message: str    

class UserSearch(BaseModel):
    id: str
    name: str
    username: str
    profileImage: Optional[HttpUrl] = None
    # location: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    avgRating: Optional[float] = None
    weightedRating: Optional[float] = None
    reviewCount: Optional[int] = None
    rank: Optional[int] = None
    followers: Optional[FollowList] = None     
    following: Optional[FollowList] = None
    is_reviewed: Optional[bool] = None

    class Config:
        from_attributes = True

class ResetPasswordWithOTPSchema(BaseModel): # for password reset
    email: str
    otp: str
    new_password: str        

class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str    

# -------------------------------
# TOKENS
# -------------------------------

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UserAuthResponse(BaseModel):
    # user: UserRead
    tokens: Token    
