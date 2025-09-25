from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text
from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID
from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import schemas
from passlib.context import CryptContext
import cloudinary.uploader
import cloudinary
from typing import List, Optional, Dict
from fastapi import UploadFile, HTTPException
import cloudinary.uploader
import random, string
import re
from sqlalchemy.exc import SQLAlchemyError
from app.schemas.schemas import (likeArt)
from crud.user_crud import(calculate_completion)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# CART OPERATIONS
# -------------------------

def add_to_cart(db: Session, cart_data: schemas.CartCreate):
    artwork = db.query(models.Artwork).filter(models.Artwork.id == str(cart_data.artworkId)).first()
    if not artwork:
        raise ValueError("Artwork not found")

    if cart_data.purchase_quantity is None:
        cart_data.purchase_quantity = 1

    # Check stock availability
    if artwork.quantity < cart_data.purchase_quantity:
        raise ValueError("Not enough stock available")

    # Check if item already exists in cart
    existing_cart_item = db.query(models.Cart).filter(
        models.Cart.userId == str(cart_data.userId),
        models.Cart.artworkId == str(cart_data.artworkId)
    ).first()

    if existing_cart_item:
        # Update quantity
        new_quantity = existing_cart_item.purchase_quantity + cart_data.purchase_quantity
        if new_quantity > artwork.quantity:
            raise ValueError("Not enough stock available")
        existing_cart_item.purchase_quantity = new_quantity
        db.commit()
        db.refresh(existing_cart_item)
        return existing_cart_item
    else:
        cart_item = models.Cart(
            userId=str(cart_data.userId),
            artworkId=str(cart_data.artworkId),
            purchase_quantity=cart_data.purchase_quantity
        )
        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)
        return cart_item

#--------------------------------------------------------

def get_user_cart(db: Session, user_id: UUID):
    user_id = str(user_id)
    return (
        db.query(models.Cart)
        .options(
            joinedload(models.Cart.artwork).joinedload(models.Artwork.images)
        )
        .filter(models.Cart.userId == user_id)
        .all()
    )

def remove_cart_item(db: Session, user_id: UUID, artwork_id: UUID):
    item = db.query(models.Cart).filter_by(userId=str(user_id), artworkId=str(artwork_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return {"status": "success", "message": "Item removed from cart"}
