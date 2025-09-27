from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text
# from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID, uuid4
# from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import artworks_schemas
from passlib.context import CryptContext
# import cloudinary.uploader
# import cloudinary
from typing import List, Optional, Dict
# from fastapi import UploadFile, HTTPException
# import cloudinary.uploader
# import random, string
# import re
# from sqlalchemy.exc import SQLAlchemyError
# from app.schemas.likes_schemas import (likeArt)
# from crud.user_crud import(calculate_completion)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------
#  RECOMMENDATION ENDPOINTS
# -------------------------

def get_recommendation(db: Session, artwork_id: UUID, limit: int = 10) -> List[artworks_schemas.ArtworkRead]:
    target_artwork = db.query(models.Artwork)\
    .options(joinedload(models.Artwork.artist),
             joinedload(models.Artwork.likes),
             joinedload(models.Artwork.images))\
    .filter(models.Artwork.id == artwork_id, models.Artwork.isDeleted == False)\
    .first()


    if not target_artwork:
        print("❌ No target artwork found")
        return []

    filters = []

    # Title filter
    if target_artwork.title:
        words = [w.strip() for w in target_artwork.title.split() if w.strip()]
        if words:
            filters.append(or_(*[models.Artwork.title.ilike(f"%{w}%") for w in words]))

    # Category filter
    if target_artwork.category:
        filters.append(models.Artwork.category.ilike(target_artwork.category))

    # Tags filter
    preferred_tags = set()
    if target_artwork.tags:
        if isinstance(target_artwork.tags, list):
            for entry in target_artwork.tags:
                preferred_tags.update([t.strip() for t in entry.split(",") if t.strip()])
        elif isinstance(target_artwork.tags, str):
            preferred_tags.update([t.strip() for t in target_artwork.tags.split(",") if t.strip()])

    if preferred_tags:
        tag_filters = [models.Artwork.tags.ilike(f"%{tag}%") for tag in preferred_tags]
        filters.append(or_(*tag_filters))

    # Query other artworks excluding the target
    query = db.query(models.Artwork).filter(models.Artwork.id != artwork_id)
    if filters:
        query = query.filter(or_(*filters))

    results = query.order_by(func.random()).limit(limit).all()

    # Convert to Pydantic schemas
    return [artworks_schemas.ArtworkRead.model_validate(art) for art in results]


