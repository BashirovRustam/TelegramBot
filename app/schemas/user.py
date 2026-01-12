from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

from app.db.enums import RolesEnum, TaskStatusEnum


# ==============================
# USER SCHEMAS
# ==============================

class UserBase(BaseModel):
    telegram_id: int
    full_name: str
    role: RolesEnum = RolesEnum.EXECUTOR
    is_active: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[RolesEnum] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
