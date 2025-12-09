from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.artworks_schemas import ArtworkCommunityJoin

# -------------------------
# COMMUNITY ARTWORK SCHEMAS
# -------------------------

class CommunityArtworkCreate(BaseModel):
    artwork_id: str

class CommunityArtworkResponse(BaseModel):
    id: str
    community_id: str
    user_id: str   # artist_id
    artwork_id: str
    artwork:ArtworkCommunityJoin
    created_at: datetime

    class Config:
        from_attributes = True