from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator, model_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal, List
from app.models.models import StatusENUM

# -------------------------------
# ARTWORK SCHEMAS
# -------------------------------
class ArtworkImageRead(BaseModel): # IMAGES FORMAT
    id: UUID
    url: str
    public_id: str

    class Config:
        from_attributes = True

class ArtworkArtist(BaseModel): # ARTIST 
    id: UUID      
    username: str
    profileImage: Optional[str] = None

class likeArt(BaseModel): # LIKE
    like_count: int    

class ArtworkAdmin(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)
    price: Optional[float] = None   
    tags: Optional[list[str]] = None
    quantity: Optional[int] = None
    artistId: str
    createdAt: datetime
    category: str
    artist: ArtworkArtist
    # isSold: bool 
    isSold: Optional[bool] = None

    class Config:
        from_attributes = True 

class ArtworkBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)
    price: Optional[float] = None
    tags: Optional[list[str]] = None
    quantity: Optional[int] = None
    isInCart: Optional[bool] = None
    isSaved: Optional[bool] = None
    isLike: Optional[bool] = None
    category: str
    artist: ArtworkArtist
    how_many_like: Optional[likeArt] = None
    forSale: bool


class ArtworkWithLikes(ArtworkBase):
    how_many_like: likeArt

class ArtworkRead(ArtworkBase):
    id: UUID
    # isSold: bool
    isSold: Optional[bool] = None
    createdAt: datetime
    artistId: UUID
    status: Optional[StatusENUM] = None

    class Config:
        from_attributes = True

class ArtworkOnly(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)
    tags: Optional[list[str]] = None
    category: str

    class Config:
        from_attributes = True        
   
class ArtworkCreate(BaseModel):
    title: str
    description: Optional[str] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)
    price: Optional[float] = None
    quantity: Optional[int] = None
    tags: Optional[list[str]] = None
    category: str
    forSale: bool

    @model_validator(mode="before")
    def check_price_quantity_for_sale(cls, values):
        for_sale = values.get("forSale")
        price = values.get("price")
        quantity = values.get("quantity")
        if for_sale:
            if price is None:
                raise ValueError("Price is required when artwork is for sale")
            if quantity is None:
                raise ValueError("Quantity is required when artwork is for sale")
        return values
                          
class ArtworkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    tags: Optional[list[str]] = None
    quantity: Optional[int] = None
    isSold: Optional[bool] = None
    images: List[ArtworkImageRead] = Field(default_factory=list)

class ArtworkCreateResponse(BaseModel): # MESSAGE AFTER CREATION
    message: str
    artwork: ArtworkRead

class ArtworkDelete(BaseModel): # MESSAGE AFTER DELETION
    message: str
    artwork_id: UUID

class ArtworkCategory(ArtworkRead):
    category: str

    class Config:
        from_attributes = True

class ArtworkMe(BaseModel):
    id: str
    title: str
    description: Optional[str]
    price: Optional[float] = None
    category: str
    images: List[ArtworkImageRead] = Field(default_factory=list)
    artistId: str
    how_many_like: Optional[likeArt] = None
    createdAt: datetime
    # isSold: bool
    isSold: Optional[bool] = None

    class Config:
        from_attributes = True 

class ArtworkMeResponse(BaseModel):
    total_count: int
    artworks: List[ArtworkMe]

class ArtworkCommunityJoin(BaseModel):
    title: str
    description: Optional[str]
    how_many_like: Optional[likeArt] = None
    category: str
    images: List[ArtworkImageRead] = Field(default_factory=list)

    class Config:
        from_attributes = True 
