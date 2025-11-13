from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional

# -------------------------------
# ARTIST REVIEW SCHEMAS
# -------------------------------

class UserReview(BaseModel):
    username: str
    profileImage: Optional[str] = None

class ArtistReviewBase(BaseModel):
    rating: int
    comment: Optional[str] = None

class ArtistReviewCreate(ArtistReviewBase):
    artistId: UUID

class ArtistReviewRead(ArtistReviewBase):
    id: UUID
    reviewerId: UUID = Field(..., alias="reviewer_id")
    artistId: UUID = Field(..., alias="artist_id")
    createdAt: datetime = Field(..., alias="created_at")
    reviewer: UserReview

    model_config = {
        "from_attributes": True  # ORM parsing
    }

class ArtistRatingSummary(BaseModel): # for calculating average rating
    artistId: UUID
    avgRating: float
    weightedRating: float
    reviewCount: int
    username: Optional[str] = None
    profileImage: Optional[str] = None

    model_config = {
        "from_attributes": True
    }    