from sqlalchemy import or_ , and_, func, text, desc
from app.models import models



# 4)HELPER CLASS FOR AVGRATING, REVIEW COUNT AND CALCULATING RANK
def get_user_rating_info(db, user_id, m=5):
    # Step 1: Get avg rating and review count for this artist
    rating_data = (
        db.query(
            func.avg(models.ArtistReview.rating).label("avgRating"),
            func.count(models.ArtistReview.id).label("reviewCount")
        )
        .filter(models.ArtistReview.artist_id == str(user_id))
        .first()
    )

    avg_rating = float(rating_data.avgRating or 0.0)
    review_count = int(rating_data.reviewCount or 0)

    # Step 2: Get global average rating (C)
    global_avg = db.query(func.avg(models.ArtistReview.rating)).scalar()
    global_avg = float(global_avg or 0.0)

    # Step 3: Compute weighted rating (Bayesian formula)
    weighted_rating = (
        (review_count / (review_count + m)) * avg_rating
        + (m / (review_count + m)) * global_avg
        if (review_count + m) > 0 else 0.0
    )

    # Step 4: Compute weighted ratings for all artists to get ranks
    artist_stats = (
        db.query(
            models.User.id.label("artist_id"),
            func.avg(models.ArtistReview.rating).label("avgRating"),
            func.count(models.ArtistReview.id).label("reviewCount")
        )
        .outerjoin(models.ArtistReview, models.User.id == models.ArtistReview.artist_id)
        .group_by(models.User.id)
        .all()
    )

    ranked_artists = []
    for artist in artist_stats:
        R = float(artist.avgRating or 0.0)
        v = int(artist.reviewCount or 0)
        w_rating = (
            (v / (v + m)) * R + (m / (v + m)) * global_avg
            if (v + m) > 0 else 0.0
        )
        ranked_artists.append((artist.artist_id, w_rating))

    ranked_artists.sort(key=lambda x: x[1], reverse=True)

    # Step 5: Find rank
    rank = next((idx for idx, (a_id, _) in enumerate(ranked_artists, start=1) if str(a_id) == str(user_id)), None)

    return {
        "avgRating": avg_rating,
        "reviewCount": review_count,
        "weightedRating": weighted_rating,  # Optional, can remove if you want old output
        "rank": rank
    }