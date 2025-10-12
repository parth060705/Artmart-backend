from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.models import Message
from app.schemas.chat_schemas import MessageCreate
from datetime import datetime
from sqlalchemy import func, or_, desc, and_
from app.models.models import Message, User



# -------------------------
# CHAT HELPERS
# -------------------------

def create_message(db: Session, sender_id: str, msg: MessageCreate) -> Message:
    if isinstance(msg.timestamp, str):
        timestamp = datetime.fromisoformat(msg.timestamp)
    else:
        timestamp = msg.timestamp or datetime.utcnow()  # fallback if not provided

    message = Message(
        sender_id=sender_id,
        receiver_id=msg.receiver_id,
        content=msg.content,
        timestamp=timestamp,
        message_type="text",
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def mark_messages_as_read(db: Session, sender_id: str, receiver_id: str):
    db.query(Message).filter(
        Message.sender_id == sender_id,
        Message.receiver_id == receiver_id,
        Message.is_read == False
    ).update({Message.is_read: True})
    db.commit()

def get_unread_count(db: Session, receiver_id: str, sender_id: str) -> int:
    return db.query(Message).filter(
        Message.sender_id == sender_id,
        Message.receiver_id == receiver_id,
        Message.is_read == False
    ).count()

def get_messages_between(db: Session, user1_id: str, user2_id: str, limit: int = 50):
    return db.query(Message).filter(
        or_(
            and_(Message.sender_id == user1_id, Message.receiver_id == user2_id),
            and_(Message.sender_id == user2_id, Message.receiver_id == user1_id)
        )
    ).order_by(Message.timestamp.desc()).limit(limit).all()

# -------------------------
# CHAT LIST ENDPOINT
# ------------------------

def get_chat_users(db: Session, current_user_id: str):
    """
    Return a list of users the current user has chatted with,
    including last message, timestamp, and unread count.
    """

    # Subquery: get latest timestamp per conversation pair
    last_messages = (
        db.query(
            func.greatest(Message.sender_id, Message.receiver_id).label("user_a"),
            func.least(Message.sender_id, Message.receiver_id).label("user_b"),
            func.max(Message.timestamp).label("last_time")
        )
        .filter(
            or_(
                Message.sender_id == current_user_id,
                Message.receiver_id == current_user_id
            )
        )
        .group_by("user_a", "user_b")
        .subquery()
    )

    # Join with message table to fetch latest message data
    latest_msgs = (
        db.query(Message)
        .join(
            last_messages,
            and_(
                func.greatest(Message.sender_id, Message.receiver_id) == last_messages.c.user_a,
                func.least(Message.sender_id, Message.receiver_id) == last_messages.c.user_b,
                Message.timestamp == last_messages.c.last_time
            )
        )
        .order_by(desc(Message.timestamp))
        .all()
    )

    chat_list = []
    for msg in latest_msgs:
        # Determine chat partner
        partner = msg.receiver if msg.sender_id == current_user_id else msg.sender

        # Count unread messages from partner → current user
        unread_count = (
            db.query(func.count(Message.id))
            .filter(
                Message.sender_id == partner.id,
                Message.receiver_id == current_user_id,
                Message.is_read == False
            )
            .scalar()
        )

        chat_list.append({
            "user_id": str(partner.id),
            "username": partner.username,
            "name": partner.name,
            "profileImage": partner.profileImage,
            "lastMessage": msg.content,
            "lastMessageType": msg.message_type,
            "lastMessageAt": msg.timestamp,
            "unreadCount": unread_count,
        })

    return chat_list
