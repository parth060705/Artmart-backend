from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.models import User, RoleEnum
from app.crud import user_crud
import os


SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080
REFRESH_TOKEN_EXPIRE_DAYS = 30

# IMPORTANT: optional=True so we can use optional auth
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/login",
    auto_error=False
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ISSUER = os.getenv("JWT_ISSUER")
print(os.getenv("JWT_ISSUER"))

if not SECRET_KEY or not ISSUER: # added logic for microservice login
    raise RuntimeError("JWT config missing")


# -------------------------------------------------------------------------
# PASSWORD HASHING
# -------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# -------------------------------------------------------------------------
# TOKENS
# -------------------------------------------------------------------------

def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "iss": ISSUER})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Returns { user_id, username } or None"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], issuer=ISSUER)
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
        }
    except JWTError:
        return None


# -------------------------------------------------------------------------
# AUTH: PROTECTED USER
# -------------------------------------------------------------------------

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    # Fix: auto_error=False means token may be None → return 401 instead of 500
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decoded = decode_access_token(token)
    if not decoded or not decoded.get("user_id"):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = decoded["user_id"]
    username = decoded.get("username")

    # Try UUID
    try:
        user_uuid = UUID(user_id_str)
        user = db.query(User).filter(User.id == user_uuid).first()
    except Exception:
        user = None

    # Fallback: try username
    if not user and username:
        user = user_crud.get_user_by_username(db, username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# -------------------------------------------------------------------------
# AUTH: OPTIONAL USER (no errors)
# -------------------------------------------------------------------------

def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        return None

    try:
        return get_current_user(token=token, db=db)
    except HTTPException as e:
        if e.status_code == 401:
            return None
        raise e


# -------------------------------------------------------------------------
# AUTH: ADMIN ONLY
# -------------------------------------------------------------------------

def get_current_admin(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decoded = decode_access_token(token)
    if not decoded or not decoded.get("username"):
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_crud.get_user_by_username(db, decoded["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user
