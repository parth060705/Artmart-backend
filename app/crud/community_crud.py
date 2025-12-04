# community_crud.py
from sqlalchemy.orm import Session
from app.models.models import Community, CommunityMember
from app.schemas.community_schemas import (
    CommunityCreate,
    CommunityUpdate
)
import uuid
from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
import uuid
import cloudinary.uploader

# -----------------------------
# CREATE COMMUNITY
# -----------------------------

# Your existing constants
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/pjpeg",
    "image/png",
    "image/svg+xml",
    "image/webp"
}

MAX_FILE_SIZE_MB = 20

def create_community(
    db: Session,
    owner_id: str,
    data: CommunityCreate,
    banner_file: UploadFile = None
):
    banner_url = None
    banner_public_id = None

    # 1️⃣ Handle Banner Upload (optional)
    if banner_file:
        # MIME validation
        if banner_file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {banner_file.content_type}"
            )

        # Size validation
        contents = banner_file.file.read()
        if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)"
            )
        banner_file.file.seek(0)

        # Cloudinary upload
        try:
            upload_result = cloudinary.uploader.upload(
                banner_file.file,
                folder="community_banners"
            )
            banner_url = upload_result.get("secure_url")
            banner_public_id = upload_result.get("public_id")

            if not banner_url or not banner_public_id:
                raise HTTPException(
                    status_code=500,
                    detail="Cloudinary upload failed"
                )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cloudinary upload error: {str(e)}"
            )

    try:
        # 2️⃣ Create community record
        new_community = Community(
            id=str(uuid.uuid4()),
            name=data.name,
            description=data.description,
            bannerImage=banner_url,
            owner_id=owner_id,
        )
        db.add(new_community)
        db.flush()

        # 3️⃣ Add owner as a member
        owner_member = CommunityMember(
            id=str(uuid.uuid4()),
            community_id=new_community.id,
            user_id=owner_id
        )
        db.add(owner_member)

        db.commit()
        db.refresh(new_community)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    # Optionally save Cloudinary public_id if your model has this column
    if banner_public_id and hasattr(Community, "bannerImagePublicId"):
        new_community.bannerImagePublicId = banner_public_id
        db.commit()
        db.refresh(new_community)

    return new_community

# -----------------------------
# GET COMMUNITY BY ID
# -----------------------------
def get_community(db: Session, community_id: str):
    return db.query(Community).filter(Community.id == community_id).first()


# -----------------------------
# GET ALL COMMUNITIES
# -----------------------------
def get_communities(db: Session, skip: int = 0, limit: int = 50):
    return db.query(Community).offset(skip).limit(limit).all()


# -----------------------------
# UPDATE COMMUNITY
# -----------------------------
def update_community(
    db: Session,
    community_id: str,
    data: CommunityUpdate,
    banner_file: UploadFile = None
):
    community = get_community(db, community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    banner_url = community.bannerImage
    banner_public_id = getattr(community, "bannerImagePublicId", None)

    # -----------------------------------
    # 1️⃣ Handle banner update (optional)
    # -----------------------------------
    if banner_file:
        # Validate MIME
        if banner_file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {banner_file.content_type}"
            )

        # Validate size
        contents = banner_file.file.read()
        if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)"
            )
        banner_file.file.seek(0)

        # Delete old banner from Cloudinary (if exists)
        if banner_public_id:
            try:
                cloudinary.uploader.destroy(banner_public_id)
            except Exception:
                pass  # don't block request on Cloudinary cleanup failure

        # Upload new banner
        try:
            upload_result = cloudinary.uploader.upload(
                banner_file.file,
                folder="community_banners"
            )
            banner_url = upload_result.get("secure_url")
            banner_public_id = upload_result.get("public_id")

            if not banner_url or not banner_public_id:
                raise HTTPException(status_code=500, detail="Cloudinary upload failed")

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cloudinary upload error: {str(e)}"
            )

    try:
        # -----------------------------------
        # 2️⃣ Update fields from CommunityUpdate
        # -----------------------------------
        update_fields = data.dict(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(community, field, value)

        # -----------------------------------
        # 3️⃣ Update banner fields (if changed)
        # -----------------------------------
        if banner_file:
            community.bannerImage = banner_url

            if hasattr(community, "bannerImagePublicId"):
                community.bannerImagePublicId = banner_public_id

        db.commit()
        db.refresh(community)

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return community



# -----------------------------
# DELETE COMMUNITY
# -----------------------------
def delete_community(db: Session, community_id: str):
    community = get_community(db, community_id)
    if not community:
        return None

    db.delete(community)
    db.commit()
    return True
