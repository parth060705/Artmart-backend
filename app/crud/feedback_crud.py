from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.models import Feedback
from app.schemas.feedback_schemas import FeedbackCreate, FeedbackUpdate
from app.models.models import FeedbackStatusEnum


def create_feedback(
    db: Session,
    payload: FeedbackCreate,
    user_id: Optional[str] = None,
) -> Feedback:
    feedback = Feedback(
        user_id=user_id,
        type=payload.type,
        message=payload.message,
        page=payload.page,
        feature=payload.feature,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_by_id(
    db: Session,
    feedback_id: str,
) -> Optional[Feedback]:
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()


def list_all_feedback(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    status: Optional[FeedbackStatusEnum] = None,
    type: Optional[str] = None,
    feature: Optional[str] = None,
) -> List[Feedback]:
    query = db.query(Feedback)

    if status:
        query = query.filter(Feedback.status == status)
    if type:
        query = query.filter(Feedback.type == type)
    if feature:
        query = query.filter(Feedback.feature == feature)

    return (
        query
        .order_by(Feedback.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_feedback(
    db: Session,
    feedback: Feedback,
    feedback_in: FeedbackUpdate,
) -> Feedback:
    update_data = feedback_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(feedback, field, value)

    db.commit()
    db.refresh(feedback)
    return feedback
