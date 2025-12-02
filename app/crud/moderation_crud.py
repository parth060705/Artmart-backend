from uuid import uuid4
from app.models.models import ModerationQueue
from sqlalchemy.orm import Session
from datetime import datetime

from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

from app.models.models import (
    Artwork, Comment, Review, ArtistReview,
    ModerationQueue, User
)

# -------------------------------
# MODERATION SCHEMAS
# -------------------------------

class GenericContentCreate(BaseModel):
    # Common fields
    user_id: UUID

    # Artwork fields
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    price: Optional[float] = None

    # Comment fields
    content: Optional[str] = None   # For Comment only

    # Review fields
    artwork_id: Optional[UUID] = None  # For Comment + Review
    comment: Optional[str] = None  # For Review + ArtistReview

    # Artist review fields
    artist_id: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_content_type(self):
        """
        Automatically detect content type based on provided fields.
        """
        title = self.title
        description = self.description
        content = self.content
        comment = self.comment
        artist_id = self.artist_id

        # ---- Artwork ----
        if title or description or self.tags:
            if not title:
                raise ValueError("Artwork requires 'title'.")
            if not description:
                raise ValueError("Artwork requires 'description'.")
            return self

        # ---- Comment ----
        if content:
            if not self.artwork_id:
                raise ValueError("Comment requires artwork_id.")
            return self

        # ---- Review ----
        if comment and self.artwork_id:
            return self

        # ---- Artist Review ----
        if comment and artist_id:
            return self

        raise ValueError("Unable to detect content type. Provide valid fields.")

# -------------------------------

MODEL_CLASS_MAPPING = {
    "artworks": Artwork,
    "comments": Comment,
    "reviews": Review,
    "artist_reviews": ArtistReview
}

def add_to_moderation(db: Session, table_name: str, content_id: str):
    queue_item = ModerationQueue(
        table_name=table_name,
        content_id=content_id,
        created_at=datetime.utcnow(),
        checked=False
    )
    db.add(queue_item)
    db.commit()
    db.refresh(queue_item)
    return queue_item

def create_content_generic(db: Session, data: GenericContentCreate):
    """
    Generic content creation function for all types.
    Automatically detects type and stores only relevant fields.
    """
    content_dict = data.dict(exclude_unset=True)
    user_id = str(data.user_id)

    # Detect content type
    if "title" in content_dict:
        content_type = "artworks"
        allowed_keys = ["title", "description", "tags"]
    elif "content" in content_dict and "artwork_id" in content_dict:
        content_type = "comments"
        allowed_keys = ["content", "artwork_id"]
    elif "content" in content_dict and "artist_id" in content_dict:
        if "artwork_id" in content_dict:
            content_type = "reviews"
            allowed_keys = ["comment", "rating", "artwork_id", "artist_id"]
        else:
            content_type = "artist_reviews"
            allowed_keys = ["comment", "rating", "artist_id"]
    else:
        raise ValueError("Cannot detect content type from fields")

    # Filter fields
    filtered_data = {k: v for k, v in content_dict.items() if k in allowed_keys}

    # Validate user
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise ValueError("User not found")

    # Validate artwork if needed
    artwork_id = filtered_data.get("artwork_id")
    if artwork_id:
        from app.models import Artwork
        artwork = db.query(Artwork).filter_by(id=str(artwork_id)).first()
        if not artwork:
            raise ValueError("Artwork not found")

    # Validate artist if needed
    artist_id = filtered_data.get("artist_id")
    if artist_id:
        artist = db.query(User).filter_by(id=str(artist_id)).first()
        if not artist:
            raise ValueError("Artist not found")

    # Create object
    ModelClass = MODEL_CLASS_MAPPING[content_type]
    new_obj = ModelClass(
        id=str(uuid4()),
        **filtered_data,
        status="pending_moderation"
    )

    # Set user_id / reviewer
    if hasattr(new_obj, "user_id"):
        setattr(new_obj, "user_id", user_id)
    if hasattr(new_obj, "reviewerId"):
        setattr(new_obj, "reviewerId", user_id)
    if hasattr(new_obj, "reviewer_id"):
        setattr(new_obj, "reviewer_id", user_id)

    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)

    # Add to moderation
    add_to_moderation(db, table_name=content_type, content_id=new_obj.id)

    return new_obj

