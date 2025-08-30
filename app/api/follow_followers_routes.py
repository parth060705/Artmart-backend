from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session  
from app.core.auth import get_current_user
from app.database import get_db
from app.models.models import User
from app.crud import crud
from app.crud.crud import serialize_user
from fastapi import APIRouter, Depends

from app.schemas.schemas import (
   FollowList
)

router = APIRouter()

# FOR PROTECTED LEVEL ROUTES
user_router = APIRouter(
    tags=["authorized"],
    # dependencies=[Depends(get_current_user)]  # Dependency Injection
)

# -------------------------
# FOLLOW & FOLLOWER ENDPOINTS
# -------------------------

@user_router.post("/{user_id}/follow")
def follow_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself.")
    
    result = crud.follow_user(db, current_user.id, user_id)
    
    if result.get("status") == "already_following":
        raise HTTPException(status_code=400, detail="Already following.")
    
    return {"msg": "Followed successfully"}

@user_router.delete("/{user_id}/unfollow")
def unfollow_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = crud.unfollow_user(db, current_user.id, user_id)
    
    if result.get("status") == "not_following":
        raise HTTPException(status_code=400, detail="Not following.")
    
    return {"msg": "Unfollowed successfully"}

@user_router.get("/me/followers", response_model=FollowList)
def get_my_followers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    followers = crud.get_followers(db, current_user.id)
    return {
        "users": [serialize_user(user) for user in followers],
        "count": len(followers)
    }

@user_router.get("/me/following", response_model=FollowList)
def get_my_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    following = crud.get_following(db, current_user.id)
    return {
        "users": [serialize_user(user) for user in following],
        "count": len(following)
    }
