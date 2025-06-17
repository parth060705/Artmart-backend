from sqlalchemy import Column, String, Float, Text, Enum, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .database import Base
import enum

class RoleEnum(str, enum.Enum):
    buyer = "buyer"
    artist = "artist"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    passwordHash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default="buyer")
    profileImage = Column(String)
    createdAt = Column(TIMESTAMP)

    artworks = relationship("Artwork", back_populates="artist")

class Artwork(Base):
    __tablename__ = "artworks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    image = Column(String)
    price = Column(Float, nullable=False)
    category = Column(String)
    artistId = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    createdAt = Column(TIMESTAMP)
    isSold = Column(Boolean, default=False)

    artist = relationship("User", back_populates="artworks")

# class Order(Base):
#     __tablename__= "Orders"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     buyerId = Column(UUID(as_uuid=True), ForeignKey("user.id"))
#     artworkId = Column(UUID(as_uuid=True), ForeignKey("artwork.id"))
#     totalAmount = Column(Float, nullable=False)
#     paymentStatus = Column(Enum(RoleEnum))
    

