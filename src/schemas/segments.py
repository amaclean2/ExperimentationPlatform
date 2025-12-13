from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SegmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rules: Optional[dict] = None


class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[dict] = None


class SegmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    rules: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class UserSegmentAssign(BaseModel):
    user_id: str
    segment_id: int


class ExperimentSegmentAssign(BaseModel):
    experiment_id: int
    segment_id: int


class SegmentDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    rules: Optional[dict]
    created_at: datetime
    users: List['UserResponse'] = []

    class Config:
        from_attributes = True


# Avoid circular import - this will be resolved when schemas are imported
from src.schemas.users import UserResponse
SegmentDetailResponse.model_rebuild()
