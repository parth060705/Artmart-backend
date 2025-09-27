from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import or_ , and_, func, text
# from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID, uuid4
# from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import order_schemas
from passlib.context import CryptContext
# import cloudinary.uploader
# import cloudinary
# from typing import List, Optional, Dict
# from fastapi import UploadFile, HTTPException
# import cloudinary.uploader
# import random, string
# import re
from sqlalchemy.exc import SQLAlchemyError
# from app.schemas.likes_schemas import (likeArt)
# from crud.user_crud import(calculate_completion)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#--------------------------
# ORDER OPERATIONS
# -------------------------

def create_order(db: Session, order_data: order_schemas.OrderCreate, user_id: UUID):
    db_order = models.Order(
        artworkId=str(order_data.artworkId),
        totalAmount=order_data.totalAmount,
        paymentStatus=order_data.paymentStatus,
        buyerId=str(user_id)
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_order(db: Session, order_id: UUID):
    order_id = str(order_id)
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def list_orders_for_user(db: Session, user_id: UUID):
    user_id = str(user_id)
    return db.query(models.Order).filter(models.Order.buyerId == user_id).all()