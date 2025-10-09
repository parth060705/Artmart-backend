from sqlalchemy.orm import Session, joinedload
from uuid import UUID, uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import artistreview_schemas
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy import desc, func

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# ARTIST REVIEW OPERATIONS
# -------------------------

def create_artist_review(db: Session, item: artistreview_schemas.ArtistReviewCreate, user_id: UUID):
    db_review = models.ArtistReview(
        reviewer_id=str(user_id),
        artist_id=str(item.artistId),
        rating=item.rating,
        comment=item.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


def reviews_for_artist(db: Session, artist_id: UUID):
    return (
        db.query(models.ArtistReview)
        .options(joinedload(models.ArtistReview.reviewer))  # preload reviewer
        .filter(models.ArtistReview.artist_id == str(artist_id))
        .all()
    )

def list_artists_by_rating(db: Session):
    result = (
        db.query(
            models.User.id.label("artistId"),
            models.User.username,
            models.User.profileImage,
            func.avg(models.ArtistReview.rating).label("avgRating"),
            func.count(models.ArtistReview.id).label("reviewCount")
        )
        .join(models.ArtistReview, models.User.id == models.ArtistReview.artist_id)
        .group_by(models.User.id)
        .order_by(desc("avgRating"))
        .all()
    )

    # Convert tuples to list of dicts for Pydantic
    return [
        {
            "artistId": r.artistId,
            "username": r.username,
            "profileImage": r.profileImage,
            "avgRating": float(r.avgRating),
            "reviewCount": r.reviewCount
        }
        for r in result
    ]