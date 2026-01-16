from datetime import time
from typing import Optional
from pydantic import BaseModel, Field


class MasterScheduleCreate(BaseModel):
    """Схема для создания расписания мастера"""
    master_id: int = Field(..., description="Идентификатор мастера")
    weekday: int = Field(..., ge=0, le=6, description="День недели (0-Понедельник, 6-Воскресенье)")
    time_from: time = Field(..., description="Время начала работы")
    time_to: time = Field(..., description="Время окончания работы")


class MasterScheduleUpdate(BaseModel):
    """Схема для обновления расписания мастера"""
    master_id: Optional[int] = Field(None, description="Идентификатор мастера")
    weekday: Optional[int] = Field(None, ge=0, le=6, description="День недели (0-Понедельник, 6-Воскресенье)")
    time_from: Optional[time] = Field(None, description="Время начала работы")
    time_to: Optional[time] = Field(None, description="Время окончания работы")


class MasterScheduleRead(BaseModel):
    """Схема для вывода информации о расписании мастера"""
    id: int = Field(..., description="Уникальный идентификатор расписания")
    master_id: int = Field(..., description="Идентификатор мастера")
    weekday: int = Field(..., description="День недели (0-Понедельник, 6-Воскресенье)")
    time_from: time = Field(..., description="Время начала работы")
    time_to: time = Field(..., description="Время окончания работы")

    class Config:
        from_attributes = True
