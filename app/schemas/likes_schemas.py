from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

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