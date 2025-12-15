from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.models import ExperimentStatus


class VariantCreate(BaseModel):
    name: str
    percent_allocated: float


class VariantUpdate(BaseModel):
    name: Optional[str] = None
    percent_allocated: Optional[float] = None
    enabled: Optional[bool] = None


class VariantResponse(BaseModel):
    id: int
    experiment_id: int
    name: str
    percent_allocated: float
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ExperimentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class EligibilityCheckRequest(BaseModel):
    user_id: str
    experiment_ids: List[int]


class ExperimentVariantInfo(BaseModel):
    variant_id: int


class EligibilityCheckResponse(BaseModel):
    eligible_experiment_ids: dict[int, ExperimentVariantInfo]


class ExperimentDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    variants: List[VariantResponse] = []
    segments: List['SegmentResponse'] = []

    class Config:
        from_attributes = True


# Avoid circular import
from src.schemas.segments import SegmentResponse
ExperimentDetailResponse.model_rebuild()
