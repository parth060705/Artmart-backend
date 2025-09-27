from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text
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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# USER OPERATIONS
# -------------------------

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: UUID):
    return db.query(models.User).filter(models.User.id == str(user_id)).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

#-------------HELPER CLASS FOR USER REGISTER------------------

# 1)HELPER CLASS FOR VALIDATION FOR STRONG PASSWORD
def validate_password_strength(password: str):
    password = password.strip()  # remove leading/trailing spaces/newlines

    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must be at least 8 characters long"}
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must contain an uppercase letter"}
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must contain a lowercase letter"}
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must contain a number"}
        )
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password must contain a special character"}
        )

# 2)HELPER CLASS FOR SUGGEST UNIQUE USERNAME
def suggest_usernames(db: Session, base_username: str, max_suggestions: int = 5):
    base = base_username.lower().replace(" ", "").replace(".", "").replace("_", "")
    suggestions = []

    while len(suggestions) < max_suggestions:
        suffix = ''.join(random.choices(string.digits, k=3))
        candidate = f"{base}{suffix}"
        if not db.query(models.User).filter_by(username=candidate).first():
            suggestions.append(candidate)
    return suggestions

# # 3)HELPER CLASS FOR FLOW REGISTER
# def calculate_completion(user) -> int:
#     completion = 0

#     # Part 1 (40%) → Basic Info
#     if user.name and user.username and user.passwordHash:
#         completion += 40

#     # Part 2 (30%) → Bio details
#     if user.bio and user.gender and user.age:
#         completion += 30

#     # Part 3 (30%) → Contact info
#     if user.location and user.pincode and user.phone:
#         completion += 30

#     return completion


def calculate_completion(user: models.User, db: Session) -> int:
    completion = 0

    # Part 1: Basic info
    if user.name and user.username and user.passwordHash:
        completion += 40

    # Part 2: Bio, gender, age
    if user.bio and user.gender and user.age:
        completion += 20

    # Part 3: Contact info
    if user.location and user.pincode and user.phone:
        completion += 20

    # Part 4: Following at least 5 users
    num_following = db.query(models.followers_association).filter(
        models.followers_association.c.follower_id == user.id
    ).count()
    if num_following >= 5:
        completion += 20

    # Part 5: At least 1 artwork
    num_artworks = db.query(models.Artwork).filter(models.Artwork.artistId == user.id).count()
    if num_artworks >= 1:
        completion += 20

    return min(completion, 100)

#---------------------------------------------------------------------------------------------

# def create_user(db: Session, user: schemas.UserCreate):
#     hashed_password = pwd_context.hash(user.password)

#     db_user = models.User(
#         name=user.name,
#         email=user.email,
#         username=user.username,
#         passwordHash=hashed_password,
#         role=models.RoleEnum.user,
#         profileImage=str(user.profileImage) if user.profileImage else None,
#         location=user.location,
#         gender=user.gender,
#         bio=user.bio,
#         age=user.age,
#         phone=str(user.phone) if user.phone else None,
#         pincode=str(user.pincode) if user.pincode else None,
#         isAgreedtoTC=user.isAgreedtoTC
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


# def update_user_details(db: Session, user_id: int, user_update: schemas.UserUpdate):
#     db_user = db.query(models.User).filter(models.User.id == user_id).first()
#     if not db_user:
#         raise ValueError("User not found")
#     if user_update.name is not None:
#         db_user.name = user_update.name
#     if user_update.location is not None:
#         db_user.location = user_update.location
#     if user_update.gender is not None:
#         db_user.gender = user_update.gender
#     if user_update.age is not None:
#         db_user.age = user_update.age
#     if user_update.bio is not None:
#         db_user.bio = user_update.bio    
#     if user_update.pincode is not None:
#         db_user.pincode = str(user_update.pincode)
#     if user_update.phone is not None:
#         db_user.phone = str(user_update.phone)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

#---------------------

# Create User (progressive registration)
def create_user(db: Session, user: user_schema.UserCreate):
    hashed_password = pwd_context.hash(user.password)

    db_user = models.User(
        name=user.name,
        email=user.email,
        username=user.username,
        passwordHash=hashed_password,
        role=models.RoleEnum.user,
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
    db_user.profile_completion = calculate_completion(db_user, db)

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
    db_user.profile_completion = calculate_completion(db_user, db)

    db.commit()
    db.refresh(db_user)
    return db_user
#---------------------

#----------------------------------------------------------------------------------

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
