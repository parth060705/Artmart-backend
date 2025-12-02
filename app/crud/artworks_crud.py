from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, UploadFile
from uuid import UUID, uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import artworks_schemas
from passlib.context import CryptContext
import cloudinary.uploader
import cloudinary
from typing import List, Optional, Dict
from fastapi import UploadFile, HTTPException
import cloudinary.uploader
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.artworks_schemas import (likeArt) 
from app.util import util
from sqlalchemy import or_
from app.crud import moderation_crud

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------
# ARTWORK OPERATIONS
# -------------------------
                                              # CREATE ARTWORK #
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "svg", "webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/pjpeg",     
    "image/png",
    "image/svg+xml",
    "image/webp"
}
MAX_FILE_SIZE_MB = 20

def create_artwork(
    db: Session,
    artwork_data: artworks_schemas.ArtworkCreate,
    user_id: UUID,
    files: List[UploadFile],
):
    # 1️⃣ Check user exists
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2️⃣ Enforce forSale logic
    if artwork_data.forSale:   # <-- changed from isSale to forSale
        if artwork_data.price is None:
            raise HTTPException(status_code=400, detail="Price is required for sale artwork")
        if artwork_data.quantity is None:
            raise HTTPException(status_code=400, detail="Quantity is required for sale artwork")
    else:
        # If not for sale, nullify price/quantity to avoid accidental DB insert
        artwork_data.price = None
        artwork_data.quantity = None

    try:
        # 3️⃣ Create artwork record
        db_artwork = models.Artwork(
            **artwork_data.dict(exclude={"images"}),  # exclude images from schema
            artistId=str(user_id),
            status="pending_moderation",  
        )
        db.add(db_artwork)
        db.flush()  # flush to get artwork ID before images

        # 4️⃣ Upload images to Cloudinary
        for file in files:
            if file.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=400, detail=f"Unsupported file type: {file.content_type}"
                )

            contents = file.file.read()
            if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=400, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)"
                )
            file.file.seek(0)

            result = cloudinary.uploader.upload(file.file, folder="artworks")
            secure_url = result.get("secure_url")
            public_id = result.get("public_id")
            if not secure_url or not public_id:
                raise HTTPException(status_code=500, detail="Cloudinary upload failed")

            # 5️⃣ Create ArtworkImage record
            db_image = models.ArtworkImage(
                artwork_id=db_artwork.id,
                url=secure_url,
                public_id=public_id,
            )
            db.add(db_image)

        db.commit()
        db.refresh(db_artwork)

        # Add to moderation queue
        moderation_crud.add_to_moderation(db, table_name="artworks", content_id=db_artwork.id)

        user.profile_completion = util.calculate_completion(user, db)
        db.commit()
        db.refresh(user)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return {
        "message": "Artwork created successfully",
        "artwork": db_artwork,
        "profile_completion": user.profile_completion
    }



#------------------------------------------------------------------------------------------------------
                                            # UPDATE ARTWORK #
# def update_artwork(
#     db: Session,
#     artwork_id: str,
#     user_id: str,
#     artwork_update: artworks_schemas.ArtworkUpdate
# ):
#     db_artwork = db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

#     if not db_artwork:
#         raise HTTPException(status_code=404, detail="Artwork not found")

#     if db_artwork.artistId != user_id:
#         raise HTTPException(status_code=403, detail="Not authorized to update this artwork")

#     # Convert update data to dict
#     update_data = artwork_update.dict(exclude_unset=True)

#     # --- Enforce business rule for price & quantity ---
#     if "isSold" in update_data:
#         is_sold = update_data["isSold"]
#     else:
#         # If not explicitly updated, use current value
#         is_sold = db_artwork.isSold

#     if not is_sold:
#         # If artwork is NOT sold, ignore price and quantity updates
#         update_data.pop("price", None)
#         update_data.pop("quantity", None)
#     else:
#         # If artwork IS sold, require price and quantity values
#         if "price" not in update_data or "quantity" not in update_data:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Price and quantity are required when artwork is sold"
#             )

#     # Apply valid updates
#     for key, value in update_data.items():
#         setattr(db_artwork, key, value)

#     db.commit()
#     db.refresh(db_artwork)

#     return db_artwork

def update_artwork(
    db: Session,
    artwork_id: str,
    user_id: str,
    artwork_update: artworks_schemas.ArtworkUpdate
):
    # Fetch the artwork
    db_artwork = db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

    if not db_artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    # Check if the user owns the artwork
    if db_artwork.artistId != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this artwork")

    # Get fields to update
    update_data = artwork_update.dict(exclude_unset=True)

    # Determine new or existing isSold state
    is_sold = update_data.get("isSold", db_artwork.isSold)

    # --- Business logic for price & quantity ---
    if not is_sold:
        # If not sold, ignore any updates to price or quantity
        update_data.pop("price", None)
        update_data.pop("quantity", None)
    else:
        # If sold, ensure price and quantity are not null
        if update_data.get("price") is None or update_data.get("quantity") is None:
            raise HTTPException(
                status_code=400,
                detail="Price and quantity cannot be null when artwork is sold"
            )

    # Apply updates to the model
    for key, value in update_data.items():
        setattr(db_artwork, key, value)

    # Commit and refresh
    db.commit()
    db.refresh(db_artwork)

    return db_artwork

# --------------------
# ADD IMAGE
# --------------------
def add_artwork_images(db, artwork_id: str, user_id: str, files: list):
    artwork = (
        db.query(models.Artwork)
        .filter_by(id=artwork_id, artistId=user_id)
        .first()
    )
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    new_images = []
    for file in files:
        upload_result = cloudinary.uploader.upload(file.file, folder="artworks")

        # create SQLAlchemy model, not dict
        db_image = models.ArtworkImage(
            artwork_id=artwork.id,
            url=upload_result["secure_url"],
            public_id=upload_result["public_id"],
        )
        db.add(db_image)
        new_images.append(db_image)

    artwork.images.extend(new_images)

    db.commit()
    db.refresh(artwork)
    return artwork

# --------------------
# REPLACE IMAGE
# --------------------
def update_artwork_image(db, artwork_id: str, user_id: str, old_public_id: str, file):
    artwork = (
        db.query(models.Artwork)
        .filter_by(id=artwork_id, artistId=user_id)
        .first()
    )
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")
    
    # checking image in db
    db_image = (
        db.query(models.ArtworkImage)
        .filter_by(artwork_id=artwork.id, public_id=old_public_id)
        .first()
    )
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # destroy image from db
    cloudinary.uploader.destroy(old_public_id)
    
    # update the image
    upload_result = cloudinary.uploader.upload(file.file, folder="artworks")
    db_image.url = upload_result["secure_url"]
    db_image.public_id = upload_result["public_id"]

    db.commit()
    db.refresh(artwork)
    return artwork

# --------------------
# DELETE IMAGE
# --------------------
def delete_artwork_image(db, artwork_id: str, user_id: str, public_id: str):
    artwork = (
        db.query(models.Artwork)
        .filter_by(id=artwork_id, artistId=user_id)
        .first()
    )
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    # Find the image record
    db_image = (
        db.query(models.ArtworkImage)
        .filter_by(artwork_id=artwork.id, public_id=public_id)
        .first()
    )
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Delete from Cloudinary
    cloudinary.uploader.destroy(public_id)

    # Remove from DB
    db.delete(db_image)
    db.commit()
    db.refresh(artwork)

    return artwork
#------------------------------------------------------------------------------------------------------------

                                          # DELETE ARTWORK
# def delete_artwork(db: Session, artwork_id: UUID, user_id: UUID):
#     artwork = db.query(models.Artwork).filter(
#         models.Artwork.id == str(artwork_id),
#         models.Artwork.artistId == str(user_id)).first()
#     if not artwork:
#         raise HTTPException(status_code=404, detail="Artwork not found or unauthorized")
#     db.delete(artwork)
#     db.commit()
#     return {"message": "Artwork deleted successfully", "artwork_id": artwork_id}

def delete_artwork(db: Session, artwork_id: UUID, user_id: UUID):
    # Find artwork that belongs to the user
    artwork = db.query(models.Artwork).filter(
        models.Artwork.id == str(artwork_id),
        models.Artwork.artistId == str(user_id)
    ).first()
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found or unauthorized")

    # Soft delete — set isDeleted flag to True
    artwork.isDeleted = True

    db.commit()
    db.refresh(artwork)
    return {"message": "Artwork marked as deleted successfully", "artwork_id": artwork_id}

                                        # GET ARTWORK LIST                                 
def list_artworks(db: Session) -> List[models.Artwork]:
    artworks = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.artist), joinedload(models.Artwork.likes))
        .order_by(func.random())  # PostgreSQL; use func.rand() for MySQL
        .all()
    )
    return artworks

                                           # GET SPECIFIC ARTWORK
def get_artwork(db: Session, artwork_id: UUID):
    return (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.artist), joinedload(models.Artwork.likes))
        .filter(models.Artwork.id == str(artwork_id))
        .first()
    )

                                          # GET MY ARTWORK

# def get_artworks_by_me(db: Session, user_id: str):
#     # Only fetch non-deleted artworks
#     artworksme = (
#         db.query(models.Artwork)
#         .options(joinedload(models.Artwork.images), joinedload(models.Artwork.likes))
#         .filter(
#             models.Artwork.artistId == user_id,
#             # models.Artwork.isDeleted.is_(False)  # Exclude deleted
#             # models.Artwork.isDeleted == False 
#         )
#         .all()
#     )

#     # total_count = len(artworksme)  # total non-deleted artworks

#     return artworksme
#     # return {
#     #     "total_count": total_count,
#     #     "artworks": artworksme
#     # }

def get_artworks_by_me(db: Session, user_id: str):
    # Only fetch non-deleted artworks (isDeleted False or NULL)
    artworksme = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.images), joinedload(models.Artwork.likes))
        .filter(
            models.Artwork.artistId == user_id,
            or_(
                models.Artwork.isDeleted == False,  # not deleted
                models.Artwork.isDeleted.is_(None)  # or NULL
            )
        )
        .all()
    )

    for artwork in artworksme:
        artwork.how_many_like = {"like_count": len(artwork.likes)}  

    return artworksme

                                          # GET USER ARTWORK
# def get_artworks_by_user(db: Session, user_id: str):
#     artworks = (
#         db.query(models.Artwork)
#         .options(joinedload(models.Artwork.likes))
#         .filter(models.Artwork.artistId == str(user_id))
#         .all()
#     )

#     for artwork in artworks:
#         artwork.how_many_like = {"like_count": len(artwork.likes)}  

#     return artworks


def get_artworks_by_user(db: Session, user_id: str):
    # Query artworks for user, excluding deleted (isDeleted=True)
    artworks = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.likes))
        .filter(
            models.Artwork.artistId == str(user_id),
            or_(
                models.Artwork.isDeleted == False,   # not deleted
                models.Artwork.isDeleted.is_(None)  # or NULL
            )
        )
        .all()
    )

    # Add like count to each artwork
    for artwork in artworks:
        artwork.how_many_like = {"like_count": len(artwork.likes)}  

    return artworks
