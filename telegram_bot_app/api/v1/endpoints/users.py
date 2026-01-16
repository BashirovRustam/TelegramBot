from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from telegram_bot_app.db.session import get_async_session
from telegram_bot_app.crud.user import UserService
from telegram_bot_app.schemas.user import UserCreate, UserUpdate, UserResponse
from telegram_bot_app.db.models import UserRole

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session)
):
    user_service = UserService(db)
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    user_service = UserService(db)
    
    # Check if user with this telegram_id already exists
    existing_user = await user_service.get_user_by_telegram_id(user_data.telegram_id)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this telegram_id already exists")
    
    user = await user_service.create_user(user_data)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_async_session)
):
    user_service = UserService(db)
    user = await user_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    user_service = UserService(db)
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.get("/role/{role}", response_model=List[UserResponse])
async def get_users_by_role(
    role: UserRole,
    db: AsyncSession = Depends(get_async_session)
):
    user_service = UserService(db)
    users = await user_service.get_users_by_role(role)
    return users
