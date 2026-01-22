from typing import Optional
from pydantic import BaseModel, Field


class SalonCreate(BaseModel):
    """Схема для создания салона"""
    name: str = Field(..., min_length=1, max_length=255, description="Название салона")
    address: str = Field(..., min_length=1, max_length=500, description="Адрес салона")
    description: Optional[str] = Field(None, max_length=1000, description="Описание салона")
    is_active: bool = Field(default=True, description="Активен ли салон")
    gis_link: Optional[str] = Field(None, max_length=1000, description="Ссылка на 2GIS")


class SalonUpdate(BaseModel):
    """Схема для обновления салона"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Название салона")
    address: Optional[str] = Field(None, min_length=1, max_length=500, description="Адрес салона")
    description: Optional[str] = Field(None, max_length=1000, description="Описание салона")
    is_active: Optional[bool] = Field(None, description="Активен ли салон")
    gis_link: Optional[str] = Field(None, max_length=1000, description="Ссылка на 2GIS")


class SalonRead(BaseModel):
    """Схема для вывода информации о салоне"""
    id: int = Field(..., description="Уникальный идентификатор салона")
    name: str = Field(..., description="Название салона")
    address: str = Field(..., description="Адрес салона")
    description: Optional[str] = Field(..., description="Описание салона")
    is_active: bool = Field(..., description="Активен ли салон")
    gis_link: Optional[str] = Field(..., description="Ссылка на 2GIS")

    class Config:
        from_attributes = True
