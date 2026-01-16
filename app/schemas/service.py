from typing import Optional
from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    """Схема для создания услуги"""
    salon_id: int = Field(..., description="Идентификатор салона")
    name: str = Field(..., min_length=1, max_length=255, description="Название услуги")
    duration_minutes: int = Field(..., gt=0, description="Длительность услуги в минутах")
    price: float = Field(..., ge=0, description="Стоимость услуги")
    is_active: bool = Field(default=True, description="Активна ли услуга")


class ServiceUpdate(BaseModel):
    """Схема для обновления услуги"""
    salon_id: Optional[int] = Field(None, description="Идентификатор салона")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название услуги")
    duration_minutes: Optional[int] = Field(None, gt=0, description="Длительность услуги в минутах")
    price: Optional[float] = Field(None, ge=0, description="Стоимость услуги")
    is_active: Optional[bool] = Field(None, description="Активна ли услуга")


class ServiceRead(BaseModel):
    """Схема для вывода информации об услуге"""
    id: int = Field(..., description="Уникальный идентификатор услуги")
    salon_id: int = Field(..., description="Идентификатор салона")
    name: str = Field(..., description="Название услуги")
    duration_minutes: int = Field(..., description="Длительность услуги в минутах")
    price: float = Field(..., description="Стоимость услуги")
    is_active: bool = Field(..., description="Активна ли услуга")

    class Config:
        from_attributes = True
