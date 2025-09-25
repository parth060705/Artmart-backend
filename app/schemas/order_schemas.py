from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

# ENUM TYPES
PaymentStatus = Literal["pending", "paid", "failed"]
PaymentMethodEnum = Literal["credit_card", "debit_card", "net_banking", "upi", "cod"]


# -------------------------------
# ORDER SCHEMAS
# -------------------------------
class UserDetail(BaseModel):
    username: str
    name: str
    location: Optional[str] = None

class ArtworkDetail(BaseModel):
    title: str
    price: float    

class OrderBase(BaseModel):
    artworkId: Optional[UUID]
    totalAmount: float
    paymentStatus: PaymentStatus

class OrderCreate(OrderBase):
    pass

class OrderRead(OrderBase):
    id: UUID
    buyerId: UUID
    createdAt: datetime
    buyer: UserDetail
    artwork: ArtworkDetail

    class Config:
        from_attributes = True

class OrderDelete(BaseModel):
    message: str
    order_id: UUID        
