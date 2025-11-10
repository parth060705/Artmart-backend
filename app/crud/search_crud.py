from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text, desc
# from fastapi import HTTPException, UploadFile, File, status
# from uuid import UUID
# from uuid import UUID, uuid4

# from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
# from app.schemas import schemas
from passlib.context import CryptContext
# import cloudinary.uploader
# import cloudinary
from typing import List, Optional, Dict
# from fastapi import UploadFile, HTTPException
# import cloudinary.uploader
# import random, string
# import re
# from sqlalchemy.exc import SQLAlchemyError
# from app.schemas.schemas import (likeArt)
# from crud.user_crud import(calculate_completion)
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import models
# from app.crud.user_crud import get_user_rating_info
from app.util import util_artistrank

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# SEARCH OPERATIONS
# -------------------------

def search_artworks(db: Session, query: str):  # ilike is use for searh in MYSQL
    return db.query(models.Artwork).filter(
        or_(
            models.Artwork.title.ilike(f"%{query}%"),
            models.Artwork.category.ilike(f"%{query}%")
            )).all()

def search_users(db: Session, query: str):
    # Fetch users matching the query
    users = (
        db.query(
            models.User.id,
            models.User.name,
            models.User.username,
            models.User.profileImage,
            models.User.location,
            models.User.gender,
            models.User.age,
            models.User.bio,
        )
        .filter(
            or_(
                models.User.username.ilike(f"%{query}%"),
                models.User.name.ilike(f"%{query}%")
            )
        )
        .all()
    )

    result = []

    for u in users:
        # ✅ Fetch rating info per user
        rating_info = util_artistrank.get_user_rating_info(db, u.id)  

        result.append({
            "id": str(u.id),
            "name": u.name,
            "username": u.username,
            "profileImage": u.profileImage,
            "location": u.location,
            "gender": u.gender,
            "age": u.age,
            "bio": u.bio,
            "avgRating": rating_info.get("avgRating"),
            "reviewCount": rating_info.get("reviewCount"),
            "rank": rating_info.get("rank"),
        })

    return result



def get_artworks_by_category(db: Session, category: str):
    return db.query(models.Artwork).filter(
        models.Artwork.category.ilike(f"%{category.strip()}%")
    ).all()

                # SEARCH ARTWORK BY SPECIFICATION OF TITLE, PRICE, CATEGORY, ARTIST NAME, LOCATION
def get_artworks_with_artist_filters(
    db: Session,
    artwork_id: Optional[str] = None,
    title: Optional[str] = None,
    price: Optional[float] = None,
    category: Optional[str] = None,
    artist_name: Optional[str] = None,
    location: Optional[str] = None,
    tags: Optional[str] = None,                                     #
    user_id: Optional[str] = None,
):
    query = db.query(models.Artwork).join(models.Artwork.artist)
    filters = []
    if artwork_id:
        filters.append(models.Artwork.id == artwork_id)
    if title:
        filters.append(models.Artwork.title.ilike(f"%{title}%"))
    if price:
        filters.append(models.Artwork.price == price)
    if category:
        filters.append(models.Artwork.category.ilike(f"%{category}%"))
    if artist_name:
        filters.append(models.User.name.ilike(f"%{artist_name}%"))
    if location:
        filters.append(models.User.location.ilike(f"%{location}%"))
    if tags:                                                                   #
        filters.append(models.Artwork.tags.ilike(f"%{tags}%"))    
    if user_id:
        filters.append(models.User.id == user_id)

    if filters:
        query = query.filter(and_(*filters))
    return query.options(joinedload(models.Artwork.artist)).all()