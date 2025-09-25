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
from app.schemas.likes_schemas import (likeArt) 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# Saved OPERATIONS
# -------------------------

def add_to_Saved(db: Session, item: schemas.SavedCreate, user_id: UUID):
    db_Saved = models.Saved(
        userId=str(user_id),
        artworkId=str(item.artworkId)
    )
    db.add(db_Saved)
    db.commit()
    db.refresh(db_Saved)
    return db_Saved

def get_user_Saved(db: Session, user_id: UUID):
    return (
        db.query(models.Saved)
        .options(joinedload(models.Saved.artwork))
        .filter(models.Saved.userId == str(user_id))
        .filter(models.Saved.artworkId.isnot(None))  # exclude Saved rows with no artwork
        .all()
    )

def remove_Saved_item(db: Session, user_id: UUID, artwork_id: UUID):
    item = db.query(models.Saved).filter_by(userId=str(user_id), artworkId=str(artwork_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Saved item not found")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Item removed from Saved"}
