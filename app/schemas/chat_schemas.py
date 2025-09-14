from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

# ENUM TYPES
MessageType = Literal["message", "typing", "read"]

# -------------------------------
# CHAT SCHEMAS
# -------------------------------

class MessageBase(BaseModel):
    receiver_id: str
    content: Optional[str] = None
    action: Literal["message", "typing", "read"]

    @field_validator("content")
    @classmethod
    def validate_content(cls, v, info):
        # info.data contains all other fields
        action = info.data.get("action")
        if action == "message" and not v:
            raise ValueError("content is required when action is 'message'")
        return v

class MessageCreate(MessageBase):
    message_type: Optional[str] = "text"

class MessageOut(BaseModel):
    sender_id: str
    receiver_id: str
    content: Optional[str] = None
    timestamp: datetime
    is_read: bool = False
    action: Literal["message", "typing", "read"] = "message"
    message_type: str = "text"

    class Config:
        from_attributes = True
