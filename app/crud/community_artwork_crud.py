from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import models
from app.schemas.community_artwork_schemas import CommunityArtworkCreate
from datetime import datetime
import uuid
from app.models.models import Community, CommunityArtwork, Artwork, CommunityMember

# -------------------------
# CREATE COMMUNITY ARTWORK
# -------------------------
def create_community_artwork(db: Session, user_id: str, community_id: str, artwork_id: str):
    # 1️⃣ Check community exists
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    # 2️⃣ Check artwork exists and belongs to user
    artwork = db.query(Artwork).filter(
        Artwork.id == artwork_id,
        Artwork.artistId == user_id
    ).first()
    print("USER ID:", user_id)
    print("ARTWORK ID:", artwork_id)
    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found or does not belong to user")

    # 3️⃣ Check if user is a member (or owner)
    if community.type == "private" and user_id != community.owner_id:
        member = db.query(CommunityMember).filter(
            CommunityMember.community_id == community_id,
            CommunityMember.user_id == user_id
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="You are not a member of this private community")

    # 4️⃣ Create community artwork
    community_artwork = CommunityArtwork(
        id=str(uuid.uuid4()),
        community_id=community_id,
        user_id=user_id,
        artwork_id=artwork_id,
        created_at=datetime.utcnow()
    )

    db.add(community_artwork)
    db.commit()
    db.refresh(community_artwork)
    return community_artwork


# -------------------------
# GET COMMUNITY ARTWORKS
# -------------------------
def get_community_artworks(db: Session, community_id: str, user_id: str | None):
    # 1. Get community
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(404, "Community not found")

    # 2. If community is PRIVATE → require login + membership
    if community.type == "private":

        # Not logged in → block
        if not user_id:
            raise HTTPException(
                403,
                "This is a private community. Login and join to view artworks."
            )

        # Logged in but not a member → block
        is_member = db.query(CommunityMember).filter(
            CommunityMember.community_id == community_id,
            CommunityMember.user_id == user_id
        ).first()

        if not is_member:
            raise HTTPException(
                403,
                "This is a private community. Join to view artworks."
            )
    return (
        db.query(CommunityArtwork)
        .filter(CommunityArtwork.community_id == community_id)
        .order_by(CommunityArtwork.created_at.desc())
        .all()
    )


# -------------------------
# GET SINGLE COMMUNITY ARTWORK
# -------------------------
def get_community_artwork(db: Session, artwork_post_id: str):
    artwork_post = db.query(models.CommunityArtwork).filter(models.CommunityArtwork.id == artwork_post_id).first()
    if not artwork_post:
        raise HTTPException(status_code=404, detail="Community artwork post not found")
    return artwork_post


# -------------------------
# DELETE COMMUNITY ARTWORK
# -------------------------
def delete_community_artwork(db: Session, artwork_post_id: str, user_id: str):
    post = db.query(CommunityArtwork).filter(CommunityArtwork.id == artwork_post_id).first()
    if not post:
        raise HTTPException(404, detail="Community artwork not found")

    # Allow deletion if post creator or community owner
    if post.user_id != user_id:
        community = db.query(Community).filter(Community.id == post.community_id).first()
        if not community or community.owner_id != user_id:
            raise HTTPException(403, detail="Not authorized to delete this post")

    db.delete(post)
    db.commit()
    return True