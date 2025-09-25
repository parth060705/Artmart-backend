from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List

# -------------------------------
# CART SCHEMAS
# -------------------------------

#-------------------- IMAGE HELPER CLASS -----------------
class ArtworkImageRead(BaseModel): # IMAGES FORMAT
    id: UUID
    url: str
    public_id: str

    class Config:
        from_attributes = True
#---------------------------------------------------------

class CartArtworkRead(BaseModel): 
    id: UUID
    images: List[ArtworkImageRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
        
class CartCreatePublic(BaseModel):
    artworkId: UUID
    purchase_quantity: int = 1  # Default to 1

class CartCreate(BaseModel):
    userId: UUID
    artworkId: UUID
    purchase_quantity: int = 1  # Match default from public schema

class CartRead(CartCreate):
    id: UUID
    artwork: CartArtworkRead  
    createdAt: datetime

    class Config:
        from_attributes = True

class CartRemove(BaseModel):
    id: UUID

    class Config:
        from_attributes = True
