from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime

# -------------------------
# Action types for chat
# -------------------------
ChatAction = Literal["message", "typing", "read"]

# -------------------------
# Base schema for incoming messages
# -------------------------
class MessageBase(BaseModel):
    receiver_id: str
    content: Optional[str] = None
    action: ChatAction

    @field_validator("content")
    @classmethod
    def validate_content(cls, v, info):
        # content is required only if action is "message"
        action = info.data.get("action")
        if action == "message" and not v:
            raise ValueError("Content is required for 'message' action")
        return v

# -------------------------
# Schema for creating a message
# -------------------------
class MessageCreate(MessageBase):
    message_type: Optional[str] = "text"  # default "text"

# -------------------------
# Schema for returning messages
# -------------------------
class MessageOut(BaseModel):
    sender_id: str
    receiver_id: str
    content: Optional[str] = None
    timestamp: Optional[datetime]
    is_read: bool = False
    action: ChatAction = "message"
    message_type: str = "text"

    class Config:
        from_attributes = True

# -------------------------
# Schema for typing indicator
# -------------------------
class TypingIndicator(BaseModel):
    sender_id: str
    receiver_id: str
    action: Literal["typing"] = "typing"
    is_typing: bool = True

# -------------------------
# Schema for read receipts
# -------------------------
class ReadReceipt(BaseModel):
    sender_id: str
    receiver_id: str
    action: Literal["read"] = "read"
    by_user: str
