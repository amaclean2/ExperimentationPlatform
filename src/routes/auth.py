from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.schemas.auth import ApiKeyCreate, ApiKeyResponse
from src.services import auth as auth_service
from typing import List

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/keys", response_model=ApiKeyResponse)
async def create_api_key(api_key: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.create_api_key(db, api_key.name)


@router.get("/keys", response_model=List[ApiKeyResponse])
async def get_api_keys(db: AsyncSession = Depends(get_db)):
    return await auth_service.get_all_api_keys(db)


@router.delete("/keys/{key_id}")
async def delete_api_key(key_id: int, db: AsyncSession = Depends(get_db)):
    await auth_service.delete_api_key(db, key_id)
    return {"message": "API key deleted successfully"}
