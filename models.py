from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    avatar_id = Column(String, nullable=True)
    device_tokens = Column(JSON, default=list)

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    image = Column(String, nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User")
    members = relationship("GroupMember", back_populates="group")

class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="Member") # Admin or Member

    group = relationship("Group", back_populates="members")
    user = relationship("User")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String) # Added title
    group_id = Column(Integer, ForeignKey("groups.id"))
    creator_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String) # Hangout or Treat
    has_restaurant = Column(Boolean, default=False)
    dynamic_fields = Column(JSON, default=list)
    itinerary = Column(JSON, default=list)
    date = Column(String)
    time = Column(String)
    min_cost = Column(Integer, nullable=True)
    max_cost = Column(Integer, nullable=True)

    participants = relationship("EventParticipant", back_populates="event")
    group = relationship("Group")
    creator = relationship("User")

class EventParticipant(Base):
    __tablename__ = "event_participants"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="Pending") # Pending, Accepted, Declined
    attended = Column(Boolean, default=False)
    review = Column(String, nullable=True)

    event = relationship("Event", back_populates="participants")

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    title = Column(String, nullable=True)
    body = Column(String)
    placeholders = Column(JSON, default=list)

class OTPCode(Base):
    __tablename__ = "otp_codes"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    code = Column(String)
    expires_at = Column(Integer) # Unix timestamp
