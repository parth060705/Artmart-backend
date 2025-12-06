from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.models import CommunityType

# -----------------------------
# COMMUNITY MEMBER SCHEMAS
# -----------------------------
class UserBase(BaseModel):
    id: str
    username: Optional[str] = None  # or whatever fields exist
    profileImage: Optional[HttpUrl] = None


    class Config:
        from_attributes = True  

class CommunityMemberBase(BaseModel):
    id: str
    community_id: str
    user_id: str
    joined_at: datetime

    class Config:
        from_attributes = True  

class CommunityMemberCreate(BaseModel):
    user_id: str


class CommunityMemberResponse(CommunityMemberBase):
    user: Optional[UserBase]


# -----------------------------
# COMMUNITY LIKE SCHEMAS
# -----------------------------
class CommunityLikeBase(BaseModel):
    id: str
    artwork_id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True  

class CommunityLikeCreate(BaseModel):
    user_id: str


class CommunityLikeResponse(CommunityLikeBase):
    user: Optional[UserBase]


# -----------------------------
# COMMUNITY ARTWORK SCHEMAS
# -----------------------------
class CommArtworkImageRead(BaseModel): # IMAGES FORMAT
    id: UUID
    url: str
    public_id: str

    class Config:
        from_attributes = True
class CommunityArtworkBase(BaseModel):
    id: str
    community_id: str
    user_id: str
    content: str
    image: List[CommArtworkImageRead] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True  

class CommunityArtworkCreate(BaseModel):
    content: str
    image: Optional[str] = None


class CommunityArtworkResponse(CommunityArtworkBase):
    user: Optional[UserBase]
    likes: Optional[List[CommunityLikeResponse]] = []


# -----------------------------
# COMMUNITY SCHEMAS
# -----------------------------
class CommunityBase(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: Optional[str]
    bannerImage: Optional[str]
    type: Optional[str] 
    created_at: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True  

class CommunityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    bannerImage: Optional[str] = None
    type: Optional[str] = "public" 

class CommunityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bannerImage: Optional[str] = None 
    type: Optional[CommunityType] = None 

class CommunitySearchResponse(CommunityBase):
    owner: Optional[UserBase]

class CommunityResponse(CommunityBase):
    owner: Optional[UserBase]
    members: Optional[List[CommunityMemberResponse]] = []
    artworks: Optional[List[CommunityArtworkResponse]] = []

class CommunitySearch(BaseModel):
    id: str
    name: str
    description: Optional[str]
    bannerImage: Optional[str] 
    type: Optional[str]

    class Config:
        from_attributes = True

# -----------------------------
# COMMUNITY JOIN REQUEST
# -----------------------------

class JoinRequestBase(BaseModel):
    id: str
    community_id: str
    user_id: str
    joinstatus: str
    created_at: datetime

    class Config:
        from_attributes = True
