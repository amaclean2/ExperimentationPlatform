from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas.events import EventCreate, EventResponse, EventFilterRequest
from src.services import events as event_service
from .utils import verify_api_key
from typing import List

router = APIRouter(prefix="/api/events", tags=["events"], dependencies=[Depends(verify_api_key)])


@router.post("/", response_model=EventResponse)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    return await event_service.create_event(db, event)


@router.post("/{experiment_id}", response_model=List[EventResponse])
async def get_events(
    experiment_id: int,
    filters: EventFilterRequest = EventFilterRequest(),
    db: AsyncSession = Depends(get_db)
):
    return await event_service.get_events(db, experiment_id, filters)
