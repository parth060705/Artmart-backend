from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

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
