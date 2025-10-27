from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_ , and_, func, text, desc
from fastapi import HTTPException, UploadFile, File, status
from app.models import models
from fastapi import UploadFile, HTTPException
import random, string
import re


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

# 3)HELPER CLASS FOR REGISTERATION FLOW
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

# 3)HELPER CLASS FOR EMAIL OTP RESET PASSWORD
otp_store = {} # Temporary in-memory OTP store in production store it in redis # {email: {"otp": "123456", "expires_at": datetime}}

def generate_otp(length: int = 6):
    return ''.join(random.choices("0123456789", k=length))



#-------------HELPER CLASS FOR USER REGISTER------------------

# 1)HELPER CLASS FOR VALIDATION FOR STRONG PASSWORD
# def validate_password_strength(password: str):
#     password = password.strip()  # remove leading/trailing spaces/newlines

#     if len(password) < 8:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"message": "Password must be at least 8 characters long"}
#         )
#     if not re.search(r"[A-Z]", password):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"message": "Password must contain an uppercase letter"}
#         )
#     if not re.search(r"[a-z]", password):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"message": "Password must contain a lowercase letter"}
#         )
#     if not re.search(r"\d", password):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"message": "Password must contain a number"}
#         )
#     if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail={"message": "Password must contain a special character"}
#         )

# # 2)HELPER CLASS FOR SUGGEST UNIQUE USERNAME
# def suggest_usernames(db: Session, base_username: str, max_suggestions: int = 5):
#     base = base_username.lower().replace(" ", "").replace(".", "").replace("_", "")
#     suggestions = []

#     while len(suggestions) < max_suggestions:
#         suffix = ''.join(random.choices(string.digits, k=3))
#         candidate = f"{base}{suffix}"
#         if not db.query(models.User).filter_by(username=candidate).first():
#             suggestions.append(candidate)
#     return suggestions

# 3)HELPER CLASS FOR REGISTERATION FLOW
# def calculate_completion(user: models.User, db: Session) -> int:
#     completion = 0

#     # Part 1: Basic info
#     if user.name and user.username and user.passwordHash:
#         completion += 40

#     # Part 2: Bio, gender, age
#     if user.bio and user.gender and user.age:
#         completion += 20

#     # Part 3: Contact info
#     if user.location and user.pincode and user.phone:
#         completion += 20

#     # Part 4: Following at least 5 users
#     num_following = db.query(models.followers_association).filter(
#         models.followers_association.c.follower_id == user.id
#     ).count()
#     if num_following >= 5:
#         completion += 20

#     # Part 5: At least 1 artwork
#     num_artworks = db.query(models.Artwork).filter(models.Artwork.artistId == user.id).count()
#     if num_artworks >= 1:
#         completion += 20

#     return min(completion, 100)

# 3)HELPER CLASS FOR EMAIL OTP RESET PASSWORD
# otp_store = {} # Temporary in-memory OTP store in production store it in redis # {email: {"otp": "123456", "expires_at": datetime}}

# def generate_otp(length: int = 6):
#     return ''.join(random.choices("0123456789", k=length))

# 4)HELPER CLASS FOR AVGRATING, REVIEW COUNT AND CALCULATING RANK
# def get_user_rating_info(db, user_id, m=5):
#     # Step 1: Get avg rating and review count for this artist
#     rating_data = (
#         db.query(
#             func.avg(models.ArtistReview.rating).label("avgRating"),
#             func.count(models.ArtistReview.id).label("reviewCount")
#         )
#         .filter(models.ArtistReview.artist_id == str(user_id))
#         .first()
#     )

#     avg_rating = float(rating_data.avgRating or 0.0)
#     review_count = int(rating_data.reviewCount or 0)

#     # Step 2: Get global average rating (C)
#     global_avg = db.query(func.avg(models.ArtistReview.rating)).scalar()
#     global_avg = float(global_avg or 0.0)

#     # Step 3: Compute weighted rating (Bayesian formula)
#     weighted_rating = (
#         (review_count / (review_count + m)) * avg_rating
#         + (m / (review_count + m)) * global_avg
#         if (review_count + m) > 0 else 0.0
#     )

#     # Step 4: Compute weighted ratings for all artists to get ranks
#     artist_stats = (
#         db.query(
#             models.User.id.label("artist_id"),
#             func.avg(models.ArtistReview.rating).label("avgRating"),
#             func.count(models.ArtistReview.id).label("reviewCount")
#         )
#         .outerjoin(models.ArtistReview, models.User.id == models.ArtistReview.artist_id)
#         .group_by(models.User.id)
#         .all()
#     )

#     ranked_artists = []
#     for artist in artist_stats:
#         R = float(artist.avgRating or 0.0)
#         v = int(artist.reviewCount or 0)
#         w_rating = (
#             (v / (v + m)) * R + (m / (v + m)) * global_avg
#             if (v + m) > 0 else 0.0
#         )
#         ranked_artists.append((artist.artist_id, w_rating))

#     ranked_artists.sort(key=lambda x: x[1], reverse=True)

#     # Step 5: Find rank
#     rank = next((idx for idx, (a_id, _) in enumerate(ranked_artists, start=1) if str(a_id) == str(user_id)), None)

#     return {
#         "avgRating": avg_rating,
#         "reviewCount": review_count,
#         "weightedRating": weighted_rating,  # Optional, can remove if you want old output
#         "rank": rank
#     }
