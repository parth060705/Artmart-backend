from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from datetime import datetime
from app.models.models import Community, CommunityJoinRequest, CommunityMember

# Send join request
def send_request(db: Session, community_id: str, user_id: str):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(404, "Community not found")

    if community.type != "private":
        raise HTTPException(400, "Join request allowed only for private communities")

    # Already owner
    if community.owner_id == user_id:
        raise HTTPException(400, "Owner does not need to join their own community")

    # Already member
    already_member = (
        db.query(CommunityMember)
        .filter(CommunityMember.community_id == community_id, CommunityMember.user_id == user_id)
        .first()
    )
    if already_member:
        raise HTTPException(400, "You are already a member of this community")

    # Already requested
    existing_request = (
        db.query(CommunityJoinRequest)
        .filter(
            CommunityJoinRequest.community_id == community_id,
            CommunityJoinRequest.user_id == user_id,
            CommunityJoinRequest.joinstatus == "pending"
        )
        .first()
    )
    if existing_request:
        raise HTTPException(400, "Join request already submitted")

    request = CommunityJoinRequest(
        id=str(uuid.uuid4()),
        community_id=community_id,
        user_id=user_id,
        joinstatus="pending",
        created_at=datetime.utcnow()
    )

    db.add(request)
    db.commit()
    db.refresh(request)
    return request

# Approve a request
def approve(db: Session, request_id: str, owner_id: str):
    req = db.query(CommunityJoinRequest).filter(CommunityJoinRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    community = req.community
    if community.owner_id != owner_id:
        raise HTTPException(403, "Only the owner can approve requests")

    # Add member
    new_member = CommunityMember(
        id=str(uuid.uuid4()),
        community_id=req.community_id,
        user_id=req.user_id,
        joined_at=datetime.utcnow()
    )
    db.add(new_member)

    # Mark request as approved
    req.joinstatus = "approved"
    db.commit()
    return req

# Reject a request
def reject(db: Session, request_id: str, owner_id: str):
    req = db.query(CommunityJoinRequest).filter(CommunityJoinRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")

    community = req.community
    if community.owner_id != owner_id:
        raise HTTPException(403, "Only the owner can reject requests")

    req.joinstatus = "rejected"
    db.commit()
    return req

# Get all pending requests for owner
def get_pending_requests(db: Session, community_id: str, owner_id: str):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(404, "Community not found")

    if community.owner_id != owner_id:
        raise HTTPException(403, "Only owner can view join requests")

    return (
        db.query(CommunityJoinRequest)
        .filter(CommunityJoinRequest.community_id == community_id,
                CommunityJoinRequest.joinstatus == "pending")
        .all()
    )

# Get all rejected requests for owner
def get_rejected_requests(db: Session, community_id: str, owner_id: str):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(404, "Community not found")

    if community.owner_id != owner_id:
        raise HTTPException(403, "Only owner can view join requests")

    return (
        db.query(CommunityJoinRequest)
        .filter(CommunityJoinRequest.community_id == community_id,
                CommunityJoinRequest.joinstatus == "rejected")
        .all()
    )