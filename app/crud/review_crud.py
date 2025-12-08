from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import or_ , and_, func, text
# from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID, uuid4
# from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import review_schemas
from passlib.context import CryptContext
from app.crud import moderation_crud

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# REVIEW OPERATIONS
# -------------------------

def create_review(db: Session, item: review_schemas.ReviewCreate, user_id: UUID):
    db_review = models.Review(
        reviewerId=str(user_id),
        artistId=str(item.artistId) if item.artistId else None,
        artworkId=str(item.artworkId),
        rating=item.rating,
        comment=item.comment,
        status="pending_moderation"  # default, optional
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Add to moderation queue
    moderation_crud.add_to_moderation(db, table_name="reviews", content_id=db_review.id)

    return db_review

def list_reviews_for_artwork(db: Session, artwork_id: UUID):
    return (
        db.query(models.Review)
        .options(joinedload(models.Review.reviewer))
        .filter(models.Review.artworkId == str(artwork_id))
        .order_by(models.Review.createdAt.desc())
        .all()
    )
