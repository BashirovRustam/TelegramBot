from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from telegram_bot_app.models.appointment import AppointmentStatusEnum
from datetime import date as DateType, time as TimeType


class AppointmentCreate(BaseModel):
    """Схема для создания записи на услугу"""
    model_config = {"arbitrary_types_allowed": True, "from_attributes": True}

    client_id: int = Field(..., description="Идентификатор клиента")
    salon_id: int = Field(..., description="Идентификатор салона")
    master_id: int = Field(..., description="Идентификатор мастера")
    service_id: int = Field(..., description="Идентификатор услуги")
    date: DateType = Field(..., description="Дата записи")
    time_start: TimeType = Field(..., description="Время начала")
    time_end: TimeType = Field(..., description="Время окончания")
    status: AppointmentStatusEnum = Field(default=AppointmentStatusEnum.BOOKED, description="Статус записи")
    notified: bool = Field(default=False, description="Флаг отправки уведомления")


class AppointmentUpdate(BaseModel):
    """Схема для обновления записи на услугу"""
    model_config = {"arbitrary_types_allowed": True, "from_attributes": True}

    client_id: Optional[int] = Field(None, description="Идентификатор клиента")
    salon_id: Optional[int] = Field(None, description="Идентификатор салона")
    master_id: Optional[int] = Field(None, description="Идентификатор мастера")
    service_id: Optional[int] = Field(None, description="Идентификатор услуги")
    date: Optional[DateType] = Field(None, description="Дата записи")
    time_start: Optional[TimeType] = Field(None, description="Время начала")
    time_end: Optional[TimeType] = Field(None, description="Время окончания")
    status: Optional[AppointmentStatusEnum] = Field(None, description="Статус записи")
    notified: Optional[bool] = Field(None, description="Флаг отправки уведомления")


class AppointmentRead(BaseModel):
    """Схема для вывода информации о записи на услугу"""
    model_config = {"arbitrary_types_allowed": True, "from_attributes": True}

    id: int = Field(..., description="Уникальный идентификатор записи")
    client_id: int = Field(..., description="Идентификатор клиента")
    salon_id: int = Field(..., description="Идентификатор салона")
    master_id: int = Field(..., description="Идентификатор мастера")
    service_id: int = Field(..., description="Идентификатор услуги")
    date: DateType = Field(..., description="Дата записи")
    time_start: TimeType = Field(..., description="Время начала")
    time_end: TimeType = Field(..., description="Время окончания")
    status: AppointmentStatusEnum = Field(..., description="Статус записи")
    created_at: datetime = Field(..., description="Дата и время создания записи")
    notified: bool = Field(..., description="Флаг отправки уведомления")