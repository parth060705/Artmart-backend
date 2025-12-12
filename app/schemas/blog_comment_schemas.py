from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Base Schema (Shared fields)
class BlogCommentBase(BaseModel):
    slug: str  
    content: str

# Create Schema
class BlogCommentCreate(BlogCommentBase):
    pass

# Update Schema
class BlogCommentUpdate(BaseModel):
    content: Optional[str] = None

# Response Schema
class BlogCommentResponse(BaseModel):
    id: str
    slug: str
    user_id: str
    content: str
    created_at: datetime
    updatedAt: datetime
    status: str

    class Config:
        from_attributes = True
