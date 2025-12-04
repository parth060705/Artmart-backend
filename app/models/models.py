from sqlalchemy import (
    Column, String, Float, Text, Enum, Boolean, ForeignKey,
    Integer, DateTime, CHAR, Table, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from sqlalchemy import Enum as SqlEnum
from app.database import Base

# -------------------------
# ENUM DEFINITIONS
# -------------------------

class RoleEnum(str, enum.Enum):
    user = "user"
    admin = "admin"
    store = "store"

class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"

# -------------------------
# PAYMENT METHOD ENUM
# -------------------------

class PaymentMethodEnum(str, enum.Enum):
    credit_card = "credit_card"
    debit_card = "debit_card"
    net_banking = "net_banking"
    upi = "upi"
    cod = "cod"  # Cash on Delivery

# -------------------------
# STATUS ENUM
# -------------------------

class StatusENUM(str, enum.Enum):
    visible = "visible"
    pending_moderation = "pending_moderation"
    hidden = "hidden"


# -------------------------
# FOLLOWERS ASSOCIATION TABLE
# -------------------------

followers_association = Table(
    "user_followers",
    Base.metadata,
    Column("follower_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("followed_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow)
)

# -------------------------
# USER MODEL
# -------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    passwordHash = Column(String(255), nullable=False)
    role = Column(SqlEnum(RoleEnum, native_enum=False), nullable=False, default=RoleEnum.user)
    profileImage = Column(String(255), nullable=True)
    profileImagePublicId = Column(String(255), nullable=True)  
    # createdAt = Column(DateTime, nullable=False)     
    # updatedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 
    location = Column(String(100), nullable=True)
    pincode = Column(CHAR(6), nullable=True)
    gender = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(String(15), nullable=True)
    bio = Column(String(500), nullable=True)
    profile_completion = Column(Integer, default=0)
    isActive = Column(Boolean, default=False)         
    isAgreedtoTC = Column(Boolean, default=False)         
 

    # Relationships
    artworks = relationship("Artwork", back_populates="artist")
    orders = relationship("Order", back_populates="buyer")
    reviews = relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewerId")
    Saved_items = relationship("Saved", back_populates="user")
    cart_items = relationship("Cart", back_populates="user")
    liked_artworks = relationship("ArtworkLike", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    followers = relationship(
        "User",
        secondary=followers_association,
        primaryjoin=id == followers_association.c.followed_id,
        secondaryjoin=id == followers_association.c.follower_id,
        backref="following"
    )

    # Follow utility methods
    def follow(self, user: "User"):
        if user not in self.following:
            self.following.append(user)

    def unfollow(self, user: "User"):
        if user in self.following:
            self.following.remove(user)

    def is_following(self, user: "User") -> bool:
        return user in self.following

    def is_followed_by(self, user: "User") -> bool:
        return user in self.followers

# -------------------------
# ARTWORK MODEL
# -------------------------

class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    images = relationship(
        "ArtworkImage",
        cascade="all, delete-orphan",
        back_populates="artwork",
    )
    tags = Column(JSON, default=list, nullable=True)  
    price = Column(Float, nullable=True)                       ####
    quantity = Column(Integer, nullable=True, default=None)    ####  
    category = Column(String(100), nullable=False)
    artistId = Column(String(36), ForeignKey("users.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)
    isSold = Column(Boolean, default=False)
    isDeleted = Column(Boolean, default=False)    
    forSale = Column(Boolean, default=False)     

    # Relationships
    artist = relationship("User", back_populates="artworks")
    orders = relationship("Order", back_populates="artwork")
    reviews = relationship("Review", back_populates="artwork")
    Saved_items = relationship("Saved", back_populates="artwork")
    cart_items = relationship("Cart", back_populates="artwork")
    likes = relationship("ArtworkLike", back_populates="artwork", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="artwork", cascade="all, delete-orphan")
    status = Column(String(20), default="pending_moderation")  ##


class ArtworkImage(Base):
    __tablename__ = "artwork_images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artwork_id = Column(String(36), ForeignKey("artworks.id"))
    url = Column(String(500), nullable=False)       # Cloudinary URLs can be long
    public_id = Column(String(255), nullable=False) # public_id is shorter


    # Relationships
    artwork = relationship("Artwork", back_populates="images")

# -------------------------
# ARTWORK LIKES
# -------------------------

class ArtworkLike(Base):
    __tablename__ = "artwork_likes"

    userId = Column(String(36), ForeignKey("users.id"), primary_key=True)
    artworkId = Column(String(36), ForeignKey("artworks.id"), primary_key=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)

    # Relationships
    artwork = relationship("Artwork", back_populates="likes")
    user = relationship("User", back_populates="liked_artworks")

# -------------------------
# COMMENT MODEL
# -------------------------

class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    artwork_id = Column(String(36), ForeignKey("artworks.id"), nullable=False)
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending_moderation")  ##

    # Relationships
    user = relationship("User", back_populates="comments")
    artwork = relationship("Artwork", back_populates="comments")

# -------------------------
# ORDER MODEL
# -------------------------

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    buyerId = Column(String(36), ForeignKey("users.id"))
    artworkId = Column(String(36), ForeignKey("artworks.id"))
    totalAmount = Column(Float, nullable=False)
    paymentStatus = Column(SqlEnum(PaymentStatusEnum, native_enum=False), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)

    # Relationships
    buyer = relationship("User", back_populates="orders")
    artwork = relationship("Artwork", back_populates="orders")

# -------------------------
# REVIEW MODEL
# -------------------------

class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reviewerId = Column(String(36), ForeignKey("users.id"))
    artistId = Column(String(36), ForeignKey("users.id"))
    artworkId = Column(String(36), ForeignKey("artworks.id"), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    createdAt = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending_moderation")  ##

    # Relationships
    reviewer = relationship("User", back_populates="reviews", foreign_keys=[reviewerId])
    artwork = relationship("Artwork", back_populates="reviews")
    artist = relationship("User", foreign_keys=[artistId])

# -------------------------
# REVIEW MODEL
# -------------------------

class ArtistReview(Base):
    __tablename__ = "artist_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    artist_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending_moderation")  ##

    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="artist_reviews_made")
    artist = relationship("User", foreign_keys=[artist_id], backref="artist_reviews_received")

# -------------------------
# SAVED MODEL
# -------------------------

class Saved(Base):
    __tablename__ = "saved"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column(String(36), ForeignKey("users.id"))
    artworkId = Column(String(36), ForeignKey("artworks.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="Saved_items")
    artwork = relationship("Artwork", back_populates="Saved_items")

# -------------------------
# CART MODEL
# -------------------------

class Cart(Base):
    __tablename__ = "cart"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column(String(36), ForeignKey("users.id"))
    artworkId = Column(String(36), ForeignKey("artworks.id"))
    purchase_quantity = Column(Integer, nullable=False, default=1)
    createdAt = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="cart_items")
    artwork = relationship("Artwork", back_populates="cart_items")

# -------------------------
# MESSAGE MODEL            
# -------------------------

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=True)  # Can be empty for typing
    # timestamp = Column(DateTime, default=datetime.utcnow)
    timestamp = Column(DateTime, nullable=False)
    is_read = Column(Boolean, default=False)
    message_type = Column(String(20), default="text")  # "text", "typing", etc.

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

# -------------------------
# PAYMENT MODEL
# -------------------------

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    transaction_id = Column(String(100), unique=True, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(SqlEnum(PaymentStatusEnum, native_enum=False), nullable=False, default=PaymentStatusEnum.pending)
    method = Column(SqlEnum(PaymentMethodEnum, native_enum=False), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # createdAt = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", backref="payments")
    order = relationship("Order", backref="payment")

# -------------------------
# ADMIN AUDIT LOG MODEL
# -------------------------

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    method = Column(String(10), nullable=False)  # e.g., GET, POST, DELETE
    path = Column(String(255), nullable=False)   # e.g., /admin/delete-user/5
    action = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship
    admin = relationship("User", backref="admin_logs")

# -------------------------
# MODERATION QUEUE LOG MODEL
# -------------------------
class ModerationQueue(Base):
    __tablename__ = "moderation_queue"

    # id = Column(Integer, primary_key=True)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    table_name = Column(String(50))
    # content_id = Column(Integer)
    content_id = Column(String(36), nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)
    checked = Column(Boolean, default=False)

# ============================================================
#                COMMUNITY SYSTEM (ONLY THESE TABLES)
# ============================================================

# -------------------------
# COMMUNITY MODEL
# -------------------------

class Community(Base):
    __tablename__ = "communities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"))
    bannerImage = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User")

    members = relationship("CommunityMember", back_populates="community")
    artworks = relationship("CommunityArtwork", back_populates="community")


# -------------------------
# COMMUNITY MEMBER
# -------------------------

class CommunityMember(Base):
    __tablename__ = "community_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    community_id = Column(String(36), ForeignKey("communities.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)

    community = relationship("Community", back_populates="members")
    user = relationship("User")


# -------------------------
# COMMUNITY ARTWORK / POST MODEL
# -------------------------

class CommunityArtwork(Base):
    __tablename__ = "community_artworks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    community_id = Column(String(36), ForeignKey("communities.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    image = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    community = relationship("Community", back_populates="artworks")
    user = relationship("User")
    likes = relationship("CommunityLike", back_populates="artwork")


# -------------------------
# COMMUNITY LIKE MODEL
# -------------------------

class CommunityLike(Base):
    __tablename__ = "community_likes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    artwork_id = Column(String(36), ForeignKey("community_artworks.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    artwork = relationship("CommunityArtwork", back_populates="likes")
    user = relationship("User")
