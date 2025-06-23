from sqlalchemy import Column, String, Float, Text, Enum, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from app.database import Base

class RoleEnum(str, enum.Enum):
    buyer = "buyer"
    artist = "artist"
    admin = "admin"

class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    passwordHash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    profileImage = Column(String)
    createdAt = Column(DateTime, default=datetime.utcnow)
    
    artworks = relationship("Artwork", back_populates="artist")
    orders = relationship("Order", back_populates="buyer")

class Artwork(Base):
    __tablename__ = "artworks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    image = Column(String)
    price = Column(Float, nullable=False)
    category = Column(String)
    artistId = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    createdAt = Column(DateTime, default=datetime.utcnow)
    isSold = Column(Boolean, default=False)
    
    artist = relationship("User", back_populates="artworks")
