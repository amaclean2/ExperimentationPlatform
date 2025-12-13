from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from src.models import User, Event
from src.schemas.events import EventCreate, EventFilterRequest
from typing import List, Optional


async def create_event(db: AsyncSession, event_data: EventCreate) -> Event:

    result = await db.execute(select(User).filter(User.id == event_data.user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_event = Event(
        user_id=user.id,
        experiment_id=event_data.experiment_id,
        variant_id=event_data.variant_id,
        type=event_data.type,
        properties=event_data.properties
    )

    db.add(db_event)

    await db.commit()
    await db.refresh(db_event)
    return db_event


async def get_events(
    db: AsyncSession,
    experiment_id: int,
    filters: EventFilterRequest
) -> List[Event]:
    query = select(Event).filter(Event.experiment_id == experiment_id)

    if filters.start_time:
        query = query.filter(Event.timestamp >= filters.start_time)

    if filters.end_time:
        query = query.filter(Event.timestamp <= filters.end_time)

    if filters.variant_id is not None:
        query = query.filter(Event.variant_id == filters.variant_id)

    if filters.event_types:
        query = query.filter(Event.type.in_(filters.event_types))

    if filters.user_ids:
        query = query.filter(Event.user_id.in_(filters.user_ids))

    result = await db.execute(query)
    events = result.scalars().all()
    return events
