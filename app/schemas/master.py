from typing import Optional
from pydantic import BaseModel, Field


class MasterCreate(BaseModel):
    """Схема для создания мастера"""
    user_id: int = Field(..., description="Идентификатор пользователя")
    salon_id: int = Field(..., description="Идентификатор салона")
    is_active: bool = Field(default=True, description="Активен ли мастер")


class MasterUpdate(BaseModel):
    """Схема для обновления мастера"""
    user_id: Optional[int] = Field(None, description="Идентификатор пользователя")
    salon_id: Optional[int] = Field(None, description="Идентификатор салона")
    is_active: Optional[bool] = Field(None, description="Активен ли мастер")


class MasterRead(BaseModel):
    """Схема для вывода информации о мастере"""
    id: int = Field(..., description="Уникальный идентификатор мастера")
    user_id: int = Field(..., description="Идентификатор пользователя")
    salon_id: int = Field(..., description="Идентификатор салона")
    is_active: bool = Field(..., description="Активен ли мастер")

    class Config:
        from_attributes = True
