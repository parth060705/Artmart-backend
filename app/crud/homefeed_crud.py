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

def get_home_feed(db: Session, current_user, limit: int = 20):
    following_ids = [u.id for u in current_user.following]

    # Query artworks from following
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

    # Recommended artworks based on liked tags
    liked_tags = (
        db.query(models.Artwork.tags)
        .join(models.ArtworkLike, models.ArtworkLike.artworkId == models.Artwork.id)
        .filter(models.ArtworkLike.userId == current_user.id)
        .all()
    )

    preferred_tags = set()
    for tags_tuple in liked_tags:
        if isinstance(tags_tuple[0], list):
            preferred_tags.update(tags_tuple[0])
        elif isinstance(tags_tuple[0], str):
            preferred_tags.update([t.strip() for t in tags_tuple[0].split(",") if t.strip()])

    recommended_query = (
        db.query(models.Artwork)
        .options(
            joinedload(models.Artwork.artist),
            joinedload(models.Artwork.likes),
            joinedload(models.Artwork.images)
        )
        .filter(
            models.Artwork.artistId != current_user.id,
            ~models.Artwork.artistId.in_(following_ids)
        )
        .order_by(func.random())
    )

    if preferred_tags:
        tag_conditions = [
            func.json_contains(models.Artwork.tags, f'"{tag}"') for tag in preferred_tags
        ]
        recommended_query = recommended_query.filter(or_(*tag_conditions))

    recommended_artworks = recommended_query.limit(limit).all()

    combined_feed = feed_artworks + recommended_artworks
    combined_feed = combined_feed[:limit]

    # Compute how_many_like and isInCart similar to get_artwork
    cart_artwork_ids = {item.artworkId for item in current_user.cart_items}

    for artwork in combined_feed:
        artwork.how_many_like = likeArt(like_count=len(artwork.likes))
        artwork.isInCart = artwork.id in cart_artwork_ids

    return combined_feed





# import pandas as pd
# import numpy as np
# from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import func
# from implicit.als import AlternatingLeastSquares
# from app.models import models
# from app.schemas.artworks_schemas import likeArt

# # -------------------------
# # TRAIN ALS MODEL
# # -------------------------

# def train_als_model(db: Session):
#     # Get user-artwork interactions from ArtworkLike
#     likes_data = db.query(models.ArtworkLike.userId, models.ArtworkLike.artworkId).all()
#     if not likes_data:
#         return None, None, None

#     df_likes = pd.DataFrame(likes_data, columns=["user_id", "artwork_id"])

#     # Encode user and artwork ids
#     df_likes["user_code"] = df_likes["user_id"].astype("category").cat.codes
#     df_likes["artwork_code"] = df_likes["artwork_id"].astype("category").cat.codes

#     user_map = dict(enumerate(df_likes["user_id"].astype("category").cat.categories))
#     artwork_map = dict(enumerate(df_likes["artwork_id"].astype("category").cat.categories))

#     from scipy.sparse import coo_matrix
#     interaction_matrix = coo_matrix(
#         (np.ones(len(df_likes)), (df_likes["artwork_code"], df_likes["user_code"]))
#     )

#     model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=15)
#     model.fit(interaction_matrix)

#     return model, user_map, artwork_map

# # -------------------------
# # GET ML RECOMMENDATIONS
# # -------------------------

# def get_ml_recommendations(current_user_id, model, user_map, artwork_map, n=20):
#     user_codes = {v: k for k, v in user_map.items()}
#     if current_user_id not in user_codes:
#         return []  # new user with no likes yet

#     user_code = user_codes[current_user_id]
#     recommended = model.recommend(user_code, N=n)

#     recommended_artwork_ids = [artwork_map[artwork_code] for artwork_code, score in recommended]
#     return recommended_artwork_ids

# # -------------------------
# # HOME FEED WITH ML
# # -------------------------

# def get_home_feed_ml(db: Session, current_user, limit: int = 20):
#     following_ids = [u.id for u in current_user.following]

#     # 1️⃣ Feed from followed artists
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

#     # 2️⃣ Train ALS model for ML recommendations
#     model, user_map, artwork_map = train_als_model(db)
#     ml_artworks = []
#     if model:
#         ml_ids = get_ml_recommendations(current_user.id, model, user_map, artwork_map, n=limit)
#         if ml_ids:
#             ml_artworks = (
#                 db.query(models.Artwork)
#                 .options(
#                     joinedload(models.Artwork.artist),
#                     joinedload(models.Artwork.likes),
#                     joinedload(models.Artwork.images)
#                 )
#                 .filter(models.Artwork.id.in_(ml_ids))
#                 .all()
#             )

#     # 3️⃣ Combine feeds and limit
#     combined_feed = feed_artworks + ml_artworks
#     combined_feed = combined_feed[:limit]

#     # 4️⃣ Add like count and cart info
#     cart_artwork_ids = {item.artworkId for item in current_user.cart_items}
#     for artwork in combined_feed:
#         artwork.how_many_like = likeArt(like_count=len(artwork.likes))
#         artwork.isInCart = artwork.id in cart_artwork_ids

#     return combined_feed
