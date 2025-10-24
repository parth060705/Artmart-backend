from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.models.models import RoleEnum
from uuid import UUID

# from app.crud import crud
from app.crud import user_crud

# JWT config (use environment vars in prod)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1080
REFRESH_TOKEN_EXPIRE_DAYS = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")  # ***
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode token and return both user_id + username if available."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username")
        }
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    decoded = decode_access_token(token)
    if not decoded or not decoded.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = decoded["user_id"]
    username = decoded.get("username")

    # Convert string ID to UUID
    try:
        user_uuid = UUID(user_id_str)
    except (ValueError, TypeError):
        user_uuid = None

    user = None
    if user_uuid:
        user = db.query(User).filter(User.id == user_uuid).first()

    # Fallback to username if needed
    if not user and username:
        user = user_crud.get_user_by_username(db, username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


#-----------------------------------------------------------------------

# def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
#     username = decode_access_token(token)
#     if username is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     user = user_crud.get_user_by_username(db, username)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if user.role != RoleEnum.admin:
#         raise HTTPException(status_code=403, detail="Admin access required")
#     return user

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    decoded = decode_access_token(token)
    if not decoded or not decoded.get("username"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_crud.get_user_by_username(db, decoded["username"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user



# HELPER CLASS FOR AUTHENTICATION BY TOKEN     USED IN (SPECIFIC ARTWORKS ROUTES, LIST ARTWORK)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

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