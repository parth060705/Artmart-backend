from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from uuid import UUID
from typing import List
from app.models import models
from app.schemas.artworks_schemas import ArtworkRead


def get_recommendation(db: Session, artwork_id: UUID, limit: int = 10) -> List[ArtworkRead]:
    """
    Recommend artworks based on a target artwork's title, category, and tags.
    Returns top 'limit' artworks excluding the target itself.
    If no matches, returns random artworks.
    """
    artwork_id_str = str(artwork_id)

    # 1️⃣ Fetch the target artwork
    target = db.query(models.Artwork)\
        .options(joinedload(models.Artwork.artist),
                 joinedload(models.Artwork.likes),
                 joinedload(models.Artwork.images))\
        .filter(models.Artwork.id == artwork_id_str,
                models.Artwork.isDeleted == False)\
        .first()

    if not target:
        return []

    # 2️⃣ Prepare target fields
    target_title_words = set(target.title.lower().split()) if target.title else set()
    target_category = target.category.lower() if target.category else None

    target_tags = set()
    if target.tags:
        if isinstance(target.tags, list):
            for t in target.tags:
                target_tags.update([tag.strip().lower() for tag in t.split(",") if tag.strip()])
        elif isinstance(target.tags, str):
            target_tags.update([tag.strip().lower() for tag in target.tags.split(",") if tag.strip()])

    # 3️⃣ Fetch all candidate artworks (excluding target)
    candidates = db.query(models.Artwork)\
        .options(joinedload(models.Artwork.artist),
                 joinedload(models.Artwork.likes),
                 joinedload(models.Artwork.images))\
        .filter(models.Artwork.id != artwork_id_str,
                models.Artwork.isDeleted == False)\
        .all()

    # 4️⃣ Score each candidate
    scored = {}
    for art in candidates:
        score = 0

        # Title words match: +1 per matching word
        if art.title:
            art_words = set(art.title.lower().split())
            score += len(target_title_words & art_words)

        # Category match: +2
        if target_category and art.category and target_category == art.category.lower():
            score += 2

        # Tags match: +1 per matching tag
        art_tags = set()
        if art.tags:
            if isinstance(art.tags, list):
                for t in art.tags:
                    art_tags.update([tag.strip().lower() for tag in t.split(",") if tag.strip()])
            elif isinstance(art.tags, str):
                art_tags.update([tag.strip().lower() for tag in art.tags.split(",") if tag.strip()])
        score += len(target_tags & art_tags)

        if score > 0:
            scored[art] = score

    # 5️⃣ Sort by score descending
    sorted_artworks = sorted(scored.keys(), key=lambda a: scored[a], reverse=True)

    # 6️⃣ If no scored artworks, fallback to random artworks
    if not sorted_artworks:
        sorted_artworks = db.query(models.Artwork)\
            .filter(models.Artwork.id != artwork_id_str,
                    models.Artwork.isDeleted == False)\
            .order_by(func.random())\
            .limit(limit)\
            .all()

    # 7️⃣ Limit to requested number
    top_artworks = sorted_artworks[:limit]

    # 8️⃣ Convert to Pydantic models
    return [ArtworkRead.model_validate(art) for art in top_artworks]
