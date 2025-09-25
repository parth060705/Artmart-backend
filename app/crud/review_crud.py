from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text
from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID
from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import schemas
from passlib.context import CryptContext
import cloudinary.uploader
import cloudinary
from typing import List, Optional, Dict
from fastapi import UploadFile, HTTPException
import cloudinary.uploader
import random, string
import re
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.schemas import (likeArt) 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# REVIEW OPERATIONS
# -------------------------

def create_review(db: Session, item: schemas.ReviewCreate, user_id: UUID):
    db_review = models.Review(
        reviewerId=str(user_id),
        artistId=str(item.artistId) if item.artistId else None,
        artworkId=str(item.artworkId),
        rating=item.rating,
        comment=item.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def list_reviews_for_artwork(db: Session, artwork_id: UUID):
    return (
        db.query(models.Review)
        .options(joinedload(models.Review.reviewer))
        .filter(models.Review.artworkId == str(artwork_id))
        .all()
    )
