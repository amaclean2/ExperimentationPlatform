from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from src.models import User, Experiment, Segment, UserSegment, ExperimentSegment
from src.schemas.segments import SegmentCreate, SegmentUpdate
from src.cache import cached, segment_cache, invalidate_segment_cache, invalidate_experiment_cache
from typing import List


async def create_segment(db: AsyncSession, segment_data: SegmentCreate) -> Segment:
    db_segment = Segment(
        name=segment_data.name,
        description=segment_data.description,
        rules=segment_data.rules
    )
    db.add(db_segment)
    await db.commit()
    await db.refresh(db_segment)
    return db_segment


@cached(segment_cache)
async def get_segments(db: AsyncSession) -> List[Segment]:
    result = await db.execute(select(Segment))
    segments = result.scalars().all()
    return segments


@cached(segment_cache)
async def get_segment_by_id(db: AsyncSession, segment_id: int) -> Segment:
    result = await db.execute(
        select(Segment)
        .options(selectinload(Segment.user_assignments).selectinload(UserSegment.user))
        .filter(Segment.id == segment_id)
    )
    segment = result.scalar_one_or_none()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    segment.users = [assignment.user for assignment in segment.user_assignments]

    return segment


async def update_segment(db: AsyncSession, segment_id: int, segment_update: SegmentUpdate) -> Segment:
    result = await db.execute(select(Segment).filter(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    if segment_update.name is not None:
        result = await db.execute(
            select(Segment).filter(
                Segment.name == segment_update.name,
                Segment.id != segment_id
            )
        )
        
        existing_segment = result.scalar_one_or_none()
        if existing_segment:
            raise HTTPException(
                status_code=400,
                detail=f"A segment with name '{segment_update.name}' already exists"
            )
        segment.name = segment_update.name

    if segment_update.description is not None:
        segment.description = segment_update.description

    if segment_update.rules is not None:
        segment.rules = segment_update.rules

    await db.commit()
    await db.refresh(segment)

    invalidate_segment_cache(segment_id)

    return segment


async def assign_user_to_segment(db: AsyncSession, user_id: str, segment_id: int) -> None:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(select(Segment).filter(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    db_assignment = UserSegment(
        user_id=user_id,
        segment_id=segment_id
    )
    db.add(db_assignment)
    await db.commit()

    invalidate_segment_cache(segment_id)


async def assign_segment_to_experiment(db: AsyncSession, experiment_id: int, segment_id: int) -> None:
    result = await db.execute(select(Experiment).filter(Experiment.id == experiment_id))
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    result = await db.execute(select(Segment).filter(Segment.id == segment_id))
    segment = result.scalar_one_or_none()
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    db_assignment = ExperimentSegment(
        experiment_id=experiment_id,
        segment_id=segment_id
    )

    db.add(db_assignment)
    await db.commit()

    invalidate_experiment_cache(experiment_id)
    invalidate_segment_cache(segment_id)


async def remove_segment_from_experiment(db: AsyncSession, experiment_id: int, segment_id: int) -> None:
    result = await db.execute(
        select(ExperimentSegment).filter(
            ExperimentSegment.experiment_id == experiment_id,
            ExperimentSegment.segment_id == segment_id
        )
    )
    
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=404, detail="Segment assignment not found")

    await db.delete(assignment)
    await db.commit()

    invalidate_experiment_cache(experiment_id)
    invalidate_segment_cache(segment_id)
