from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from src.models import User
from src.schemas.users import UserCreate, UserUpdate
from typing import List


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    db_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        is_premium=user_data.is_premium,
        country_code=user_data.country_code
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_users(db: AsyncSession) -> List[User]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


async def get_user_by_id(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def update_user(db: AsyncSession, user_id: str, user_update: UserUpdate) -> User:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.first_name is not None:
        user.first_name = user_update.first_name

    if user_update.last_name is not None:
        user.last_name = user_update.last_name

    if user_update.email is not None:
        result = await db.execute(
            select(User).filter(
                User.email == user_update.email,
                User.id != user_id
            )
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"A user with email '{user_update.email}' already exists"
            )
        user.email = user_update.email

    if user_update.is_premium is not None:
        user.is_premium = user_update.is_premium

    if user_update.country_code is not None:
        user.country_code = user_update.country_code

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: str) -> None:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
