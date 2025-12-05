import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models import models


def get_member(db: Session, community_id: str, user_id: str):
    return (
        db.query(models.CommunityMember)
        .filter(
            models.CommunityMember.community_id == community_id,
            models.CommunityMember.user_id == user_id
        )
        .first()
    )


def add_member(db: Session, community_id: str, user_id: str):
    # Check community exists
    community = db.query(models.Community).filter(models.Community.id == community_id).first()
    if not community:
        raise HTTPException(404, "Community not found")
    
    # Check privacy
    if community.type == models.CommunityType.private:
        raise HTTPException(403, "Cannot join a private community directly")

    # Prevent adding owner as a member
    if community.owner_id == user_id:
        raise HTTPException(400, "Owner is already a member")

    # Prevent adding owner as a duplicate member
    if community.owner_id == user_id:
        raise HTTPException(400, "Owner is already a member")

    # Prevent duplicate join
    existing = get_member(db, community_id, user_id)
    if existing:
        raise HTTPException(400, "User already a community member")

    new_member = models.CommunityMember(
        id=str(uuid.uuid4()),
        community_id=community_id,
        user_id=user_id,
        joined_at=datetime.utcnow()
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member

def remove_member(db: Session, community_id: str, user_id: str):
    member = get_member(db, community_id, user_id)
    if not member:
        raise HTTPException(404, "Member not found")

    db.delete(member)
    db.commit()
    return True

def remove_member_by_owner(db: Session, community_id: str, user_id: str):
    # 1️⃣ Fetch member
    member = db.query(models.CommunityMember).filter(
        models.CommunityMember.community_id == community_id,
        models.CommunityMember.user_id == user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # 2️⃣ Optional: Prevent removing the owner
    community = db.query(models.Community).filter(models.Community.id == community_id).first()
    if community.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the owner of the community")

    # 3️⃣ Delete member
    db.delete(member)
    db.commit()

    return True

def list_members(db: Session, community_id: str):
    return (
        db.query(models.CommunityMember)
        .filter(models.CommunityMember.community_id == community_id)
        .all()
    )
