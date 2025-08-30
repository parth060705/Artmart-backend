from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session  
from typing import List
from app.core.auth import get_current_user
from app.database import get_db
from app.models.models import User
from app.crud import crud
from fastapi import APIRouter, Depends

from app.schemas.schemas import (
    OrderCreate, OrderRead,
)

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# -------------------------
# ORDER ENDPOINTS
# -------------------------

@user_router.post("/orders", response_model=OrderRead)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_order(db, order_data, user_id=current_user.id)

@user_router.get("/orders/my", response_model=List[OrderRead])
def get_my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.list_orders_for_user(db, user_id=current_user.id)
