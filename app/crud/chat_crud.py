from sqlalchemy.orm import Session

# FOR MESSAGING
from app.models.models import Message
from app.schemas.chat_schemas import MessageCreate
from datetime import datetime

# -------------------------
# MESSAGING OPERATIONS
# -------------------------

def create_message(db: Session, sender_id: str, msg: MessageCreate) -> Message:
    message = Message(
        sender_id=sender_id,
        receiver_id=msg.receiver_id,
        content=msg.content,
        timestamp=datetime.utcnow(),
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
        ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
        ((Message.sender_id == user2_id) & (Message.receiver_id == user1_id))
    ).order_by(Message.timestamp.desc()).limit(limit).all()
