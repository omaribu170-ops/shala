from pydantic import BaseModel, Field
from typing import Optional, List, Any

class GroupCreate(BaseModel):
    name: str
    phones: List[str]

class EventCreate(BaseModel):
    title: str # Added title based on review feedback
    group_id: int
    type: str # Hangout or Treat
    date: str
    time: str
    dynamic_fields: Optional[List[dict]] = []
    itinerary: Optional[List[str]] = []
    has_restaurant: Optional[bool] = False
    min_cost: Optional[int] = None
    max_cost: Optional[int] = None

class EventRespond(BaseModel):
    status: str # Accepted, Declined

class UserBase(BaseModel):
    phone: str
    name: Optional[str] = None

    class Config:
        from_attributes = True

class TemplateCreate(BaseModel):
    type: str
    title: Optional[str] = None
    body: str
    placeholders: Optional[List[str]] = []

class EventAttendance(BaseModel):
    attended: bool
    review: Optional[str] = None
