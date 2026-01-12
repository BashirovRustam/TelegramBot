from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

from app.db.enums import TaskStatusEnum
from app.schemas.user import UserRead



class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatusEnum = TaskStatusEnum.NEW
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    executor_id: Optional[int] = None


class TaskCreate(TaskBase):
    created_by: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    executor_id: Optional[int] = None
    completed_at: Optional[datetime] = None


class TaskRead(TaskBase):
    id: int
    created_by: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    # Relationships
    executor: Optional['UserRead'] = None
    creator: Optional['UserRead'] = None
    attachments: Optional[List['TaskAttachmentRead']] = []
    status_history: Optional[List['TaskStatusHistoryRead']] = []

    class Config:
        from_attributes = True


# ==============================
# TASK ATTACHMENT SCHEMAS
# ==============================

class TaskAttachmentBase(BaseModel):
    task_id: int
    telegram_file_id: str


class TaskAttachmentCreate(TaskAttachmentBase):
    pass


class TaskAttachmentRead(TaskAttachmentBase):
    id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ==============================
# TASK STATUS HISTORY SCHEMAS
# ==============================

class TaskStatusHistoryRead(BaseModel):
    id: int
    task_id: int
    old_status: Optional[TaskStatusEnum] = None
    new_status: TaskStatusEnum
    changed_by: int
    changed_at: datetime

    # Relationships
    task: Optional['TaskRead'] = None
    user: Optional['UserRead'] = None

    class Config:
        from_attributes = True


# ==============================
# FORWARD REFERENCES RESOLUTION
# ==============================

# Resolve forward references
UserRead.model_rebuild()
TaskRead.model_rebuild()
TaskAttachmentRead.model_rebuild()
TaskStatusHistoryRead.model_rebuild()
