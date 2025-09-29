from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text
# from fastapi import HTTPException, UploadFile, File, status
# from uuid import UUID, uuid4
# from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
# from app.schemas import schemas
from passlib.context import CryptContext
# import cloudinary.uploader
# import cloudinary
# from typing import List, Optional, Dict
# from fastapi import UploadFile, HTTPException
# import cloudinary.uploader
# import random, string
# import re
# from sqlalchemy.exc import SQLAlchemyError
from app.schemas.artworks_schemas import (likeArt)
# from crud.user_crud import(calculate_completion)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# HOME FEED OPERATIONS
# -------------------------

# def get_home_feed(db: Session, current_user, limit: int = 20):
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





import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models import models
from app.schemas.artworks_schemas import likeArt

# -------------------------
# Train / Prepare Tag Matrix
# -------------------------

def prepare_tag_matrix(db: Session):
    # Get all artworks and tags
    artworks_data = db.query(models.Artwork.id, models.Artwork.tags).filter(models.Artwork.isDeleted == False).all()
    if not artworks_data:
        return None, None

    df_artworks = pd.DataFrame(artworks_data, columns=["artwork_id", "tags"])
    # Convert tags to comma-separated string
    df_artworks["tags"] = df_artworks["tags"].apply(lambda x: ",".join(x) if isinstance(x, list) else "")

    # TF-IDF vectorization of tags
    tfidf = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    tag_matrix = tfidf.fit_transform(df_artworks["tags"])

    return df_artworks, tag_matrix

# -------------------------
# Get Recommended Artwork IDs
# -------------------------

def get_tag_recommendations(db: Session, current_user, n=20):
    df_artworks, tag_matrix = prepare_tag_matrix(db)
    if df_artworks is None:
        return []

    # Get artworks liked by user
    liked_artworks = [like.artworkId for like in current_user.liked_artworks]
    if not liked_artworks:
        return []  # no likes yet

    # Get indices of liked artworks
    liked_indices = df_artworks[df_artworks["artwork_id"].isin(liked_artworks)].index.tolist()

    # Compute similarity between liked artworks and all artworks
    similarity = cosine_similarity(tag_matrix[liked_indices], tag_matrix)
    # Average similarity across liked artworks
    mean_similarity = similarity.mean(axis=0)

    # Sort and pick top N most similar (excluding already liked artworks)
    df_artworks["score"] = mean_similarity
    recommendations = df_artworks[~df_artworks["artwork_id"].isin(liked_artworks)]
    recommendations = recommendations.sort_values(by="score", ascending=False).head(n)

    return recommendations["artwork_id"].tolist()

# -------------------------
# Home Feed with Content-Based Recommendations
# -------------------------

def get_home_feed(db: Session, current_user, limit: int = 20):
    following_ids = [u.id for u in current_user.following]

    # 1️⃣ Feed from followed artists
    feed_artworks = (
        db.query(models.Artwork)
        .options(
            joinedload(models.Artwork.artist),
            joinedload(models.Artwork.likes),
            joinedload(models.Artwork.images)
        )
        .filter(models.Artwork.artistId.in_(following_ids))
        .order_by(func.random())
        .limit(limit)
        .all()
    )

    # 2️⃣ Content-based recommendations
    rec_ids = get_tag_recommendations(db, current_user, n=limit)
    recommended_artworks = []
    if rec_ids:
        recommended_artworks = (
            db.query(models.Artwork)
            .options(
                joinedload(models.Artwork.artist),
                joinedload(models.Artwork.likes),
                joinedload(models.Artwork.images)
            )
            .filter(models.Artwork.id.in_(rec_ids))
            .all()
        )

    # 3️⃣ Combine feed
    combined_feed = feed_artworks + recommended_artworks
    combined_feed = combined_feed[:limit]

    # 4️⃣ Add like count and cart info
    cart_artwork_ids = {item.artworkId for item in current_user.cart_items}
    for artwork in combined_feed:
        artwork.how_many_like = likeArt(like_count=len(artwork.likes))
        artwork.isInCart = artwork.id in cart_artwork_ids

    return combined_feed
