import uuid
from fastapi import HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.models import models
from app.core import auth
from app.crud.user_crud import calculate_completion
from app.schemas.user_schema import UserRead

from dotenv import load_dotenv
import os

# Load .env file
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
        raise HTTPException(status_code=400, detail="Invalid Google token")


def register_with_google(db: Session, id_token_str: str):
    """Register a new user using Google OAuth."""
    id_info = verify_google_token(id_token_str)

    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")
    google_id = id_info.get("sub")

    if not email:
        raise HTTPException(status_code=400, detail="Invalid Google account data")

    # Check for existing user
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Create new user
    user = models.User(
        id=str(uuid.uuid4()),
        email=email,
        name=name,
        username=email.split("@")[0],
        profileImage=picture,
        googleId=google_id,
        passwordHash=None,
        isActive=True,
        isVerified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user.profileCompletion = calculate_completion(user, db)
    db.commit()

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


def login_with_google(db: Session, id_token_str: str):
    """Login an existing user via Google OAuth."""
    id_info = verify_google_token(id_token_str)
    email = id_info.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Invalid Google account data")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not registered. Please register first.")

    # Update completion score (optional)
    user.profileCompletion = calculate_completion(user, db)
    db.commit()

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
