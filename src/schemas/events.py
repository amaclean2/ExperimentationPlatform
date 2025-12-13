from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EventCreate(BaseModel):
    user_id: str
    experiment_id: Optional[int] = None
    variant_id: Optional[int] = None
    type: str
    properties: Optional[dict] = None


class EventFilterRequest(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    variant_id: Optional[int] = None
    event_types: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None


class EventResponse(BaseModel):
    id: int
    user_id: str
    experiment_id: Optional[int]
    variant_id: Optional[int]
    type: str
    timestamp: datetime
    properties: Optional[dict]

    class Config:
        from_attributes = True
