from sqlalchemy.orm import Session  
from fastapi import Query
from typing import List, Optional
from app.database import get_db
from app.crud import crud
from app.crud.crud import get_artworks_with_artist_filters

# FOR MEASSAGING
from fastapi import APIRouter, Depends

from app.schemas.schemas import (
    UserSearch,
    ArtworkRead,
    ArtworkCategory
)

router = APIRouter()

# -------------------------
# SEARCH ENDPOINTS
# -------------------------

@router.get("/artworks/search", response_model=List[ArtworkRead])
def search_artworks(
    query: str = Query(..., min_length=2, description="Search artworks"),
    db: Session = Depends(get_db)
):
    return crud.search_artworks(db, query)

@router.get("/search/user", response_model=List[UserSearch])
def search_users(
    query: str = Query(..., min_length=2, description="Search artist"),
    db: Session = Depends(get_db)
):
    return crud.search_users(db, query)

@router.get("/artworks/category/{category}", response_model=List[ArtworkCategory])
def read_artworks_by_category(category: str, db: Session = Depends(get_db)):
    return crud.get_artworks_by_category(db, category)

@router.get("/artworks/filter", response_model=List[ArtworkRead])
def get_artworks_with_filters(
    title: Optional[str] = None,
    price: Optional[float] = None,
    category: Optional[str] = None,
    artist_name: Optional[str] = None,
    location: Optional[str] = None,
    tags: Optional[str] = None,                                #
    db: Session = Depends(get_db)
):
    return get_artworks_with_artist_filters(
        db,
        title=title,
        price=price,
        category=category,
        artist_name=artist_name,
        location=location,
        tags=tags                                                   #
    )