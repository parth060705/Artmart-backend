from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

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