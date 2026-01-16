from datetime import datetime, date, time
from typing import Optional
from pydantic import BaseModel, Field
from telegram_bot_app.models.appointment import AppointmentStatusEnum


class AppointmentCreate(BaseModel):
    """Схема для создания записи на услугу"""
    client_id: int = Field(..., description="Идентификатор клиента")
    salon_id: int = Field(..., description="Идентификатор салона")
    master_id: int = Field(..., description="Идентификатор мастера")
    service_id: int = Field(..., description="Идентификатор услуги")
    date: date = Field(..., description="Дата записи")
    time_start: time = Field(..., description="Время начала")
    time_end: time = Field(..., description="Время окончания")
    status: AppointmentStatusEnum = Field(default=AppointmentStatusEnum.BOOKED, description="Статус записи")


class AppointmentUpdate(BaseModel):
    """Схема для обновления записи на услугу"""
    client_id: Optional[int] = Field(None, description="Идентификатор клиента")
    salon_id: Optional[int] = Field(None, description="Идентификатор салона")
    master_id: Optional[int] = Field(None, description="Идентификатор мастера")
    service_id: Optional[int] = Field(None, description="Идентификатор услуги")
    date: Optional[date] = Field(None, description="Дата записи")
    time_start: Optional[time] = Field(None, description="Время начала")
    time_end: Optional[time] = Field(None, description="Время окончания")
    status: Optional[AppointmentStatusEnum] = Field(None, description="Статус записи")


class AppointmentRead(BaseModel):
    """Схема для вывода информации о записи на услугу"""
    id: int = Field(..., description="Уникальный идентификатор записи")
    client_id: int = Field(..., description="Идентификатор клиента")
    salon_id: int = Field(..., description="Идентификатор салона")
    master_id: int = Field(..., description="Идентификатор мастера")
    service_id: int = Field(..., description="Идентификатор услуги")
    date: date = Field(..., description="Дата записи")
    time_start: time = Field(..., description="Время начала")
    time_end: time = Field(..., description="Время окончания")
    status: AppointmentStatusEnum = Field(..., description="Статус записи")
    created_at: datetime = Field(..., description="Дата и время создания записи")

    class Config:
        from_attributes = True
