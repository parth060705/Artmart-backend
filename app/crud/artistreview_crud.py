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

# def create_artist_review(db: Session, item: artistreview_schemas.ArtistReviewCreate, user_id: UUID):
#     db_review = models.ArtistReview(
#         reviewer_id=str(user_id),
#         artist_id=str(item.artistId),
#         rating=item.rating,
#         comment=item.comment
#     )
#     db.add(db_review)
#     db.commit()
#     db.refresh(db_review)
#     return db_review

def create_artist_review(db: Session, item: artistreview_schemas.ArtistReviewCreate, user_id: UUID):
    # Check if the user already reviewed this artist
    existing_review = (
        db.query(models.ArtistReview)
        .filter(
            models.ArtistReview.reviewer_id == str(user_id),
            models.ArtistReview.artist_id == str(item.artistId)
        )
        .first()
    )

    if existing_review:
        # Update existing review
        existing_review.rating = item.rating
        existing_review.comment = item.comment
        db.commit()
        db.refresh(existing_review)
        return existing_review

    # Otherwise, create a new review
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
    """
    List all artists with their average rating, review count, and rank.
    """

    # Subquery with window function for rank
    result = (
        db.query(
            models.User.id.label("artistId"),
            models.User.name,
            models.User.username,
            models.User.profileImage,
            func.coalesce(func.avg(models.ArtistReview.rating), 0).label("avgRating"),
            func.count(models.ArtistReview.id).label("reviewCount"),
            func.rank()
            .over(order_by=desc(func.coalesce(func.avg(models.ArtistReview.rating), 0)))
            .label("rank")
        )
        .outerjoin(models.ArtistReview, models.User.id == models.ArtistReview.artist_id)
        .group_by(models.User.id)
        .order_by(desc("avgRating"))
        .all()
    )

    # Convert query results to list of dicts for Pydantic response
    return [
        {
            "artistId": r.artistId,
            "name": r.name,
            "username": r.username,
            "profileImage": r.profileImage,
            "avgRating": float(r.avgRating) if r.avgRating is not None else 0.0,
            "reviewCount": int(r.reviewCount) if r.reviewCount is not None else 0,
            "rank": int(r.rank)
        }
        for r in result
    ]
