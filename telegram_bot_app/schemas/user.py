from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from telegram_bot_app.models.user import UserRoleEnum


class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    telegram_id: int = Field(..., description="Уникальный идентификатор Telegram пользователя")
    full_name: str = Field(..., min_length=1, max_length=255, description="Полное имя пользователя")
    role: UserRoleEnum = Field(default=UserRoleEnum.CLIENT, description="Роль пользователя")
    is_active: bool = Field(default=True, description="Активен ли пользователь")


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    telegram_id: Optional[int] = Field(None, description="Уникальный идентификатор Telegram пользователя")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Полное имя пользователя")
    role: Optional[UserRoleEnum] = Field(None, description="Роль пользователя")
    is_active: Optional[bool] = Field(None, description="Активен ли пользователь")


class UserRead(BaseModel):
    """Схема для вывода информации о пользователе"""
    id: int = Field(..., description="Уникальный идентификатор пользователя в базе данных")
    telegram_id: int = Field(..., description="Уникальный идентификатор Telegram пользователя")
    full_name: str = Field(..., description="Полное имя пользователя")
    role: UserRoleEnum = Field(..., description="Роль пользователя")
    is_active: bool = Field(..., description="Активен ли пользователь")
    created_at: datetime = Field(..., description="Дата и время создания пользователя")

    class Config:
        from_attributes = True
