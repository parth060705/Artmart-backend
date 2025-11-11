from fastapi import Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from uuid import UUID
from app.database import get_db
from app.models import models
from app.schemas.artworks_schemas import ArtworkRead
from typing import List, Set
from app.schemas.artworks_schemas import ArtworkRead, ArtworkArtist, ArtworkOnly

def parse_tags(tags) -> set:
    """Safely parse tags (list or comma-separated string) into lowercase set."""
    if not tags:
        return set()
    tag_set = set()
    if isinstance(tags, list):
        for t in tags:
            tag_set.update([tag.strip().lower() for tag in t.split(",") if tag.strip()])
    elif isinstance(tags, str):
        tag_set.update([tag.strip().lower() for tag in tags.split(",") if tag.strip()])
    return tag_set

# RECOMMENDATION BY ARTWORK TAGS AND CATEGORY
def recommend_artworks(db: Session, artwork_id: UUID, limit: int = 10) -> List[ArtworkRead]:
    """
    Recommend artworks based primarily on category and tags.
    Falls back to random artworks if no strong matches are found.
    Returns a list of validated ArtworkRead Pydantic models.
    """
    artwork_id_str = str(artwork_id)

    # 1️⃣ Fetch target artwork
    target = (
        db.query(models.Artwork)
        .options(
            joinedload(models.Artwork.artist),
            joinedload(models.Artwork.likes),
            joinedload(models.Artwork.images),
        )
        .filter(models.Artwork.id == artwork_id_str, models.Artwork.isDeleted == False)
        .first()
    )
    if not target:
        return []

    # 2️⃣ Extract category and tags (ignore missing)
    target_category = target.category.lower() if target.category else None
    target_tags = parse_tags(target.tags)
    target_title_words = set(target.title.lower().split()) if target.title else set()

    # 3️⃣ Fetch all candidate artworks except target
    candidates = (
        db.query(models.Artwork)
        .options(
            joinedload(models.Artwork.artist),
            joinedload(models.Artwork.likes),
            joinedload(models.Artwork.images),
        )
        .filter(models.Artwork.id != artwork_id_str, models.Artwork.isDeleted == False)
        .all()
    )

    # 4️⃣ Score candidates
    scored = {}
    for art in candidates:
        score = 0

        # ✅ Category match — strong weight
        if target_category and art.category and target_category == art.category.lower():
            score += 3

        # ✅ Tag overlap — medium weight
        art_tags = parse_tags(art.tags)
        score += len(target_tags & art_tags) * 2  # each shared tag adds weight

        # ✅ Title word similarity — weak fallback
        if art.title:
            art_words = set(art.title.lower().split())
            score += len(target_title_words & art_words)

        if score > 0:
            scored[art] = score

    # 5️⃣ Sort by descending score
    sorted_artworks = sorted(scored.keys(), key=lambda a: scored[a], reverse=True)

    # 6️⃣ Fallback: random if no matches
    if not sorted_artworks:
        sorted_artworks = (
            db.query(models.Artwork)
            .filter(models.Artwork.id != artwork_id_str, models.Artwork.isDeleted == False)
            .order_by(func.random())
            .limit(limit)
            .all()
        )

    # 7️⃣ Limit results and return as Pydantic models
    top_artworks = sorted_artworks[:limit]
    return [ArtworkRead.model_validate(art, from_attributes=True) for art in top_artworks]

# RECOMMENDATION BY USERS INTERRACTION FOR PERSONALIZED DISCOVER FEED
# def list_recommendations(db: Session, current_user, limit: int = 10) -> List[models.Artwork]:
#     """
#     Return personalized artwork recommendations if user is logged in.
#     Otherwise, return random artworks.
#     """
#     # 🔹 If user not logged in → random artworks
#     if not current_user:
#         return (
#             db.query(models.Artwork)
#             .filter(models.Artwork.isDeleted == False)
#             .order_by(func.random())
#             .limit(limit)
#             .options(joinedload(models.Artwork.artist),
#                      joinedload(models.Artwork.likes),
#                      joinedload(models.Artwork.images))
#             .all()
#         )

#     user_id = str(current_user.id)

#     # 1️⃣ Get user’s interacted artworks (liked, saved, commented)
#     liked_ids = [x.artworkId for x in db.query(models.ArtworkLike.artworkId).filter_by(userId=user_id).all()]
#     saved_ids = [x.artworkId for x in db.query(models.Saved.artworkId).filter_by(userId=user_id).all()]
#     commented_ids = []
#     if hasattr(models, "ArtworkComment"):
#         commented_ids = [x.artworkId for x in db.query(models.ArtworkComment.artworkId).filter_by(userId=user_id).all()]

#     interacted_ids = set(liked_ids + saved_ids + commented_ids)
#     if not interacted_ids:
#         # no interactions yet → random
#         return (
#             db.query(models.Artwork)
#             .filter(models.Artwork.isDeleted == False)
#             .order_by(func.random())
#             .limit(limit)
#             .options(joinedload(models.Artwork.artist),
#                      joinedload(models.Artwork.likes),
#                      joinedload(models.Artwork.images))
#             .all()
#         )

#     # 2️⃣ Extract tags & categories from interacted artworks
#     interacted_artworks = (
#         db.query(models.Artwork)
#         .filter(models.Artwork.id.in_(list(interacted_ids)))
#         .all()
#     )

#     user_tags = set()
#     user_categories = set()
#     for art in interacted_artworks:
#         user_tags |= parse_tags(art.tags)
#         if art.category:
#             user_categories.add(art.category.lower())

#     # 3️⃣ Find matching artworks
#     candidates = (
#         db.query(models.Artwork)
#         .filter(models.Artwork.id.notin_(list(interacted_ids)),
#                 models.Artwork.isDeleted == False)
#         .options(joinedload(models.Artwork.artist),
#                  joinedload(models.Artwork.likes),
#                  joinedload(models.Artwork.images))
#         .all()
#     )

#     scored = {}
#     for art in candidates:
#         score = 0

#         if art.category and art.category.lower() in user_categories:
#             score += 3  # category has higher weight

#         art_tags = parse_tags(art.tags)
#         score += len(user_tags & art_tags) * 2

#         if score > 0:
#             scored[art] = score

#     sorted_artworks = sorted(scored.keys(), key=lambda a: scored[a], reverse=True)

#     if not sorted_artworks:
#         # fallback to random
#         return (
#             db.query(models.Artwork)
#             .filter(models.Artwork.isDeleted == False)
#             .order_by(func.random())
#             .limit(limit)
#             .all()
#         )

#     return sorted_artworks[:limit]

def list_recommendations(db: Session, current_user, limit: int | None = None) -> List[models.Artwork]:
    """
    Personalized recommendations:
      - If user logged in: based on liked/saved/commented artworks (tags + categories)
      - If no user: random artworks
      - If no interactions yet: random artworks
    """
    # 🧑‍🤝‍🧑 Guest user → random artworks
    if not current_user:
        query = (
            db.query(models.Artwork)
            .filter(models.Artwork.isDeleted == False)
            .order_by(func.random())
        )
        if limit:
            query = query.limit(limit)
        return query.options(
            joinedload(models.Artwork.artist),
            joinedload(models.Artwork.likes),
            joinedload(models.Artwork.images)
        ).all()

    user_id = str(current_user.id)

    # 1️⃣ Fetch interacted artworks (liked, saved, commented)
    liked_ids = [x.artworkId for x in db.query(models.ArtworkLike.artworkId).filter_by(userId=user_id).all()]
    saved_ids = [x.artworkId for x in db.query(models.Saved.artworkId).filter_by(userId=user_id).all()]
    commented_ids = []
    if hasattr(models, "ArtworkComment"):
        commented_ids = [x.artworkId for x in db.query(models.ArtworkComment.artworkId).filter_by(userId=user_id).all()]

    interacted_ids = set(liked_ids + saved_ids + commented_ids)

    # 🩶 If user hasn’t interacted → show random
    if not interacted_ids:
        query = (
            db.query(models.Artwork)
            .filter(models.Artwork.isDeleted == False)
            .order_by(func.random())
        )
        if limit:
            query = query.limit(limit)
        return query.options(
            joinedload(models.Artwork.artist),
            joinedload(models.Artwork.likes),
            joinedload(models.Artwork.images)
        ).all()

    # 2️⃣ Extract categories and tags
    interacted_artworks = (
        db.query(models.Artwork)
        .filter(models.Artwork.id.in_(list(interacted_ids)))
        .all()
    )

    user_tags = set()
    user_categories = set()
    for art in interacted_artworks:
        user_tags |= parse_tags(art.tags)
        if art.category:
            user_categories.add(art.category.lower())

    # 3️⃣ Fetch candidate artworks
    candidates = (
        db.query(models.Artwork)
        .filter(models.Artwork.id.notin_(list(interacted_ids)),
                models.Artwork.isDeleted == False)
        .options(
            joinedload(models.Artwork.artist),
            joinedload(models.Artwork.likes),
            joinedload(models.Artwork.images)
        )
        .all()
    )

    # 4️⃣ Score each candidate based on tag/category match
    scored = {}
    for art in candidates:
        score = 0
        if art.category and art.category.lower() in user_categories:
            score += 3
        art_tags = parse_tags(art.tags)
        score += len(user_tags & art_tags) * 2
        if score > 0:
            scored[art] = score

    # 5️⃣ Sort by relevance
    sorted_artworks = sorted(scored.keys(), key=lambda a: scored[a], reverse=True)

    # 6️⃣ Fallback to random if no matches
    if not sorted_artworks:
        query = (
            db.query(models.Artwork)
            .filter(models.Artwork.isDeleted == False)
            .order_by(func.random())
        )
        if limit:
            query = query.limit(limit)
        return query.options(
            joinedload(models.Artwork.artist),
            joinedload(models.Artwork.likes),
            joinedload(models.Artwork.images)
        ).all()

    # ✅ Optional limit if specified
    if limit:
        sorted_artworks = sorted_artworks[:limit]

    return sorted_artworks