from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text, desc
from fastapi import HTTPException, UploadFile, File, status
from uuid import UUID, uuid4
# from uuid import uuid4
from app.models import models
from app.models.models import RoleEnum
from app.schemas import user_schema
from passlib.context import CryptContext
import cloudinary.uploader
import cloudinary
# from typing import List, Optional, Dict
from fastapi import UploadFile, HTTPException
import cloudinary.uploader
import random, string
import re
# from sqlalchemy.exc import SQLAlchemyError
# from app.schemas.likes_schemas import (likeArt) 
from datetime import datetime, timedelta
import random
from app.models.models import User
from typing import Optional
from sqlalchemy import func, desc
from decimal import Decimal
from app.util import util, util_artistrank
from app.crud import follow_crud

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------
# USER OPERATIONS
# -------------------------

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# def get_user(db: Session, user_id: str, current_user=None):
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         return None

#     rating_info = util_artistrank.get_user_rating_info(db, str(user.id))

#     # Determine if current_user has reviewed this user
#     is_reviewed = False
#     if current_user:
#         review_exists = db.query(models.ArtistReview).filter(
#             models.ArtistReview.artist_id == str(user_id),
#             models.ArtistReview.reviewer_id == str(current_user.id)
#         ).first()
#         is_reviewed = review_exists is not None

#     return {
#         "id": str(user.id),
#         "name": user.name,
#         "username": user.username,
#         "profileImage": user.profileImage,
#         "gender": user.gender,
#         "age": user.age,
#         "bio": user.bio,
#         "createdAt": user.createdAt,
#         "avgRating": rating_info["avgRating"],
#         "weightedRating": rating_info["weightedRating"],
#         "reviewCount": rating_info["reviewCount"],
#         "rank": rating_info["rank"],
#         "is_reviewed": is_reviewed
#     }

def get_user(db: Session, user_id: str, current_user=None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    rating_info = util_artistrank.get_user_rating_info(db, str(user.id))

    # Determine if current_user has reviewed this user
    is_reviewed = False
    if current_user:
        review_exists = db.query(models.ArtistReview).filter(
            models.ArtistReview.artist_id == str(user_id),
            models.ArtistReview.reviewer_id == str(current_user.id)
        ).first()
        is_reviewed = review_exists is not None

    # Followers & Following
    followers = follow_crud.get_followers(db, user.id)
    following = follow_crud.get_following(db, user.id)

    followers_data = {
        "users": [follow_crud.serialize_user(u) for u in followers],
        "count": len(followers)
    }

    following_data = {
        "users": [follow_crud.serialize_user(u) for u in following],
        "count": len(following)
    }
    
    return {
        "id": str(user.id),
        "name": user.name,
        "username": user.username,
        "profileImage": user.profileImage,
        "gender": user.gender,
        "age": user.age,
        "bio": user.bio,
        "createdAt": user.createdAt,
        "avgRating": rating_info["avgRating"],
        "weightedRating": rating_info["weightedRating"],
        "reviewCount": rating_info["reviewCount"],
        "rank": rating_info["rank"],
        "is_reviewed": is_reviewed,
        "followers": followers_data,
        "following": following_data
    }


# def get_user_with_rating(db: Session, user_id: UUID):
#     """
#     Return user info including optional avgRating, reviewCount, and rank among all artists.
#     """

#     # Subquery: compute avgRating, reviewCount, and rank for all artists
#     ranked_artists = (
#         db.query(
#             models.User.id.label("artist_id"),
#             func.coalesce(func.avg(models.ArtistReview.rating), 0).label("avgRating"),
#             func.count(models.ArtistReview.id).label("reviewCount"),
#             func.rank()
#             .over(order_by=desc(func.coalesce(func.avg(models.ArtistReview.rating), 0)))
#             .label("rank")
#         )
#         .outerjoin(models.ArtistReview, models.User.id == models.ArtistReview.artist_id)
#         .group_by(models.User.id)
#         .subquery()
#     )

#     # Fetch the requested user's ranking info
#     result = db.query(ranked_artists).filter(ranked_artists.c.artist_id == str(user_id)).first()

#     # Fetch the basic user info
#     user = db.query(models.User).filter(models.User.id == str(user_id)).first()
#     if not user:
#         return None

#     user_dict = user.__dict__.copy()
#     user_dict["avgRating"] = float(result.avgRating) if result and result.avgRating is not None else None
#     user_dict["reviewCount"] = int(result.reviewCount) if result and result.reviewCount is not None else None
#     user_dict["rank"] = int(result.rank) if result and result.rank is not None else None

#     return user_dict


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

# Create User (progressive registration)
def create_user(db: Session, user: user_schema.UserCreate):
    hashed_password = pwd_context.hash(user.password)

    db_user = models.User(
        name=user.name,
        email=user.email,
        username=user.username,
        passwordHash=hashed_password,
        profileImage=str(user.profileImage) if user.profileImage else None,
        location=user.location,
        gender=user.gender,
        bio=user.bio,
        age=user.age,
        phone=str(user.phone) if user.phone else None,
        pincode=str(user.pincode) if user.pincode else None,
        isAgreedtoTC=user.isAgreedtoTC,
    )

    # calculate completion
    db_user.profile_completion = util.calculate_completion(db_user, db)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Update User (progressive registration)
def update_user_details(db: Session, user_id: int, user_update: user_schema.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")

    # Update only provided fields
    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.location is not None:
        db_user.location = user_update.location
    if user_update.gender is not None:
        db_user.gender = user_update.gender
    if user_update.age is not None:
        db_user.age = user_update.age
    if user_update.bio is not None:
        db_user.bio = user_update.bio
    if user_update.pincode is not None:
        db_user.pincode = str(user_update.pincode)
    if user_update.phone is not None:
        db_user.phone = str(user_update.phone)

    # Recalculate completion
    db_user.profile_completion = util.calculate_completion(db_user, db)

    db.commit()
    db.refresh(db_user)
    return db_user

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/svg+xml"}
def upload_image_to_cloudinary(file: UploadFile):
    print("[DEBUG] File type:", file.content_type)
    print("[DEBUG] Cloudinary API key:", cloudinary.config().api_key)
    print("[DEBUG] Cloudinary Cloud name:", cloudinary.config().cloud_name)

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Validate file size (max 5MB)
    contents = file.file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    file.file.seek(0)

    # Upload to Cloudinary
    try:
        result = cloudinary.uploader.upload(file.file, folder="user_profiles")
        print("[DEBUG] Upload result:", result)
    except Exception as e:
        print("[ERROR] Cloudinary upload failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

    return {
        "message": "Image uploaded successfully",
        "url": result["secure_url"]
    }

#################### FOR REPLACING PROFILE PHOTOS FROM CLOUDINARY AFTER UPDATING
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "svg"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/svg+xml"}

def update_user_profile_image(db: Session, user_id: UUID, file: UploadFile):
    print("[DEBUG] User ID:", user_id)
    print("[DEBUG] File type:", file.content_type)
    print("[DEBUG] Cloudinary API key:", cloudinary.config().api_key)  
    print("[DEBUG] Cloudinary Cloud name:", cloudinary.config().cloud_name)

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = file.file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    file.file.seek(0)

    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete previous image if present
    if user.profileImagePublicId:
        try:
            deletion_result = cloudinary.uploader.destroy(user.profileImagePublicId)
            print("[DEBUG] Deleted old image:", deletion_result)
        except Exception as e:
            print("[ERROR] Could not delete old image:", str(e))

    # Upload new image
    try:
        result = cloudinary.uploader.upload(file.file, folder="user_profiles")
        print("[DEBUG] Upload result:", result)
    except Exception as e:
        print("[ERROR] Cloudinary upload failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Cloudinary error: {str(e)}")

    # Save new image URL and public_id
    user.profileImage = result["secure_url"]
    user.profileImagePublicId = result["public_id"]
    db.commit()
    db.refresh(user)

    return {
        "message": "Profile image uploaded successfully",
        "profileImage": user.profileImage
    }

# for forgot password
def forgot_password(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return  # Do not reveal if email exists

    otp = util.generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    util.otp_store[email] = {"otp": otp, "expires_at": expires_at}
    return otp  # Routes will handle sending email

def reset_password(db: Session, email: str, otp: str, new_password: str):
    # Check OTP
    record = util.otp_store.get(email)
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    if record["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if record["expires_at"] < datetime.utcnow():
        del util.otp_store[email]
        raise HTTPException(status_code=400, detail="OTP expired")

    # Get user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate new password
    util.validate_password_strength(new_password)

    # Update password
    user.passwordHash = pwd_context.hash(new_password)
    db.commit()
    db.refresh(user)

    # Remove OTP
    del util.otp_store[email]
    return user

# for change password
def change_user_password(db: Session, user: User, old_password: str, new_password: str):
    # Verify old password
    if not pwd_context.verify(old_password, user.passwordHash):
        return {"success": False, "detail": "Old password is incorrect"}

    # Validate new password strength
    util.validate_password_strength(new_password)

    # Update password
    user.passwordHash = pwd_context.hash(new_password)
    db.commit()
    db.refresh(user)

    return {"success": True, "detail": "Password changed successfully"}