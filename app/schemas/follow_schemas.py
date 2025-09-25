from pydantic import BaseModel, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Optional, List

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

class FollowStatus(BaseModel):
    is_following: bool