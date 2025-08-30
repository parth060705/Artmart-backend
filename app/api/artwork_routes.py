from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session  
from fastapi import Form
from uuid import UUID
from typing import List, Optional
from app.core.auth import get_current_user
from app.database import get_db
from app.models.models import User
from app.crud import crud
from app.models import models
from sqlalchemy.orm import joinedload

# FOR MEASSAGING
from fastapi import APIRouter, Depends

from app.schemas.schemas import (
    ArtworkCreate, ArtworkRead, ArtworkCreateResponse, ArtworkDelete,
    ArtworkUpdate, ArtworkArtist,
)

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# -------------------------
# ARTWORK ENDPOINTS
# -------------------------
@user_router.post("/artworks", response_model=ArtworkCreateResponse)
def create_artwork(
    title: str = Form(...),
    price: float = Form(...),
    tags: list[str] = Form(...),
    quantity: int = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    files: List[UploadFile] = File(...),  # MULTIPLE files now
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artwork_data = ArtworkCreate(
        title=title,
        description=description,
        price=price,
        tags=tags,
        quantity=quantity,
        category=category,
    )
    return crud.create_artwork(
        db=db,
        artwork_data=artwork_data,
        user_id=current_user.id,
        files=files,  # <-- List of UploadFile
    )

@user_router.patch("/update/artworks/{artwork_id}", response_model=ArtworkRead)
def update_artwork(
    artwork_id: UUID,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    tags: Optional[list[str]] = Form(None),
    quantity: Optional[int] = Form(None),
    isSold: Optional[bool] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_files = [
        f for f in (files or [])
        if isinstance(f, UploadFile) and f.filename and f.content_type != "application/octet-stream"
    ]

    artwork_update = ArtworkUpdate(
        title=title,
        description=description,
        category=category,
        price=price,
        tags=tags,
        quantity=quantity,
        isSold=isSold
    )

    return crud.update_artwork(
        db=db,
        artwork_id=str(artwork_id),
        user_id=str(current_user.id),
        artwork_update=artwork_update,
        files=valid_files  # pass only real files
    )

@user_router.delete("/artworks/{artwork_id}", response_model=ArtworkDelete)
def delete_artwork(
    artwork_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    return crud.delete_artwork(db, artwork_id=artwork_id, user_id=current_user.id)

@router.get("/artworks", response_model=List[ArtworkRead])
def list_artworks_route(db: Session = Depends(get_db)):
    artworks = crud.list_artworks(db)
    result = []
    for art in artworks:
        like_count = len(art.likes) if art.likes else 0
        result.append(
            ArtworkRead(
                id=art.id,
                title=art.title,
                description=art.description,
                category=art.category,
                price=art.price,
                tags=art.tags,
                quantity=art.quantity,
                isSold=art.isSold,
                images=art.images,
                createdAt=art.createdAt,
                artistId=art.artistId,
                how_many_like={"like_count": like_count},
                artist=ArtworkArtist(
                    username=art.artist.username,
                    profileImage=art.artist.profileImage
                ),
            )
        )
    return result

@user_router.get("/artworks", response_model=List[ArtworkRead])
def list_artworks_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud.list_artworks_with_cart_flag(db, current_user.id)


@router.get("/artworks/{artwork_id}", response_model=ArtworkRead)
def get_artwork(artwork_id: UUID, db: Session = Depends(get_db)):
    db_artwork = db.query(models.Artwork).options(joinedload(models.Artwork.artist)).filter(models.Artwork.id == str(artwork_id)).first()
    if not db_artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    like_count = len(db_artwork.likes) if db_artwork.likes else 0
    return ArtworkRead(
        id=db_artwork.id,
        title=db_artwork.title,
        description=db_artwork.description,
        category=db_artwork.category,
        price=db_artwork.price,
        tags=db_artwork.tags,
        quantity=db_artwork.quantity,
        isSold=db_artwork.isSold,
        images=db_artwork.images,
        createdAt=db_artwork.createdAt,
        artistId=db_artwork.artistId,
        artist=ArtworkArtist(
            username=db_artwork.artist.username,
            profileImage=db_artwork.artist.profileImage
        ),
        how_many_like={"like_count": like_count}
    )

# DELETE SINGLE IMAGE
@user_router.delete("/artworks/{artwork_id}/images")
def delete_artwork_image(
    artwork_id: UUID,
    image_url: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artwork = db.query(models.Artwork).filter(
        models.Artwork.id == str(artwork_id),
        models.Artwork.artistId == current_user.id
    ).first()

    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found or not owned by user")

    if not artwork.images or image_url not in artwork.images:
        raise HTTPException(status_code=404, detail="Image not found in artwork")

    # remove image
    artwork.images = [img for img in artwork.images if img != image_url]

    db.commit()
    db.refresh(artwork)
    return {"message": "Image deleted successfully", "images": artwork.images}

# Replace/Update Image
@user_router.patch("/artworks/{artwork_id}/images")
async def update_artwork_image(
    artwork_id: UUID,
    old_image_url: str = Form(...),
    new_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artwork = db.query(models.Artwork).filter(
        models.Artwork.id == str(artwork_id),
        models.Artwork.artistId == current_user.id
    ).first()

    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found or not owned by user")

    if not artwork.images or old_image_url not in artwork.images:
        raise HTTPException(status_code=404, detail="Old image not found in artwork")

    # upload new file -> return URL
    new_image_url = await save_file(new_file)   # <-- implement your S3/local save

    # replace in list
    artwork.images = [new_image_url if img == old_image_url else img for img in artwork.images]

    db.commit()
    db.refresh(artwork)
    return {"message": "Image replaced successfully", "images": artwork.images}

# Add Extra Images
@user_router.post("/artworks/{artwork_id}/images")
async def add_artwork_images(
    artwork_id: UUID,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artwork = db.query(models.Artwork).filter(
        models.Artwork.id == str(artwork_id),
        models.Artwork.artistId == current_user.id
    ).first()

    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found or not owned by user")

    # upload each file
    new_urls = []
    for file in files:
        url = await save_file(file)   # <-- same as in create
        new_urls.append(url)

    if not artwork.images:
        artwork.images = []

    artwork.images.extend(new_urls)

    db.commit()
    db.refresh(artwork)
    return {"message": "Images added successfully", "images": artwork.images}

