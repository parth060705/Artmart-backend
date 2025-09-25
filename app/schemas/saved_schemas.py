from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List

# -------------------------------
# SAVED SCHEMAS
# -------------------------------

#-------------------- IMAGE HELPER CLASS -----------------
class ArtworkImageRead(BaseModel): # IMAGES FORMAT
    id: UUID
    url: str
    public_id: str

    class Config:
        from_attributes = True
#---------------------------------------------------------


class SavedArtworkRead(BaseModel): 
    id: UUID
    images: List[ArtworkImageRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SavedCreatePublic(BaseModel):
    artworkId: UUID

class SavedCreate(BaseModel):
    userId: UUID
    artworkId: UUID

class SavedRead(BaseModel):
    id: UUID
    artwork: SavedArtworkRead
    createdAt: datetime

    class Config:
        from_attributes = True

class SavedRemove(SavedCreate):
    id: UUID

    class Config:
        from_attributes = True

