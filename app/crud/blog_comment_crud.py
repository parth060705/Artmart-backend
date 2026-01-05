from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import models
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import models
from app.schemas.blog_comment_schemas import (
    BlogCommentCreate,
    BlogCommentUpdate
)
from app.crud import moderation_crud


# -----------------------------------------------------
# CREATE COMMENT
# -----------------------------------------------------
def create_comment(db: Session, payload: BlogCommentCreate, user_id: str):

    new_comment = models.BlogComment(
        slug=payload.slug,
        content=payload.content,
        user_id=user_id,
        status="pending_moderation"
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    # Add to moderation queue
    moderation_crud.add_to_moderation(db, table_name="blog_comment", content_id=new_comment.id)

    return new_comment

# -----------------------------------------------------
# GET COMMENT BY SLUG
# -----------------------------------------------------
def get_comments_by_slug(db: Session, slug: str):
    comments = (
        db.query(models.BlogComment)
        .filter(models.BlogComment.slug == slug)
        .order_by(models.BlogComment.created_at.asc())
        .all()
    )

    if not comments:
        raise HTTPException(status_code=404, detail="No comments found")

    return comments


# -----------------------------------------------------
# UPDATE COMMENT
# -----------------------------------------------------
def update_comment(db: Session, comment_id: str, payload: BlogCommentUpdate, user_id: str):
    # Fetch the specific comment
    comment = db.query(models.BlogComment).filter(
        models.BlogComment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Ensure only the authorized can update
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to update this comment")

    # Apply updates
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(comment, key, value)

    db.commit()
    db.refresh(comment)

    return comment

# -----------------------------------------------------
# DELETE COMMENT
# -----------------------------------------------------
def delete_comment(db: Session, comment_id: str, user_id: str):
    comment = db.query(models.BlogComment).filter(
        models.BlogComment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Only the authorized can delete
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this comment")

    db.delete(comment)
    db.commit()

    return {"message": "Comment deleted successfully"}


