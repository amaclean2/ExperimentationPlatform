from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from src.models import ApiKey
from typing import List
import secrets


async def create_api_key(db: AsyncSession, name: str) -> ApiKey:
    key = secrets.token_urlsafe(32)

    db_api_key = ApiKey(
        key=key,
        name=name
    )
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)
    return db_api_key


async def get_all_api_keys(db: AsyncSession) -> List[ApiKey]:
    result = await db.execute(select(ApiKey))
    api_keys = result.scalars().all()
    return api_keys


async def delete_api_key(db: AsyncSession, key_id: int) -> None:
    result = await db.execute(select(ApiKey).filter(ApiKey.id == key_id))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(api_key)
    await db.commit()