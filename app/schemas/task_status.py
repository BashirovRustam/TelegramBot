from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.db.enums import TaskStatusEnum


class TaskStatusHistoryBase(BaseModel):
    task_id: int
    old_status: Optional[TaskStatusEnum] = None
    new_status: TaskStatusEnum
    changed_by: int


class TaskStatusHistoryCreate(TaskStatusHistoryBase):
    pass


class TaskStatusHistoryUpdate(BaseModel):
    old_status: Optional[TaskStatusEnum] = None
    new_status: Optional[TaskStatusEnum] = None
    changed_by: Optional[int] = None


class TaskStatusHistoryRead(TaskStatusHistoryBase):
    id: int
    changed_at: datetime

    class Config:
        from_attributes = True
