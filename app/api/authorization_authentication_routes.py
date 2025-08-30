from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session  
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from datetime import timedelta
from app.core import auth
from app.crud import crud

# FOR MEASSAGING
from fastapi import APIRouter, Depends

from app.schemas.schemas import (
    Token
)

router = APIRouter()

# ------------------------------------------
# AUTHORIZATION & AUTHENTICATION ENDPOINTS
# ------------------------------------------

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.passwordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = auth.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    username = auth.decode_access_token(refresh_token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_access_token = auth.create_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
