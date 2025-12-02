from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import or_ , and_, func, text
# from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID, uuid4
# from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import comment_schemas
from passlib.context import CryptContext
# import cloudinary.uploader
# import cloudinary
# from typing import List, Optional, Dict
# from fastapi import UploadFile, HTTPException
# import cloudinary.uploader
# import random, string
# import re
# from sqlalchemy.exc import SQLAlchemyError
# from app.schemas.schemas import (likeArt)
from app.crud import moderation_crud


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# COMMENTS OPERATIONS
# -------------------------
def create_comment(db: Session, user_id: UUID, comment_data: models.Comment):
    artwork_id = str(comment_data.artwork_id)
    user_id = str(user_id)

    artwork = db.query(models.Artwork).filter_by(id=artwork_id).first()
    if not artwork:
        return {"message": "Artwork not found."}

    new_comment = models.Comment(
        id=str(uuid4()),
        user_id=user_id,
        artwork_id=artwork_id,
        content=comment_data.content,
        status="pending_moderation"  # default, optional
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # Add to moderation queue
    moderation_crud.add_to_moderation(db, table_name="comments", content_id=new_comment.id)

    return {"message": "Comment added successfully.", "comment": new_comment}

def get_comments_by_artwork(db: Session, artwork_id: str):
    return (
        db.query(models.Comment)
        .options(joinedload(models.Comment.user))
        .filter(models.Comment.artwork_id == artwork_id)
        .all()
    )