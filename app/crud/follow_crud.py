from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import or_ , and_, func, text
# from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID, uuid4
# from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
# from app.schemas import follow_schemas
from passlib.context import CryptContext
# import cloudinary.uploader
# import cloudinary
# from typing import List, Optional, Dict
# from fastapi import UploadFile, HTTPException
# import cloudinary.uploader
# import random, string
# import re
# from sqlalchemy.exc import SQLAlchemyError
# from app.schemas.schemas import (likeArt)
# from app.crud.user_crud import(calculate_completion)
from app.util import util


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# FOLLOW OPERATIONS
# -------------------------

def serialize_user(user: models.User):
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "profileImage": user.profileImage,
    }

# def follow_user(db: Session, follower_id: str, followed_id: str):
#     if follower_id == followed_id:
#         raise ValueError("User cannot follow themselves.")

#     follower = db.get(models.User, follower_id)
#     followed = db.get(models.User, followed_id)

#     if not follower or not followed:
#         raise ValueError("User not found.")

#     if follower.is_following(followed):
#         return {"status": "already_following"}

#     follower.follow(followed)
#     db.commit()
#     return {"status": "followed"}

def follow_user(db: Session, follower_id: str, followed_id: str):
    if follower_id == followed_id:
        raise ValueError("User cannot follow themselves.")

    follower = db.get(models.User, follower_id)
    followed = db.get(models.User, followed_id)

    if not follower or not followed:
        raise ValueError("User not found.")

    if follower.is_following(followed):
        return {"status": "already_following", "profile_completion": follower.profile_completion}

    try:
        # Add follow relationship
        follower.follow(followed)
        db.commit()
        db.refresh(follower)

        # Recalculate profile completion after follow
        follower.profile_completion = util.calculate_completion(follower, db)
        db.commit()
        db.refresh(follower)

    except Exception as e:
        db.rollback()
        raise e

    return {
        "status": "followed",
        "profile_completion": follower.profile_completion
    }

def unfollow_user(db: Session, follower_id: str, followed_id: str):
    follower = db.get(models.User, follower_id)
    followed = db.get(models.User, followed_id)

    if not follower or not followed:
        raise ValueError("User not found.")

    if not follower.is_following(followed):
        return {"status": "not_following"}

    follower.unfollow(followed)
    db.commit()
    return {"status": "unfollowed"}


def get_followers(db: Session, user_id: str):
    user = db.get(models.User, user_id)
    if not user:
        raise ValueError("User not found.")
    return user.followers


def get_following(db: Session, user_id: str):
    user = db.get(models.User, user_id)
    if not user:
        raise ValueError("User not found.")
    return user.following

def is_user_following(db: Session, follower_id: str, following_id: str) -> bool:
    follower = db.query(models.User).filter(models.User.id == follower_id).first()
    following = db.query(models.User).filter(models.User.id == following_id).first()

    if not follower or not following:
        return False

    return following in follower.following

# def is_user_following(db: Session, follower_id: str, following_id: str) -> bool:
#     return db.query(models.Follow).filter(
#         models.Follow.follower_id == str(follower_id),
#         models.Follow.following_id == str(following_id)
#     ).first() is not None

