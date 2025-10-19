import uuid
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.models import models
from app.core import auth
from app.schemas.user_schema import UserRead
from app.crud.user_crud import calculate_completion, suggest_usernames
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def verify_google_token(id_token_str: str):
    """Verify the Google ID token and extract user info."""
    try:
        id_info = id_token.verify_oauth2_token(
            id_token_str, requests.Request(), GOOGLE_CLIENT_ID
        )
        return id_info
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid Google token"}
        )


def authenticate_with_google(db: Session, id_token_str: str):
    """Unified Google OAuth handler — auto-register or log in existing user."""
    id_info = verify_google_token(id_token_str)

    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")
    google_id = id_info.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid Google account data"}
        )

    # --- Check if user already exists ---
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        # --- Register new Google user ---
        base_username = email.split("@")[0]
        suggestions = suggest_usernames(db, base_username, max_suggestions=1)
        username = suggestions[0] if suggestions else f"{base_username}_{uuid.uuid4().hex[:4]}"

        # Note: passwordHash cannot be NULL, so use a placeholder
        placeholder_password = "GOOGLE_USER_ACCOUNT"

        user = models.User(
            id=str(uuid.uuid4()),
            name=name or base_username,
            email=email,
            username=username,
            passwordHash=placeholder_password,
            profileImage=picture,
            role=models.RoleEnum.user,
            isActive=True,
            isAgreedtoTC=True,  # Optional, set False if you want explicit consent
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    # --- Update profile completion ---
    user.profile_completion = calculate_completion(user, db)
    db.commit()

    # --- Generate tokens ---
    access_token = auth.create_token(data={"sub": str(user.id)})
    refresh_token = auth.create_token(
        data={"sub": str(user.id)}, expires_delta=auth.REFRESH_TOKEN_EXPIRE_DAYS
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserRead.from_orm(user),
    }
