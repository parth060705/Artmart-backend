from sqlalchemy.orm import Session, joinedload
from uuid import UUID, uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import artistreview_schemas
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy import desc, func
# from app.crud.user_crud import get_user_rating_info
from app.util import util_artistrank

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# ARTIST REVIEW OPERATIONS
# -------------------------

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
    List all artists with their average rating, review count, and rank
    using the get_user_rating_info() helper.
    """

    artists = db.query(models.User).all()
    results = []

    for artist in artists:
        rating_info = util_artistrank.get_user_rating_info(db, artist.id)

        results.append({
            "artistId": artist.id,
            "name": artist.name,
            "username": artist.username,
            "profileImage": artist.profileImage,
            "avgRating": rating_info["avgRating"],
            "reviewCount": rating_info["reviewCount"],
            "weightedRating": rating_info["weightedRating"],  # ✅ fixed
            "rank": rating_info["rank"]
        })

    # Sort by weightedRating instead of avgRating (more fair)
    results.sort(key=lambda x: x["weightedRating"], reverse=True)

    return results
