from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text
from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID
from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
# from app.schemas import schemas
from app.schemas import artworks_schemas
from passlib.context import CryptContext
import cloudinary.uploader
import cloudinary
from typing import List, Optional, Dict
from fastapi import UploadFile, HTTPException
import cloudinary.uploader
import random, string
import re
from sqlalchemy.exc import SQLAlchemyError
# from app.schemas.schemas import (likeArt)
# from app.crud.user_crud import(calculate_completion)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ------------------------------------------------------------------------------------------------------------------
#                                        ADMIN & SUPER-ADMIN ENDPOINTS
# -------------------------------------------------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "svg"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/pjpeg",     
    "image/png",
    "image/svg+xml"
}
MAX_FILE_SIZE_MB = 20


                                                 # USERS
def list_all_users(db: Session):
    return db.query(models.User).all()

def delete_user(db: Session, user_id):  # no UUID typing
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

def update_user_details_admin(db: Session, user_id: str, update_data: dict):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

def get_users_filters(
    db: Session,
    user_id: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    username: Optional[str] = None,
    gender: Optional[str] = None,
    role: Optional[str] = None,
    location: Optional[str] = None,
):
    query = db.query(models.User)
    filters = []
    if user_id:
        filters.append(models.User.id == user_id)
    if name:
        filters.append(models.User.name.ilike(f"%{name}%"))
    if email:
        filters.append(models.User.email == email)
    if username:
        filters.append(models.User.username == username)
    if gender:
        filters.append(models.User.gender.ilike(f"%{gender}%"))
    if role:
        filters.append(models.User.role.ilike(f"%{role}%"))
    if location:
        filters.append(models.User.location.ilike(f"%{location}%"))

    if filters:
        query = query.filter(and_(*filters))
    return query.all()

                                               # ARTWORKS
def list_artworks_admin(db: Session):
    return db.query(models.Artwork).all()

def update_artwork(
    db: Session,
    artwork_id: str,
    artwork_update: artworks_schemas.ArtworkUpdate,
    files: Optional[List[UploadFile]] = None
):
    db_artwork = db.query(models.Artwork).filter(models.Artwork.id == artwork_id).first()

    if not db_artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    update_data = artwork_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_artwork, key, value)

    if files:
        new_image_urls = []

        for f in files:
            if f.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {f.content_type}")

            contents = f.file.read()
            if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)")
            f.file.seek(0)

            try:
                result = cloudinary.uploader.upload(f.file, folder="artworks")
                secure_url = result.get("secure_url")
                if secure_url:
                    new_image_urls.append(secure_url)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

        db_artwork.images = (db_artwork.images or []) + new_image_urls

    db.commit()
    db.refresh(db_artwork)
    return db_artwork

def delete_artwork_admin(db: Session, artwork_id: str):
    # ✅ Load artwork with its related images in one query
    artwork = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.images))  # eager load images
        .filter(models.Artwork.id == artwork_id)
        .first()
    )

    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    # ✅ Delete all images from Cloudinary
    for img in artwork.images:   # ArtworkImage objects
        try:
            cloudinary.uploader.destroy(img.public_id)
        except Exception as e:
            print(f"⚠️ Cloudinary cleanup failed for {img.public_id}: {e}")

    db.delete(artwork)
    db.commit()

    return {
        "message": "Artwork deleted successfully",
        "artwork_id": artwork_id
    }
                                              # ORDERS
def list_all_orders(db: Session):
    return db.query(models.Order)\
        .options(
            joinedload(models.Order.buyer),
            joinedload(models.Order.artwork)
        )\
        .all()

def delete_order(db: Session, order_id: UUID):
    order = db.query(models.Order).filter(models.Order.id == str(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {
        "message": "Order deleted successfully",
        "order_id": order_id }

                                              # FOLLOW & FOLLOWERS
def list_follow_followers(db: Session):
    return (
        db.query(
            models.User.username,
            models.User.profileImage,
            models.followers_association.c.follower_id,
            models.followers_association.c.followed_id,
            models.followers_association.c.created_at
        )
        .join(models.User, models.User.id == models.followers_association.c.follower_id)
        .all()
    )
