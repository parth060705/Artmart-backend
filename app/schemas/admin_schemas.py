from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional

# -------------------------------
# ADMIN SCHEMAS
# -------------------------------

class AdminAuditLogBase(BaseModel):
    method: str
    path: str
    action: str
    description: Optional[str] = None
    ip_address: Optional[str] = None

class AdminAuditLogCreate(AdminAuditLogBase):
    admin_id: str

# Schema for reading a log (response model)
class AdminAuditLogResponse(AdminAuditLogBase):
    id: str
    admin_id: str
    timestamp: datetime

    class Config:
        from_attributes = True