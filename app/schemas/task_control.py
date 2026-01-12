from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TaskAttachmentBase(BaseModel):
    task_id: int
    telegram_file_id: str


class TaskAttachmentCreate(TaskAttachmentBase):
    pass


class TaskAttachmentUpdate(BaseModel):
    telegram_file_id: Optional[str] = None


class TaskAttachmentRead(TaskAttachmentBase):
    id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
