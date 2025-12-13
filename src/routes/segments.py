from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas.segments import (
    SegmentCreate, SegmentUpdate, SegmentResponse,
    UserSegmentAssign, ExperimentSegmentAssign, SegmentDetailResponse
)
from src.services import segments as segment_service
from .utils import verify_api_key
from typing import List

router = APIRouter(prefix="/api/segments", tags=["segments"], dependencies=[Depends(verify_api_key)])


@router.post("/", response_model=SegmentResponse)
async def create_segment(segment: SegmentCreate, db: AsyncSession = Depends(get_db)):
    return await segment_service.create_segment(db, segment)


@router.get("/", response_model=List[SegmentResponse])
async def get_segments(db: AsyncSession = Depends(get_db)):
    return await segment_service.get_segments(db)


@router.get("/{segment_id}", response_model=SegmentDetailResponse)
async def get_segment(segment_id: int, db: AsyncSession = Depends(get_db)):
    return await segment_service.get_segment_by_id(db, segment_id)


@router.put("/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    segment_id: int,
    segment_update: SegmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await segment_service.update_segment(db, segment_id, segment_update)


@router.post("/assign-user")
async def assign_user_to_segment(assignment: UserSegmentAssign, db: AsyncSession = Depends(get_db)):
    await segment_service.assign_user_to_segment(db, assignment.user_id, assignment.segment_id)
    return {"message": "User assigned to segment successfully"}


@router.post("/assign-experiment")
async def assign_segment_to_experiment(assignment: ExperimentSegmentAssign, db: AsyncSession = Depends(get_db)):
    await segment_service.assign_segment_to_experiment(db, assignment.experiment_id, assignment.segment_id)
    return {"message": "Segment assigned to experiment successfully"}


@router.delete("/unassign-experiment")
async def remove_segment_from_experiment(assignment: ExperimentSegmentAssign, db: AsyncSession = Depends(get_db)):
    await segment_service.remove_segment_from_experiment(db, assignment.experiment_id, assignment.segment_id)
    return {"message": "Segment removed from experiment successfully"}
