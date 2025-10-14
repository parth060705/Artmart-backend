from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text
from app.models import models
from app.models.models import RoleEnum
from passlib.context import CryptContext
from app.schemas.artworks_schemas import (likeArt)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# HOME FEED OPERATIONS
# -------------------------

# def get_home_feed(db: Session, current_user, limit: int = 10):
#     following_ids = [u.id for u in current_user.following]

#     # Query artworks from following
#     feed_artworks = (
#         db.query(models.Artwork)
#         .options(
#             joinedload(models.Artwork.artist),
#             joinedload(models.Artwork.likes),
#             joinedload(models.Artwork.images)
#         )
#         .filter(models.Artwork.artistId.in_(following_ids))
#         .order_by(func.random())
#         .limit(limit)
#         .all()
#     )

#     # Recommended artworks based on liked tags
#     liked_tags = (
#         db.query(models.Artwork.tags)
#         .join(models.ArtworkLike, models.ArtworkLike.artworkId == models.Artwork.id)
#         .filter(models.ArtworkLike.userId == current_user.id)
#         .all()
#     )

#     preferred_tags = set()
#     for tags_tuple in liked_tags:
#         if isinstance(tags_tuple[0], list):
#             preferred_tags.update(tags_tuple[0])
#         elif isinstance(tags_tuple[0], str):
#             preferred_tags.update([t.strip() for t in tags_tuple[0].split(",") if t.strip()])

#     recommended_query = (
#         db.query(models.Artwork)
#         .options(
#             joinedload(models.Artwork.artist),
#             joinedload(models.Artwork.likes),
#             joinedload(models.Artwork.images)
#         )
#         .filter(
#             models.Artwork.artistId != current_user.id,
#             ~models.Artwork.artistId.in_(following_ids)
#         )
#         .order_by(func.random())
#     )

#     if preferred_tags:
#         tag_conditions = [
#             func.json_contains(models.Artwork.tags, f'"{tag}"') for tag in preferred_tags
#         ]
#         recommended_query = recommended_query.filter(or_(*tag_conditions))

#     recommended_artworks = recommended_query.limit(limit).all()

#     combined_feed = feed_artworks + recommended_artworks
#     combined_feed = combined_feed[:limit]

#     # Compute how_many_like and isInCart similar to get_artwork
#     cart_artwork_ids = {item.artworkId for item in current_user.cart_items}

#     for artwork in combined_feed:
#         artwork.how_many_like = likeArt(like_count=len(artwork.likes))
#         artwork.isInCart = artwork.id in cart_artwork_ids

#     return combined_feed


#*****************************************************************************





import pandas as pd
import numpy as np
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models import models
from app.schemas.artworks_schemas import likeArt


# --------------------------------------------------------
# 1️⃣ Load artworks and prepare tag matrix
# --------------------------------------------------------
def get_artworks_and_tags(db: Session):
    """
    Load all artworks and create a simple normalized tag matrix.
    """
    artworks = (
        db.query(models.Artwork.id, models.Artwork.tags)
        .filter(models.Artwork.isDeleted == False)
        .all()
    )
    if not artworks:
        return None, None

    df = pd.DataFrame(artworks, columns=["artwork_id", "tags"])
    df["tags"] = df["tags"].apply(lambda x: ",".join(x) if isinstance(x, list) else (x or ""))

    # Split tags and build vocabulary
    tags_split = df["tags"].apply(lambda x: [t.strip().lower() for t in x.split(",") if t])
    vocab = sorted({t for tags in tags_split for t in tags})
    vocab_index = {t: i for i, t in enumerate(vocab)}

    # Build simple term frequency matrix
    matrix = np.zeros((len(df), len(vocab)))
    for i, tags in enumerate(tags_split):
        for tag in tags:
            matrix[i, vocab_index[tag]] += 1

    # Normalize (to make it act like cosine similarity)
    row_sums = np.linalg.norm(matrix, axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    matrix = matrix / row_sums

    return df, matrix


# --------------------------------------------------------
# 2️⃣ Recommend artworks based on tag similarity
# --------------------------------------------------------
def recommend_artworks(db: Session, current_user, limit: int = 10):
    """
    Recommend artworks similar to those the user liked.
    """
    df, matrix = get_artworks_and_tags(db)
    if df is None:
        return []

    liked_ids = [like.artworkId for like in current_user.liked_artworks]
    if not liked_ids:
        return []

    liked_idx = df[df["artwork_id"].isin(liked_ids)].index.tolist()
    if not liked_idx:
        return []

    liked_matrix = matrix[liked_idx]
    sim = liked_matrix @ matrix.T  # cosine similarity
    avg_sim = sim.mean(axis=0)

    df["score"] = avg_sim
    recs = df[~df["artwork_id"].isin(liked_ids)].sort_values(by="score", ascending=False).head(limit)
    return recs["artwork_id"].tolist()


# --------------------------------------------------------
# 3️⃣ Build personalized home feed (no cart)
# --------------------------------------------------------
def get_home_feed(db: Session, current_user):
    """
    Combine followed artists' artworks + tag-based recommendations + random fallback.
    """
    LIMIT_FOLLOWING = 6
    LIMIT_TAGS = 4
    TOTAL_FEED = 10

    # 1️⃣ Artworks from followed artists
    following_ids = [u.id for u in current_user.following]
    following_artworks = (
        db.query(models.Artwork)
        .options(joinedload(models.Artwork.artist),
                 joinedload(models.Artwork.likes),
                 joinedload(models.Artwork.images))
        .filter(models.Artwork.artistId.in_(following_ids),
                models.Artwork.artistId != current_user.id)
        .order_by(func.random())
        .limit(LIMIT_FOLLOWING)
        .all()
    )

    seen_ids = {a.id for a in following_artworks}

    # 2️⃣ Tag-based recommendations
    rec_ids = recommend_artworks(db, current_user, limit=LIMIT_TAGS * 2)
    rec_artworks = []
    if rec_ids:
        rec_artworks = (
            db.query(models.Artwork)
            .options(joinedload(models.Artwork.artist),
                     joinedload(models.Artwork.likes),
                     joinedload(models.Artwork.images))
            .filter(models.Artwork.id.in_(rec_ids),
                    models.Artwork.artistId != current_user.id,
                    ~models.Artwork.id.in_(seen_ids))
            .limit(LIMIT_TAGS)
            .all()
        )

    # 3️⃣ Combine both lists
    feed = following_artworks + rec_artworks
    seen_ids.update({a.id for a in feed})

    # 4️⃣ Fill remaining with random artworks if needed
    remaining = TOTAL_FEED - len(feed)
    if remaining > 0:
        extra_artworks = (
            db.query(models.Artwork)
            .options(joinedload(models.Artwork.artist),
                     joinedload(models.Artwork.likes),
                     joinedload(models.Artwork.images))
            .filter(models.Artwork.artistId != current_user.id,
                    ~models.Artwork.id.in_(seen_ids))
            .order_by(func.random())
            .limit(remaining)
            .all()
        )
        feed += extra_artworks

    # 5️⃣ Add like count (only)
    for art in feed:
        art.how_many_like = likeArt(like_count=len(art.likes))

    return feed