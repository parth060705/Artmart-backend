from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.models import FeedbackTypeEnum, FeedbackStatusEnum


class FeedbackBase(BaseModel):
    type: FeedbackTypeEnum
    message: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)
    page: Optional[str] = None
    feature: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    pass


class FeedbackUpdate(BaseModel):
    """Admin-only updates"""
    status: Optional[FeedbackStatusEnum] = None
    admin_note: Optional[str] = Field(None, max_length=2000)


class FeedbackRead(FeedbackBase):
    id: UUID
    user_id: Optional[UUID]
    status: FeedbackStatusEnum
    admin_note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
